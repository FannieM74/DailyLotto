from database import SessionLocal, Draw, Prediction
from collections import Counter
import numpy as np
from models.lstm import load_model, predict_with_model, SEQ_LEN
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


def markov_predict(prior_draws, n_size, pick_count):
    if len(prior_draws) < 2:
        return None
    matrix = build_transition_matrix(prior_draws, n_size, pick_count)
    last = prior_draws[-1]
    last_nums = _get_nums(last, pick_count)
    candidates = {}
    for n in last_nums:
        probs = matrix[n - 1]
        for i in range(n_size):
            if probs[i] > 0:
                candidates[i + 1] = candidates.get(i + 1, 0) + probs[i]
    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    picked = []
    for num, _ in sorted_candidates:
        if num not in picked:
            picked.append(num)
        if len(picked) == pick_count:
            break
    while len(picked) < pick_count:
        for i in range(1, n_size + 1):
            if i not in picked:
                picked.append(i)
                if len(picked) == pick_count:
                    break
    return picked


def pair_freq_predict(draws, pick_count):
    pairs = Counter()
    for d in draws:
        ns = sorted(_get_nums(d, pick_count))
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                pairs[(ns[i], ns[j])] += 1
    top = [p for p, _ in pairs.most_common(50)]
    picked = []
    for a, b in top:
        if a not in picked: picked.append(a)
        if len(picked) == pick_count: break
        if b not in picked: picked.append(b)
        if len(picked) == pick_count: break
    return sorted(picked)


def delta_predict(draws, n_size, pick_count):
    if not draws:
        return list(range(1, pick_count + 1))
    deltas = Counter()
    for d in draws:
        ns = sorted(_get_nums(d, pick_count))
        for i in range(len(ns) - 1):
            deltas[ns[i + 1] - ns[i]] += 1
    common = [d for d, _ in deltas.most_common(10)]
    last = sorted(_get_nums(draws[-1], pick_count))
    picked = set()
    for start in last:
        picked.add(start)
        for delta in common:
            n = start + delta
            if 1 <= n <= n_size and n not in picked:
                picked.add(n)
            if len(picked) >= pick_count:
                break
        if len(picked) >= pick_count:
            break
    fill = 1
    while len(picked) < pick_count:
        if fill not in picked:
            picked.add(fill)
        fill += 1
    return sorted(list(picked))[:pick_count]


def ensemble_predict(draws, freq_set, n_size, pick_count):
    weights = [0.0] * n_size
    for i, d in enumerate(draws):
        w = 0.99 ** (len(draws) - 1 - i)
        for n in _get_nums(d, pick_count):
            weights[n - 1] += w
    wfreq = set(sorted(range(1, n_size + 1), key=lambda x: weights[x - 1], reverse=True)[:pick_count])
    votes = Counter()
    for n in freq_set: votes[n] += 1
    for n in wfreq: votes[n] += 1
    return sorted([n for n, _ in votes.most_common(pick_count)])


def weighted_freq_predict(draws, n_size, pick_count):
    weights = [0.0] * n_size
    for i, d in enumerate(draws):
        w = 0.99 ** (len(draws) - 1 - i)
        for n in _get_nums(d, pick_count):
            weights[n - 1] += w
    return sorted(range(1, n_size + 1), key=lambda x: weights[x - 1], reverse=True)[:pick_count]


def hot_cold_predict(draws, n_size, pick_count):
    c = Counter()
    for d in draws:
        for n in _get_nums(d, pick_count):
            c[n] += 1
    ranked = sorted(range(1, n_size + 1), key=lambda x: c.get(x, 0), reverse=True)
    hot_count = min(3, pick_count)
    cold_count = pick_count - hot_count
    return sorted(ranked[:hot_count] + ranked[-cold_count:])


