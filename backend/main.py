from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from database import init_db, SessionLocal, Draw, Prediction
from models.frequency import get_frequency_prediction
from models.markov import get_markov_prediction
from models.lstm import get_lstm_prediction, train_lstm
from models.alternative import (get_pair_frequency_prediction, get_delta_prediction,
                                get_ensemble_prediction, get_weighted_frequency_prediction,
                                get_hot_cold_prediction)
from predictor import store_daily_predictions, backfill_matches
from seed import seed_database
from backtest import backtest
from games import GAMES, SAST, next_draw_date
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
import threading

_scheduler: BackgroundScheduler | None = None


def _pred_numbers(p):
    nums = [p.n1, p.n2, p.n3, p.n4, p.n5]
    if p.n6 is not None:
        nums.append(p.n6)
    return nums


class TicketCheck(BaseModel):
    n1: int
    n2: int
    n3: int
    n4: int
    n5: int
    n6: Optional[int] = None


app = FastAPI(title="DailyLotto API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _startup_worker():
    for game in ["daily_lotto"]:
        try:
            seed_database(game)
        except Exception as e:
            print(f"[{game}] Seed failed on startup: {e}")
        try:
            train_lstm(game)
        except Exception as e:
            print(f"[{game}] LSTM training failed on startup: {e}")
        try:
            session = SessionLocal()
            has_predictions = session.query(Prediction).filter_by(game=game).first()
            session.close()
            if not has_predictions:
                backtest(game, limit=500)
        except Exception as e:
            print(f"[{game}] Backtest failed on startup: {e}")


def daily_update(game: str):
    label = GAMES[game]["label"]
    print(f"[{date.today()}] {label} update started — seeding...")
    try:
        seed_database(game)
    except Exception as e:
        print(f"[{game}] Daily seed failed: {e}")
    try:
        backfill_matches()
    except Exception as e:
        print(f"[{game}] Daily backfill failed: {e}")
    try:
        store_daily_predictions(game)
    except Exception as e:
        print(f"[{game}] Daily predictions failed: {e}")
    try:
        train_lstm(game)
    except Exception as e:
        print(f"[{game}] Daily LSTM train failed: {e}")
    print(f"[{date.today()}] {label} update complete")


def _schedule_game_jobs(scheduler: BackgroundScheduler):
    for game_key, cfg in GAMES.items():
        t = cfg["predict_time"]
        days = cfg["predict_days"]
        day_of_week = ",".join(str(d) for d in days)
        scheduler.add_job(
            daily_update,
            "cron",
            args=[game_key],
            hour=t["hour"],
            minute=t["minute"],
            day_of_week=day_of_week,
            timezone=SAST,
            id=f"daily_update_{game_key}",
            replace_existing=True,
        )


@app.on_event("startup")
def startup():
    global _scheduler
    init_db()
    threading.Thread(target=_startup_worker, daemon=True).start()
    _scheduler = BackgroundScheduler()
    _schedule_game_jobs(_scheduler)
    _scheduler.start()


@app.on_event("shutdown")
def shutdown():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)


@app.get("/")
def health():
    return {"status": "ok", "app": "DailyLotto API"}


@app.get("/games")
def list_games():
    return [
        {
            "id": key,
            "label": cfg["label"],
            "pick_count": cfg["pick_count"],
            "max_number": cfg["max_number"],
            "has_bonus": cfg["has_bonus"],
            "has_powerball": cfg["has_powerball"],
            "powerball_max": cfg.get("powerball_max"),
            "draw_days": cfg["draw_days"],
        }
        for key, cfg in GAMES.items()
    ]


@app.get("/predict/frequency")
def predict_frequency(game: str = "daily_lotto"):
    return get_frequency_prediction(game)


@app.get("/predict/markov")
def predict_markov(game: str = "daily_lotto"):
    return get_markov_prediction(game)


@app.get("/predict/lstm")
def predict_lstm(game: str = "daily_lotto"):
    return get_lstm_prediction(game)


@app.get("/predict/pair-freq")
def predict_pair_freq(game: str = "daily_lotto"):
    return get_pair_frequency_prediction(game)


@app.get("/predict/delta")
def predict_delta(game: str = "daily_lotto"):
    return get_delta_prediction(game)


