from database import SessionLocal, Draw, Prediction
from collections import Counter
import numpy as np
from models.lstm import load_model, predict_with_model, SEQ_LEN, NUM_NUMBERS

N = 36
PICK = 5


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


def pair_freq_predict(draws):
    pairs = Counter()
    for d in draws:
        ns = sorted([d.n1, d.n2, d.n3, d.n4, d.n5])
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                pairs[(ns[i], ns[j])] += 1
    top = [p for p, _ in pairs.most_common(50)]
    picked = []
    for a, b in top:
        if a not in picked: picked.append(a)
        if len(picked) == 5: break
        if b not in picked: picked.append(b)
        if len(picked) == 5: break
    return sorted(picked)


def delta_predict(draws):
    if not draws:
        return list(range(1, 6))
    deltas = Counter()
    for d in draws:
        ns = sorted([d.n1, d.n2, d.n3, d.n4, d.n5])
        for i in range(len(ns) - 1):
            deltas[ns[i + 1] - ns[i]] += 1
    common = [d for d, _ in deltas.most_common(10)]
    last_nums = [draws[-1].n1, draws[-1].n2, draws[-1].n3, draws[-1].n4, draws[-1].n5]
    last = sorted(last_nums)
    picked = set()
    for start in last:
        picked.add(start)
        for delta in common:
            n = start + delta
            if 1 <= n <= 36 and n not in picked:
                picked.add(n)
            if len(picked) >= 5:
                break
        if len(picked) >= 5:
            break
    fill = 1
    while len(picked) < 5:
        if fill not in picked:
            picked.add(fill)
        fill += 1
    return sorted(list(picked))[:5]


def ensemble_predict(draws, freq_set):
    weights = [0.0] * 36
    for i, d in enumerate(draws):
        w = 0.99 ** (len(draws) - 1 - i)
        for n in [d.n1, d.n2, d.n3, d.n4, d.n5]:
            weights[n - 1] += w
    wfreq = set(sorted(range(1, 37), key=lambda x: weights[x - 1], reverse=True)[:5])
    votes = Counter()
    for n in freq_set: votes[n] += 1
    for n in wfreq: votes[n] += 1
    return sorted([n for n, _ in votes.most_common(5)])


def weighted_freq_predict(draws):
    weights = [0.0] * 36
    for i, d in enumerate(draws):
        w = 0.99 ** (len(draws) - 1 - i)
        for n in [d.n1, d.n2, d.n3, d.n4, d.n5]:
            weights[n - 1] += w
    return sorted(range(1, 37), key=lambda x: weights[x - 1], reverse=True)[:5]


def hot_cold_predict(draws):
    c = Counter()
    for d in draws:
        for n in [d.n1, d.n2, d.n3, d.n4, d.n5]:
            c[n] += 1
    ranked = sorted(range(1, 37), key=lambda x: c.get(x, 0), reverse=True)
    return sorted(ranked[:3] + ranked[-2:])


