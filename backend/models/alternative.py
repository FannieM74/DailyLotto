from database import SessionLocal, Draw
from collections import Counter
from games import GAMES


def _get_nums(d, pick_count):
    nums = [d.n1, d.n2, d.n3, d.n4, d.n5]
    if pick_count > 5 and d.n6 is not None:
        nums.append(d.n6)
    return nums


def get_pair_frequency_prediction(game):
    cfg = GAMES[game]
    N = cfg["max_number"]
    PICK = cfg["pick_count"]

    session = SessionLocal()
    all_draws = session.query(Draw).filter(Draw.game == game).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}
    pairs = Counter()
    for d in all_draws:
        ns = sorted(_get_nums(d, PICK))
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


def get_delta_prediction(game):
    cfg = GAMES[game]
    N = cfg["max_number"]
    PICK = cfg["pick_count"]

    session = SessionLocal()
    all_draws = session.query(Draw).filter(Draw.game == game).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}
    deltas = Counter()
    for d in all_draws:
        ns = sorted(_get_nums(d, PICK))
        for i in range(len(ns) - 1):
            deltas[ns[i + 1] - ns[i]] += 1
    common = [d for d, _ in deltas.most_common(10)]
    last = sorted(_get_nums(all_draws[-1], PICK))
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


def get_ensemble_prediction(game):
    cfg = GAMES[game]
    N = cfg["max_number"]
    PICK = cfg["pick_count"]

    session = SessionLocal()
    all_draws = session.query(Draw).filter(Draw.game == game).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}

    c = Counter()
    for d in all_draws:
        for n in _get_nums(d, PICK):
            c[n] += 1

    weights = [0.0] * N
    for i, d in enumerate(all_draws):
        w = 0.99 ** (len(all_draws) - 1 - i)
        for n in _get_nums(d, PICK):
            weights[n - 1] += w

    sorted_by_freq = sorted(range(1, N + 1), key=lambda x: c.get(x, 0), reverse=True)
    sorted_by_w = sorted(range(1, N + 1), key=lambda x: weights[x - 1], reverse=True)
    sorted_by_pair = sorted(range(1, N + 1), key=lambda x: _pair_score(x, all_draws, PICK), reverse=True)
    ranked_by_delta = _delta_ranking(all_draws, N, PICK)

    votes = Counter()
    for picks in [sorted_by_freq[:PICK], sorted_by_w[:PICK], sorted_by_pair[:PICK], ranked_by_delta[:PICK]]:
        for n in picks:
            votes[n] += 1

    votes_ranked = votes.most_common()
    max_vote = votes_ranked[0][1] if votes_ranked else 0
    result = sorted([n for n, v in votes_ranked if v == max_vote])
    remaining = PICK - len(result)
    if remaining > 0:
        for n, _ in votes_ranked:
            if n not in result:
                result.append(n)
                remaining -= 1
                if remaining == 0:
                    break
    return {"picks": sorted(result[:PICK])}


def _pair_score(n, all_draws, pick_count):
    pairs = Counter()
    for d in all_draws:
        ns = sorted(_get_nums(d, pick_count))
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                pairs[(ns[i], ns[j])] += 1
    score = 0
    for (a, b), cnt in pairs.most_common(30):
        if a == n or b == n:
            score += cnt
    return score


def _delta_ranking(all_draws, n_size, pick_count):
    deltas = Counter()
    for d in all_draws:
        ns = sorted(_get_nums(d, pick_count))
        for i in range(len(ns) - 1):
            deltas[ns[i + 1] - ns[i]] += 1
    common_deltas = {d for d, _ in deltas.most_common(8)}
    scores = Counter()
    for i in range(len(all_draws) - 1):
        curr = _get_nums(all_draws[i], pick_count)
        for n in _get_nums(all_draws[i + 1], pick_count):
            if abs(n - curr[0]) in common_deltas:
                scores[n] += 1
    return [n for n, _ in scores.most_common(n_size)]


def get_weighted_frequency_prediction(game):
    cfg = GAMES[game]
    N = cfg["max_number"]
    PICK = cfg["pick_count"]

    session = SessionLocal()
    all_draws = session.query(Draw).filter(Draw.game == game).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}
    weights = [0.0] * N
    for i, d in enumerate(all_draws):
        w = 0.99 ** (len(all_draws) - 1 - i)
        for n in _get_nums(d, PICK):
            weights[n - 1] += w
    picks = sorted(range(1, N + 1), key=lambda x: weights[x - 1], reverse=True)[:PICK]
    return {"picks": picks}


def get_hot_cold_prediction(game):
    cfg = GAMES[game]
    N = cfg["max_number"]
    PICK = cfg["pick_count"]

    session = SessionLocal()
    all_draws = session.query(Draw).filter(Draw.game == game).order_by(Draw.draw_date).all()
    session.close()
    if not all_draws:
        return {"error": "No draw data available"}
    c = Counter()
    for d in all_draws:
        for n in _get_nums(d, PICK):
            c[n] += 1
    ranked = sorted(range(1, N + 1), key=lambda x: c.get(x, 0), reverse=True)
    hot = ranked[:3]
    cold = ranked[-(PICK - 3):]
    return {"picks": sorted(hot + cold)}
