from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import init_db, SessionLocal, Draw, Prediction
from models.frequency import get_frequency_prediction
from models.markov import get_markov_prediction
from models.lstm import get_lstm_prediction
from predictor import store_daily_predictions, backfill_matches
from seed import seed_database
from backtest import backtest
from datetime import date, timedelta

class TicketCheck(BaseModel):
    n1: int
    n2: int
    n3: int
    n4: int
    n5: int


app = FastAPI(title="DailyLotto API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def health():
    return {"status": "ok", "app": "DailyLotto API"}


@app.get("/predict/frequency")
def predict_frequency():
    return get_frequency_prediction()


@app.get("/predict/markov")
def predict_markov():
    return get_markov_prediction()


@app.get("/predict/lstm")
def predict_lstm():
    return get_lstm_prediction()


@app.get("/draws/latest")
def latest_draw():
    session = SessionLocal()
    draw = session.query(Draw).order_by(Draw.draw_date.desc()).first()
    session.close()
    if not draw:
        return {"error": "No draws found"}
    return {
        "id": draw.id,
        "date": str(draw.draw_date),
        "numbers": [draw.n1, draw.n2, draw.n3, draw.n4, draw.n5],
    }


@app.get("/draws/recent")
def recent_draws(days: int = 7):
    session = SessionLocal()
    cutoff = date.today() - timedelta(days=days * 2)
    draws = (
        session.query(Draw)
        .filter(Draw.draw_date >= cutoff)
        .order_by(Draw.draw_date.desc())
        .limit(days)
        .all()
    )
    session.close()
    return [
        {
            "id": d.id,
            "date": str(d.draw_date),
            "numbers": [d.n1, d.n2, d.n3, d.n4, d.n5],
        }
        for d in draws
    ]


@app.post("/checker")
def check_ticket(ticket: TicketCheck):
    session = SessionLocal()
    user_set = {ticket.n1, ticket.n2, ticket.n3, ticket.n4, ticket.n5}
    draws = session.query(Draw).order_by(Draw.draw_date.desc()).limit(100).all()
    session.close()
    results = []
    for d in draws:
        actual_set = {d.n1, d.n2, d.n3, d.n4, d.n5}
        matches = len(user_set & actual_set)
        if matches > 0:
            results.append(
                {
                    "date": str(d.draw_date),
                    "draw_numbers": list(actual_set),
                    "matches": matches,
                }
            )
    return {"results": results, "total_checked": len(draws)}


@app.get("/tracker")
def get_tracker():
    session = SessionLocal()
    predictions = (
        session.query(Prediction)
        .order_by(Prediction.draw_date.desc())
        .limit(100)
        .all()
    )
    result = []
    for p in predictions:
        draw = session.query(Draw).filter_by(draw_date=p.draw_date).first()
        draw_numbers = [draw.n1, draw.n2, draw.n3, draw.n4, draw.n5] if draw else None
        pred_set = {p.n1, p.n2, p.n3, p.n4, p.n5}
        matching_numbers = list(pred_set & set(draw_numbers)) if draw_numbers else []
        result.append(
            {
                "id": p.id,
                "date": str(p.draw_date),
                "method": p.method,
                "prediction": [p.n1, p.n2, p.n3, p.n4, p.n5],
                "matches": p.matches,
                "draw_numbers": draw_numbers,
                "matching_numbers": matching_numbers,
            }
        )
    session.close()
    return result


@app.get("/tracker/win-rates")
def win_rates():
    session = SessionLocal()
    predictions = (
        session.query(Prediction).filter(Prediction.matches.isnot(None)).all()
    )
    session.close()
    methods = {}
    for p in predictions:
        if p.method not in methods:
            methods[p.method] = {
                "total": 0,
                "matches": 0,
                "wins_2plus": 0,
                "wins_3plus": 0,
                "streak": 0,
                "best_streak": 0,
            }
        m = methods[p.method]
        m["total"] += 1
        m["matches"] += p.matches
        if p.matches >= 2:
            m["wins_2plus"] += 1
            m["streak"] += 1
        else:
            m["streak"] = 0
        m["best_streak"] = max(m["best_streak"], m["streak"])
        if p.matches >= 3:
            m["wins_3plus"] += 1
    result = {}
    for method, stats in methods.items():
        result[method] = {
            "total_predictions": stats["total"],
            "total_matches": stats["matches"],
            "avg_matches": round(stats["matches"] / stats["total"], 2)
            if stats["total"]
            else 0,
            "win_rate_2plus": round(stats["wins_2plus"] / stats["total"], 3)
            if stats["total"]
            else 0,
            "win_rate_3plus": round(stats["wins_3plus"] / stats["total"], 3)
            if stats["total"]
            else 0,
            "best_streak": stats["best_streak"],
        }
    return result


@app.post("/seed")
def seed():
    seed_database()
    return {"status": "seeded"}


@app.post("/train")
def train():
    from models.lstm import train_lstm
    ok = train_lstm()
    if not ok:
        return {"error": "Not enough data to train"}
    return {"status": "model trained"}

@app.post("/retrain")
def retrain():
    store_daily_predictions()
    return {"status": "predictions stored"}


@app.post("/backfill")
def backfill():
    backfill_matches()
    return {"status": "matches updated"}


@app.post("/backtest")
def run_backtest(limit: int = 500):
    return backtest(limit=limit)