@app.get("/predict/ensemble")
def predict_ensemble(game: str = "daily_lotto"):
    return get_ensemble_prediction(game)


@app.get("/predict/weighted-freq")
def predict_weighted_freq(game: str = "daily_lotto"):
    return get_weighted_frequency_prediction(game)


@app.get("/predict/hot-cold")
def predict_hot_cold(game: str = "daily_lotto"):
    return get_hot_cold_prediction(game)


@app.get("/draws/latest")
def latest_draw(game: str = "daily_lotto"):
    session = SessionLocal()
    try:
        draw = (
            session.query(Draw)
            .filter_by(game=game)
            .order_by(Draw.draw_date.desc())
            .first()
        )
        if not draw:
            return {"error": f"No draws found for {game}"}
        numbers = [draw.n1, draw.n2, draw.n3, draw.n4, draw.n5]
        if draw.n6 is not None:
            numbers.append(draw.n6)
        return {
            "id": draw.id,
            "game": draw.game,
            "date": str(draw.draw_date),
            "numbers": numbers,
            "bonus": draw.bonus,
            "powerball": draw.powerball,
            "machine": draw.machine,
        }
    finally:
        session.close()


@app.get("/draws/recent")
def recent_draws(game: str = "daily_lotto", days: int = 7):
    session = SessionLocal()
    try:
        cutoff = date.today() - timedelta(days=days * 2)
        draws = (
            session.query(Draw)
            .filter(Draw.game == game, Draw.draw_date >= cutoff)
            .order_by(Draw.draw_date.desc())
            .limit(days)
            .all()
        )
        result = []
        for d in draws:
            numbers = [d.n1, d.n2, d.n3, d.n4, d.n5]
            if d.n6 is not None:
                numbers.append(d.n6)
            result.append({
                "id": d.id,
                "game": d.game,
                "date": str(d.draw_date),
                "numbers": numbers,
                "bonus": d.bonus,
                "powerball": d.powerball,
            })
        return result
    finally:
        session.close()


@app.post("/checker")
def check_ticket(ticket: TicketCheck, game: str = "daily_lotto"):
    session = SessionLocal()
    try:
        user_set = {ticket.n1, ticket.n2, ticket.n3, ticket.n4, ticket.n5}
        if ticket.n6 is not None:
            user_set.add(ticket.n6)
        draws = (
            session.query(Draw)
            .filter_by(game=game)
            .order_by(Draw.draw_date.desc())
            .limit(100)
            .all()
        )
        results = []
        for d in draws:
            actual_set = {d.n1, d.n2, d.n3, d.n4, d.n5}
            if d.n6 is not None:
                actual_set.add(d.n6)
            if d.bonus is not None:
                actual_set.add(d.bonus)
            if d.powerball is not None:
                actual_set.add(d.powerball)
            matches = len(user_set & actual_set)
            if matches > 0:
                draw_numbers = [d.n1, d.n2, d.n3, d.n4, d.n5]
                if d.n6 is not None:
                    draw_numbers.append(d.n6)
                results.append({
                    "date": str(d.draw_date),
                    "draw_numbers": draw_numbers,
                    "bonus": d.bonus,
                    "powerball": d.powerball,
                    "matches": matches,
                })
        return {"results": results, "total_checked": len(draws)}
    finally:
        session.close()


@app.get("/tracker")
def get_tracker(game: str = "daily_lotto"):
    session = SessionLocal()
    try:
        predictions = (
            session.query(Prediction)
            .filter_by(game=game)
            .order_by(Prediction.draw_date.desc())
            .limit(400)
            .all()
        )
        result = []
        for p in predictions:
            draw = (
                session.query(Draw)
                .filter_by(game=game, draw_date=p.draw_date)
                .first()
            )
            pred_numbers = [p.n1, p.n2, p.n3, p.n4, p.n5]
            if p.n6 is not None:
                pred_numbers.append(p.n6)
            if draw:
                draw_numbers = [draw.n1, draw.n2, draw.n3, draw.n4, draw.n5]
                if draw.n6 is not None:
                    draw_numbers.append(draw.n6)
                pred_set = set(pred_numbers)
                matching_numbers = list(pred_set & set(draw_numbers))
            else:
                draw_numbers = None
                matching_numbers = []
            result.append({
                "id": p.id,
                "game": p.game,
                "date": str(p.draw_date),
                "method": p.method,
                "prediction": pred_numbers,
                "matches": p.matches,
                "draw_numbers": draw_numbers,
                "matching_numbers": matching_numbers,
            })
        return result
    finally:
        session.close()


