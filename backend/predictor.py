from database import SessionLocal, Prediction, Draw
from datetime import date
from models.frequency import get_frequency_prediction
from models.markov import get_markov_prediction
from models.lstm import get_lstm_prediction
from models.alternative import (get_pair_frequency_prediction, get_delta_prediction,
                                get_ensemble_prediction, get_weighted_frequency_prediction,
                                get_hot_cold_prediction)


def store_daily_predictions():
    session = SessionLocal()
    today = date.today()
    methods = {
        "frequency": get_frequency_prediction,
        "markov": get_markov_prediction,
        "lstm": get_lstm_prediction,
        "pair_freq": get_pair_frequency_prediction,
        "delta": get_delta_prediction,
        "ensemble": get_ensemble_prediction,
        "weighted_freq": get_weighted_frequency_prediction,
        "hot_cold": get_hot_cold_prediction,
    }
    for method_name, func in methods.items():
        result = func()
        if "error" in result:
            print(f"Error in {method_name}: {result['error']}")
            continue
        picks = result["picks"]
        existing = (
            session.query(Prediction)
            .filter_by(draw_date=today, method=method_name)
            .first()
        )
        if existing:
            existing.n1, existing.n2, existing.n3, existing.n4, existing.n5 = picks
        else:
            session.add(
                Prediction(
                    draw_date=today,
                    method=method_name,
                    n1=picks[0],
                    n2=picks[1],
                    n3=picks[2],
                    n4=picks[3],
                    n5=picks[4],
                )
            )
    session.commit()
    session.close()


def backfill_matches():
    session = SessionLocal()
    predictions = (
        session.query(Prediction).filter(Prediction.matches.is_(None)).all()
    )
    for p in predictions:
        draw = session.query(Draw).filter_by(draw_date=p.draw_date).first()
        if draw:
            pred_set = {p.n1, p.n2, p.n3, p.n4, p.n5}
            actual_set = {draw.n1, draw.n2, draw.n3, draw.n4, draw.n5}
            p.matches = len(pred_set & actual_set)
    session.commit()
    session.close()