def backtest(limit=500):
    session = SessionLocal()
    all_draws = session.query(Draw).order_by(Draw.draw_date).all()

    if len(all_draws) < 100:
        session.close()
        return {"error": "Need at least 100 draws for backtesting"}

    target_draws = all_draws[-limit:]
    start_idx = len(all_draws) - limit
    lstm_params = load_model()

    counter = Counter()
    for d in all_draws[:start_idx]:
        counter[d.n1] += 1
        counter[d.n2] += 1
        counter[d.n3] += 1
        counter[d.n4] += 1
        counter[d.n5] += 1

    inserted = {"frequency": 0, "markov": 0, "lstm": 0, "pair_freq": 0, "delta": 0,
                 "ensemble": 0, "weighted_freq": 0, "hot_cold": 0}

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

        if idx >= 1:
            prior = all_draws[:idx]

            pf_picks = pair_freq_predict(prior)
            pf_matches = len(set(pf_picks) & actual_set)
            existing = session.query(Prediction).filter_by(draw_date=draw.draw_date, method="pair_freq").first()
            if existing:
                existing.n1, existing.n2, existing.n3, existing.n4, existing.n5 = pf_picks
                existing.matches = pf_matches
            else:
                session.add(Prediction(
                    draw_date=draw.draw_date, method="pair_freq",
                    n1=pf_picks[0], n2=pf_picks[1], n3=pf_picks[2], n4=pf_picks[3], n5=pf_picks[4],
                    matches=pf_matches,
                ))
            inserted["pair_freq"] += 1

            d_picks = delta_predict(prior)
            d_matches = len(set(d_picks) & actual_set)
            existing = session.query(Prediction).filter_by(draw_date=draw.draw_date, method="delta").first()
            if existing:
                existing.n1, existing.n2, existing.n3, existing.n4, existing.n5 = d_picks
                existing.matches = d_matches
            else:
                session.add(Prediction(
                    draw_date=draw.draw_date, method="delta",
                    n1=d_picks[0], n2=d_picks[1], n3=d_picks[2], n4=d_picks[3], n5=d_picks[4],
                    matches=d_matches,
                ))
            inserted["delta"] += 1

            e_picks = ensemble_predict(prior, set(freq_picks))
            e_matches = len(set(e_picks) & actual_set)
            existing = session.query(Prediction).filter_by(draw_date=draw.draw_date, method="ensemble").first()
            if existing:
                existing.n1, existing.n2, existing.n3, existing.n4, existing.n5 = e_picks
                existing.matches = e_matches
            else:
                session.add(Prediction(
                    draw_date=draw.draw_date, method="ensemble",
                    n1=e_picks[0], n2=e_picks[1], n3=e_picks[2], n4=e_picks[3], n5=e_picks[4],
                    matches=e_matches,
                ))
            inserted["ensemble"] += 1

            wf_picks = weighted_freq_predict(prior)
            wf_matches = len(set(wf_picks) & actual_set)
            existing = session.query(Prediction).filter_by(draw_date=draw.draw_date, method="weighted_freq").first()
            if existing:
                existing.n1, existing.n2, existing.n3, existing.n4, existing.n5 = wf_picks
                existing.matches = wf_matches
            else:
                session.add(Prediction(
                    draw_date=draw.draw_date, method="weighted_freq",
                    n1=wf_picks[0], n2=wf_picks[1], n3=wf_picks[2], n4=wf_picks[3], n5=wf_picks[4],
                    matches=wf_matches,
                ))
            inserted["weighted_freq"] += 1

            hc_picks = hot_cold_predict(prior)
            hc_matches = len(set(hc_picks) & actual_set)
            existing = session.query(Prediction).filter_by(draw_date=draw.draw_date, method="hot_cold").first()
            if existing:
                existing.n1, existing.n2, existing.n3, existing.n4, existing.n5 = hc_picks
                existing.matches = hc_matches
            else:
                session.add(Prediction(
                    draw_date=draw.draw_date, method="hot_cold",
                    n1=hc_picks[0], n2=hc_picks[1], n3=hc_picks[2], n4=hc_picks[3], n5=hc_picks[4],
                    matches=hc_matches,
                ))
            inserted["hot_cold"] += 1

        if lstm_params and idx >= SEQ_LEN:
            prior = all_draws[idx - SEQ_LEN : idx]
            seq_oh = np.zeros((SEQ_LEN, NUM_NUMBERS), dtype=np.float32)
            for t, d in enumerate(prior):
                for n in [d.n1, d.n2, d.n3, d.n4, d.n5]:
                    seq_oh[t, n - 1] = 1.0
            probs = predict_with_model(lstm_params, seq_oh)
            top_indices = np.argsort(probs)[-5:][::-1]
            lstm_picks = [int(i) + 1 for i in sorted(top_indices)]
            lstm_matches = len(set(lstm_picks) & actual_set)
            existing = session.query(Prediction).filter_by(draw_date=draw.draw_date, method="lstm").first()
            if existing:
                existing.n1, existing.n2, existing.n3, existing.n4, existing.n5 = lstm_picks
                existing.matches = lstm_matches
            else:
                session.add(Prediction(
                    draw_date=draw.draw_date, method="lstm",
                    n1=lstm_picks[0], n2=lstm_picks[1], n3=lstm_picks[2], n4=lstm_picks[3], n5=lstm_picks[4],
                    matches=lstm_matches,
                ))
            inserted["lstm"] += 1

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