@app.get("/tracker/win-rates")
def win_rates(game: str = "daily_lotto"):
    session = SessionLocal()
    try:
        predictions = (
            session.query(Prediction)
            .filter(Prediction.game == game, Prediction.matches.isnot(None))
            .all()
        )
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
    finally:
        session.close()


@app.get("/predict/today")
def predict_today(game: str = "daily_lotto"):
    cfg = GAMES[game]
    target = next_draw_date(game)
    session = SessionLocal()
    try:
        rows = session.query(Prediction).filter_by(game=game, draw_date=target).all()
        if rows:
            picks = {p.method: _pred_numbers(p) for p in rows}
            return {"game": game, "date": str(target), "picks": picks}
    finally:
        session.close()
    store_daily_predictions(game, target)
    session = SessionLocal()
    try:
        rows = session.query(Prediction).filter_by(game=game, draw_date=target).all()
        picks = {p.method: _pred_numbers(p) for p in rows}
        return {"game": game, "date": str(target), "picks": picks}
    finally:
        session.close()


@app.get("/results/latest")
def results_latest(game: str = "daily_lotto"):
    session = SessionLocal()
    try:
        pred = (
            session.query(Prediction)
            .filter(Prediction.game == game, Prediction.matches.isnot(None))
            .order_by(Prediction.draw_date.desc())
            .first()
        )
        if not pred:
            return {"error": f"No completed results yet for {game}"}
        latest_date = pred.draw_date
        preds = session.query(Prediction).filter_by(game=game, draw_date=latest_date).all()
        draw = session.query(Draw).filter_by(game=game, draw_date=latest_date).first()
        if not draw:
            return {"error": f"No draw found for {latest_date}"}
        draw_numbers = [draw.n1, draw.n2, draw.n3, draw.n4, draw.n5]
        if draw.n6 is not None:
            draw_numbers.append(draw.n6)
        methods = {}
        for p in preds:
            picks = [p.n1, p.n2, p.n3, p.n4, p.n5]
            if p.n6 is not None:
                picks.append(p.n6)
            methods[p.method] = {
                "picks": picks,
                "matches": p.matches,
            }
        return {
            "game": game,
            "date": str(latest_date),
            "draw_numbers": draw_numbers,
            "bonus": draw.bonus,
            "powerball": draw.powerball,
            "methods": methods,
        }
    finally:
        session.close()


@app.get("/tracker/recent-matches")
def recent_matches(game: str = "daily_lotto"):
    session = SessionLocal()
    try:
        methods_list = ["frequency", "weighted_freq", "pair_freq", "delta", "ensemble", "markov", "hot_cold", "lstm"]
        result = {}
        for method in methods_list:
            rows = (
                session.query(Prediction.matches)
                .filter(Prediction.game == game, Prediction.method == method, Prediction.matches.isnot(None))
                .order_by(Prediction.draw_date.desc())
                .limit(3)
                .all()
            )
            result[method] = [r[0] for r in rows]
        return result
    finally:
        session.close()


@app.post("/seed")
def seed(game: str = "daily_lotto"):
    seed_database(game)
    return {"game": game, "status": "seeded"}


@app.post("/train")
def train(game: str = "daily_lotto"):
    ok = train_lstm(game)
    if not ok:
        return {"game": game, "error": "Not enough data to train"}
    return {"game": game, "status": "model trained"}


@app.post("/retrain")
def retrain(game: str = "daily_lotto"):
    seed_database(game)
    store_daily_predictions(game)
    return {"game": game, "status": "predictions stored"}


@app.post("/backfill")
def backfill():
    backfill_matches()
    return {"status": "matches updated"}


@app.post("/backtest")
def run_backtest(game: str = "daily_lotto", limit: int = 500):
    return backtest(game, limit=limit)
