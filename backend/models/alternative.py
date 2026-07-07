from database import SessionLocal, Draw
from collections import Counter

N = 36
PICK = 5


def get_pair_frequency_prediction():
    session = SessionLocal()
    all_draws = session.query(Draw).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}
    pairs = Counter()
    for d in all_draws:
        ns = sorted([d.n1, d.n2, d.n3, d.n4, d.n5])
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                pairs[(ns[i], ns[j])] += 1
    top = [p for p, _ in pairs.most_common(50)]
    picked = []
    for a, b in top:
        if a not in picked: picked.append(a)
        if len(picked) == PICK: break
        if b not in picked: picked.append(b)
        if len(picked) == PICK: break
    return {"picks": sorted(picked), "total_pairs": len(pairs)}


def get_delta_prediction():
    session = SessionLocal()
    all_draws = session.query(Draw).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}
    deltas = Counter()
    for d in all_draws:
        ns = sorted([d.n1, d.n2, d.n3, d.n4, d.n5])
        for i in range(len(ns) - 1):
            deltas[ns[i + 1] - ns[i]] += 1
    common = [d for d, _ in deltas.most_common(10)]
    last = sorted([all_draws[-1].n1, all_draws[-1].n2, all_draws[-1].n3, all_draws[-1].n4, all_draws[-1].n5])
    picked = set()
    for start in last:
        picked.add(start)
        for delta in common:
            n = start + delta
            if 1 <= n <= N and n not in picked:
                picked.add(n)
            if len(picked) >= PICK:
                break
        if len(picked) >= PICK:
            break
    fill = 1
    while len(picked) < PICK:
        if fill not in picked:
            picked.add(fill)
        fill += 1
    return {"picks": sorted(list(picked))[:PICK]}


def get_ensemble_prediction():
    session = SessionLocal()
    all_draws = session.query(Draw).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}

    c = Counter()
    for d in all_draws:
        for n in [d.n1, d.n2, d.n3, d.n4, d.n5]:
            c[n] += 1
    freq_picks = set(sorted(range(1, N + 1), key=lambda x: c.get(x, 0), reverse=True)[:PICK])

    weights = [0.0] * N
    for i, d in enumerate(all_draws):
        w = 0.99 ** (len(all_draws) - 1 - i)
        for n in [d.n1, d.n2, d.n3, d.n4, d.n5]:
            weights[n - 1] += w
    wfreq_picks = set(sorted(range(1, N + 1), key=lambda x: weights[x - 1], reverse=True)[:PICK])

    votes = Counter()
    for n in freq_picks: votes[n] += 1
    for n in wfreq_picks: votes[n] += 1
    return {"picks": sorted([n for n, _ in votes.most_common(PICK)])}


def get_weighted_frequency_prediction():
    session = SessionLocal()
    all_draws = session.query(Draw).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}
    weights = [0.0] * N
    for i, d in enumerate(all_draws):
        w = 0.99 ** (len(all_draws) - 1 - i)
        for n in [d.n1, d.n2, d.n3, d.n4, d.n5]:
            weights[n - 1] += w
    picks = sorted(range(1, N + 1), key=lambda x: weights[x - 1], reverse=True)[:PICK]
    return {"picks": picks}


def get_hot_cold_prediction():
    session = SessionLocal()
    all_draws = session.query(Draw).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}
    c = Counter()
    for d in all_draws:
        for n in [d.n1, d.n2, d.n3, d.n4, d.n5]:
            c[n] += 1
    ranked = sorted(range(1, N + 1), key=lambda x: c.get(x, 0), reverse=True)
    hot = ranked[:3]
    cold = ranked[-2:]
    return {"picks": sorted(hot + cold)}
