import numpy as np
from database import SessionLocal, Draw
from games import GAMES


def _get_nums(d, pick_count):
    nums = [d.n1, d.n2, d.n3, d.n4, d.n5]
    if pick_count > 5 and d.n6 is not None:
        nums.append(d.n6)
    return nums


def build_transition_matrix(draws, n_size, pick_count):
    matrix = np.zeros((n_size, n_size), dtype=float)
    for i in range(len(draws) - 1):
        curr_nums = set(_get_nums(draws[i], pick_count))
        next_nums = set(_get_nums(draws[i + 1], pick_count))
        for c in curr_nums:
            for n in next_nums:
                matrix[c - 1][n - 1] += 1
    row_sums = matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    matrix = matrix / row_sums
    return matrix


def get_markov_prediction(game):
    cfg = GAMES[game]
    N = cfg["max_number"]
    PICK = cfg["pick_count"]

    session = SessionLocal()
    all_draws = session.query(Draw).filter(Draw.game == game).order_by(Draw.draw_date).all()
    session.close()

    if len(all_draws) < 2:
        return {"error": "Not enough draw data"}

    matrix = build_transition_matrix(all_draws, N, PICK)
    last_draw = all_draws[-1]
    last_nums = _get_nums(last_draw, PICK)

    candidates = {}
    for n in last_nums:
        probs = matrix[n - 1]
        for i in range(N):
            if probs[i] > 0:
                candidates[i + 1] = candidates.get(i + 1, 0) + probs[i]

    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    picked = []
    for num, _ in sorted_candidates:
        if num not in picked:
            picked.append(num)
        if len(picked) == PICK:
            break

    if len(picked) < PICK:
        for i in range(1, N + 1):
            if i not in picked:
                picked.append(i)
            if len(picked) == PICK:
                break

    confidence = sum(candidates.get(n, 0) for n in picked) / max(
        sum(candidates.values()), 0.01
    )

    return {
        "last_draw": {"date": str(last_draw.draw_date), "numbers": last_nums},
        "picks": picked,
        "confidence": round(float(confidence), 4),
        "transition_matrix": matrix.tolist(),
    }
