from database import SessionLocal, Draw, Prediction
from collections import Counter


def build_transition_matrix(draws):
    matrix = np.zeros((36, 36), dtype=float)
    for i in range(len(draws) - 1):
        curr_nums = {draws[i].n1, draws[i].n2, draws[i].n3, draws[i].n4, draws[i].n5}
        next_nums = {draws[i + 1].n1, draws[i + 1].n2, draws[i + 1].n3, draws[i + 1].n4, draws[i + 1].n5}
        for c in curr_nums:
            for n in next_nums:
                matrix[c - 1][n - 1] += 1
    row_sums = matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    matrix = matrix / row_sums
    return matrix


def markov_predict(prior_draws):
    if len(prior_draws) < 2:
        return None
    matrix = build_transition_matrix(prior_draws)
    last = prior_draws[-1]
    last_nums = [last.n1, last.n2, last.n3, last.n4, last.n5]
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
    while len(picked) < 5:
        for i in range(1, 37):
            if i not in picked:
                picked.append(i)
                if len(picked) == 5:
                    break
    return picked


def backtest(limit=500):
    session = SessionLocal()
    all_draws = session.query(Draw).order_by(Draw.draw_date).all()

    if len(all_draws) < 100:
        session.close()
        return {"error": "Need at least 100 draws for backtesting"}

    target_draws = all_draws[-limit:]
    start_idx = len(all_draws) - limit

    counter = Counter()
    for d in all_draws[:start_idx]:
        counter[d.n1] += 1
        counter[d.n2] += 1
        counter[d.n3] += 1
        counter[d.n4] += 1
        counter[d.n5] += 1

    inserted = {"frequency": 0, "markov": 0}

    for i, draw in enumerate(target_draws):
        actual_set = {draw.n1, draw.n2, draw.n3, draw.n4, draw.n5}
        idx = start_idx + i

        if counter:
            sorted_nums = sorted(range(1, 37), key=lambda x: counter.get(x, 0), reverse=True)
            freq_picks = sorted_nums[:5]
            freq_matches = len(set(freq_picks) & actual_set)
            existing = session.query(Prediction).filter_by(draw_date=draw.draw_date, method="frequency").first()
            if existing:
                existing.n1, existing.n2, existing.n3, existing.n4, existing.n5 = freq_picks
                existing.matches = freq_matches
            else:
                session.add(Prediction(
                    draw_date=draw.draw_date, method="frequency",
                    n1=freq_picks[0], n2=freq_picks[1], n3=freq_picks[2], n4=freq_picks[3], n5=freq_picks[4],
                    matches=freq_matches,
                ))
            inserted["frequency"] += 1

        if idx >= 1:
            prior = all_draws[:idx]
            markov_picks = markov_predict(prior)
            if markov_picks:
                markov_matches = len(set(markov_picks) & actual_set)
                existing = session.query(Prediction).filter_by(draw_date=draw.draw_date, method="markov").first()
                if existing:
                    existing.n1, existing.n2, existing.n3, existing.n4, existing.n5 = markov_picks
                    existing.matches = markov_matches
                else:
                    session.add(Prediction(
                        draw_date=draw.draw_date, method="markov",
                        n1=markov_picks[0], n2=markov_picks[1], n3=markov_picks[2], n4=markov_picks[3], n5=markov_picks[4],
                        matches=markov_matches,
                    ))
                inserted["markov"] += 1

        counter[draw.n1] += 1
        counter[draw.n2] += 1
        counter[draw.n3] += 1
        counter[draw.n4] += 1
        counter[draw.n5] += 1

        if (i + 1) % 100 == 0:
            session.commit()
            print(f"Backtest progress: {i + 1}/{limit}")

    session.commit()
    total = session.query(Prediction).count()
    session.close()

    print(f"Backtest complete. Inserted/updated: {inserted}. Total predictions in DB: {total}")
    return {"status": "ok", "inserted": inserted}
