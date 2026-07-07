import numpy as np
from database import SessionLocal, Draw


def build_transition_matrix(draws):
    matrix = np.zeros((36, 36), dtype=float)
    for i in range(len(draws) - 1):
        curr_nums = {
            draws[i].n1,
            draws[i].n2,
            draws[i].n3,
            draws[i].n4,
            draws[i].n5,
        }
        next_nums = {
            draws[i + 1].n1,
            draws[i + 1].n2,
            draws[i + 1].n3,
            draws[i + 1].n4,
            draws[i + 1].n5,
        }
        for c in curr_nums:
            for n in next_nums:
                matrix[c - 1][n - 1] += 1
    row_sums = matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    matrix = matrix / row_sums
    return matrix


def get_markov_prediction():
    session = SessionLocal()
    all_draws = session.query(Draw).order_by(Draw.draw_date).all()
    session.close()

    if len(all_draws) < 2:
        return {"error": "Not enough draw data"}

    matrix = build_transition_matrix(all_draws)
    last_draw = all_draws[-1]
    last_nums = [last_draw.n1, last_draw.n2, last_draw.n3, last_draw.n4, last_draw.n5]

    candidates = {}
    for n in last_nums:
        probs = matrix[n - 1]
        for i in range(36):
            if probs[i] > 0:
                candidates[i + 1] = candidates.get(i + 1, 0) + probs[i]

    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    picked = []
    for num, _ in sorted_candidates:
        if num not in picked:
            picked.append(num)
        if len(picked) == 5:
            break

    if len(picked) < 5:
        for i in range(1, 37):
            if i not in picked:
                picked.append(i)
            if len(picked) == 5:
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
