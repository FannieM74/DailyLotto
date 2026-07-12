from database import SessionLocal, Draw
from datetime import date
from collections import Counter
from games import GAMES


def _get_nums(d, pick_count):
    nums = [d.n1, d.n2, d.n3, d.n4, d.n5]
    if pick_count > 5 and d.n6 is not None:
        nums.append(d.n6)
    return nums


def get_frequency_prediction(game):
    cfg = GAMES[game]
    N = cfg["max_number"]
    PICK = cfg["pick_count"]

    session = SessionLocal()
    all_draws = session.query(Draw).filter(Draw.game == game).all()
    session.close()

    if not all_draws:
        return {"error": "No draw data available"}

    today = date.today()
    counter = Counter()
    for d in all_draws:
        for n in _get_nums(d, PICK):
            counter[n] += 1

    counts = [counter.get(i, 0) for i in range(1, N + 1)]
    sorted_nums = sorted(range(1, N + 1), key=lambda x: counter.get(x, 0), reverse=True)
    hot = sorted_nums[:PICK]

    last_seen = {}
    for d in reversed(all_draws):
        for n in _get_nums(d, PICK):
            if n not in last_seen:
                last_seen[n] = d.draw_date
    overdue = sorted(
        range(1, N + 1),
        key=lambda x: (
            today - last_seen.get(x, date(2019, 1, 1))
        ).days,
        reverse=True,
    )[:PICK]

    cold = sorted_nums[-PICK:]

    return {
        "counts": counts,
        "hot": hot,
        "cold": cold,
        "overdue": overdue,
        "picks": hot,
        "total_draws": len(all_draws),
    }
