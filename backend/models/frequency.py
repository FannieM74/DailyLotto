from database import SessionLocal, Draw
from datetime import date
from collections import Counter


def get_frequency_prediction():
    session = SessionLocal()
    all_draws = session.query(Draw).all()
    session.close()

    if not all_draws:
        return {"error": "No draw data available"}

    today = date.today()
    counter = Counter()
    for d in all_draws:
        counter[d.n1] += 1
        counter[d.n2] += 1
        counter[d.n3] += 1
        counter[d.n4] += 1
        counter[d.n5] += 1

    counts = [counter.get(i, 0) for i in range(1, 37)]
    sorted_nums = sorted(range(1, 37), key=lambda x: counter.get(x, 0), reverse=True)
    hot = sorted_nums[:5]

    last_seen = {}
    for d in reversed(all_draws):
        for n in [d.n1, d.n2, d.n3, d.n4, d.n5]:
            if n not in last_seen:
                last_seen[n] = d.draw_date
    overdue = sorted(
        range(1, 37),
        key=lambda x: (
            today - last_seen.get(x, date(2019, 1, 1))
        ).days,
        reverse=True,
    )[:5]

    cold = sorted_nums[-5:]

    return {
        "counts": counts,
        "hot": hot,
        "cold": cold,
        "overdue": overdue,
        "picks": hot,
        "total_draws": len(all_draws),
    }
