from database import SessionLocal, Prediction, Draw
from datetime import date
from collections import Counter
from models.frequency import get_frequency_prediction
from models.markov import get_markov_prediction
from models.lstm import get_lstm_prediction
from models.alternative import (get_pair_frequency_prediction, get_delta_prediction,
                                get_ensemble_prediction, get_weighted_frequency_prediction,
                                get_hot_cold_prediction)
from games import GAMES, next_draw_date


def _predict_bonus(game):
    cfg = GAMES[game]
    session = SessionLocal()
    all_draws = session.query(Draw).filter(Draw.game == game).all()
    session.close()
    if not all_draws:
        return None
    counter = Counter()
    if cfg["has_bonus"]:
        for d in all_draws:
            if d.bonus is not None:
                counter[d.bonus] += 1
    if cfg["has_powerball"]:
        for d in all_draws:
            if d.powerball is not None:
                counter[d.powerball] += 1
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def store_daily_predictions(game, target_date=None):
    cfg = GAMES[game]
    if target_date is None:
        target_date = next_draw_date(game)
    PICK = cfg["pick_count"]
    session = SessionLocal()
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
    bonus_pb = _predict_bonus(game)
    for method_name, func in methods.items():
        result = func(game)
        if "error" in result:
            print(f"Error in {method_name} ({game}): {result['error']}")
            continue
        picks = result["picks"]
        existing = (
            session.query(Prediction)
            .filter_by(game=game, draw_date=target_date, method=method_name)
            .first()
        )
        pred_data = {
            "game": game,
            "draw_date": target_date,
            "method": method_name,
        }
        for j, n in enumerate(picks):
            pred_data[f"n{j + 1}"] = n
        if cfg["has_bonus"]:
            pred_data["bonus"] = bonus_pb
        if cfg["has_powerball"]:
            pred_data["powerball"] = bonus_pb
        if existing:
            for k, v in pred_data.items():
                setattr(existing, k, v)
        else:
            session.add(Prediction(**pred_data))
    session.commit()
    session.close()


def backfill_matches():
    session = SessionLocal()
    predictions = (
        session.query(Prediction).filter(Prediction.matches.is_(None)).all()
    )
    for p in predictions:
        draw = session.query(Draw).filter_by(draw_date=p.draw_date, game=p.game).first()
        if draw:
            pred_set = {p.n1, p.n2, p.n3, p.n4, p.n5}
            actual_set = {draw.n1, draw.n2, draw.n3, draw.n4, draw.n5}
            if p.n6 is not None:
                pred_set.add(p.n6)
            if draw.n6 is not None:
                actual_set.add(draw.n6)
            p.matches = len(pred_set & actual_set)
    session.commit()
    session.close()