def backtest(game, limit=500):
    cfg = GAMES[game]
    N = cfg["max_number"]
    PICK = cfg["pick_count"]

    session = SessionLocal()
    all_draws = session.query(Draw).filter(Draw.game == game).order_by(Draw.draw_date).all()

    if len(all_draws) < 100:
        session.close()
        return {"error": "Need at least 100 draws for backtesting"}

    target_draws = all_draws[-limit:]
    start_idx = len(all_draws) - limit
    lstm_params = load_model(game)

    inserted = {"frequency": 0, "markov": 0, "lstm": 0, "pair_freq": 0, "delta": 0,
                 "ensemble": 0, "weighted_freq": 0, "hot_cold": 0}

    WINDOW = 200

    for i, draw in enumerate(target_draws):
        actual_set = set(_get_nums(draw, PICK))
        idx = start_idx + i
        prior = all_draws[:idx]
        pw = prior[-WINDOW:] if len(prior) > WINDOW else prior

        if len(pw) >= 10:
            wc = Counter()
            for d in pw:
                for n in _get_nums(d, PICK):
                    wc[n] += 1
            sorted_nums = sorted(range(1, N + 1), key=lambda x: wc.get(x, 0), reverse=True)
            freq_picks = sorted_nums[:PICK]
            freq_matches = len(set(freq_picks) & actual_set)
            existing = session.query(Prediction).filter_by(game=game, draw_date=draw.draw_date, method="frequency").first()
            pred_data = {"game": game, "draw_date": draw.draw_date, "method": "frequency", "matches": freq_matches}
            for j, n in enumerate(freq_picks):
                pred_data[f"n{j + 1}"] = n
            if existing:
                for k, v in pred_data.items():
                    setattr(existing, k, v)
            else:
                session.add(Prediction(**pred_data))
            inserted["frequency"] += 1

        if len(pw) >= 2:
            markov_picks = markov_predict(pw, N, PICK)
            if markov_picks:
                markov_matches = len(set(markov_picks) & actual_set)
                existing = session.query(Prediction).filter_by(game=game, draw_date=draw.draw_date, method="markov").first()
                pred_data = {"game": game, "draw_date": draw.draw_date, "method": "markov", "matches": markov_matches}
                for j, n in enumerate(markov_picks):
                    pred_data[f"n{j + 1}"] = n
                if existing:
                    for k, v in pred_data.items():
                        setattr(existing, k, v)
                else:
                    session.add(Prediction(**pred_data))
                inserted["markov"] += 1

            pf_picks = pair_freq_predict(pw, PICK)
            pf_matches = len(set(pf_picks) & actual_set)
            existing = session.query(Prediction).filter_by(game=game, draw_date=draw.draw_date, method="pair_freq").first()
            pred_data = {"game": game, "draw_date": draw.draw_date, "method": "pair_freq", "matches": pf_matches}
            for j, n in enumerate(pf_picks):
                pred_data[f"n{j + 1}"] = n
            if existing:
                for k, v in pred_data.items():
                    setattr(existing, k, v)
            else:
                session.add(Prediction(**pred_data))
            inserted["pair_freq"] += 1

            d_picks = delta_predict(pw, N, PICK)
            d_matches = len(set(d_picks) & actual_set)
            existing = session.query(Prediction).filter_by(game=game, draw_date=draw.draw_date, method="delta").first()
            pred_data = {"game": game, "draw_date": draw.draw_date, "method": "delta", "matches": d_matches}
            for j, n in enumerate(d_picks):
                pred_data[f"n{j + 1}"] = n
            if existing:
                for k, v in pred_data.items():
                    setattr(existing, k, v)
            else:
                session.add(Prediction(**pred_data))
            inserted["delta"] += 1

            e_picks = ensemble_predict(pw, set(freq_picks), N, PICK)
            e_matches = len(set(e_picks) & actual_set)
            existing = session.query(Prediction).filter_by(game=game, draw_date=draw.draw_date, method="ensemble").first()
            pred_data = {"game": game, "draw_date": draw.draw_date, "method": "ensemble", "matches": e_matches}
            for j, n in enumerate(e_picks):
                pred_data[f"n{j + 1}"] = n
            if existing:
                for k, v in pred_data.items():
                    setattr(existing, k, v)
            else:
                session.add(Prediction(**pred_data))
            inserted["ensemble"] += 1

            wf_picks = weighted_freq_predict(pw, N, PICK)
            wf_matches = len(set(wf_picks) & actual_set)
            existing = session.query(Prediction).filter_by(game=game, draw_date=draw.draw_date, method="weighted_freq").first()
            pred_data = {"game": game, "draw_date": draw.draw_date, "method": "weighted_freq", "matches": wf_matches}
            for j, n in enumerate(wf_picks):
                pred_data[f"n{j + 1}"] = n
            if existing:
                for k, v in pred_data.items():
                    setattr(existing, k, v)
            else:
                session.add(Prediction(**pred_data))
            inserted["weighted_freq"] += 1

            hc_picks = hot_cold_predict(pw, N, PICK)
            hc_matches = len(set(hc_picks) & actual_set)
            existing = session.query(Prediction).filter_by(game=game, draw_date=draw.draw_date, method="hot_cold").first()
            pred_data = {"game": game, "draw_date": draw.draw_date, "method": "hot_cold", "matches": hc_matches}
            for j, n in enumerate(hc_picks):
                pred_data[f"n{j + 1}"] = n
            if existing:
                for k, v in pred_data.items():
                    setattr(existing, k, v)
            else:
                session.add(Prediction(**pred_data))
            inserted["hot_cold"] += 1

        if lstm_params and idx >= SEQ_LEN:
            prior_lstm = all_draws[idx - SEQ_LEN : idx]
            seq_oh = np.zeros((SEQ_LEN, N), dtype=np.float32)
            for t, d in enumerate(prior_lstm):
                for n in _get_nums(d, PICK):
                    seq_oh[t, n - 1] = 1.0
            probs = predict_with_model(lstm_params, seq_oh)
            top_indices = np.argsort(probs)[-PICK:][::-1]
            lstm_picks = [int(i) + 1 for i in sorted(top_indices)]
            lstm_matches = len(set(lstm_picks) & actual_set)
            existing = session.query(Prediction).filter_by(game=game, draw_date=draw.draw_date, method="lstm").first()
            pred_data = {"game": game, "draw_date": draw.draw_date, "method": "lstm", "matches": lstm_matches}
            for j, n in enumerate(lstm_picks):
                pred_data[f"n{j + 1}"] = n
            if existing:
                for k, v in pred_data.items():
                    setattr(existing, k, v)
            else:
                session.add(Prediction(**pred_data))
            inserted["lstm"] += 1

        if (i + 1) % 50 == 0:
            session.commit()
            print(f"Backtest progress: {i + 1}/{limit}")

    session.commit()
    total = session.query(Prediction).count()
    session.close()

    print(f"Backtest complete. Inserted/updated: {inserted}. Total predictions in DB: {total}")
    return {"status": "ok", "inserted": inserted}
