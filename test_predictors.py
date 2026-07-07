"""
Standalone backtest for new predictor candidates.
Loads draw data from JSON, runs walk-forward, reports results.
"""
import json, sys, math
from collections import Counter
import random

random.seed(42)

# ── Load draws ──────────────────────────────────────────────────
with open("/tmp/draws.json") as f:
    raw = json.load(f)

# Sort chronologically (API returns newest first)
draws = list(reversed(raw))
print(f"Loaded {len(draws)} draws: {draws[0]['date']} → {draws[-1]['date']}")

N = 36
PICK = 5

def nums(d):
    return d["numbers"]

def match_count(picks, actual):
    return len(set(picks) & set(actual))

# ── Predictor: Weighted Frequency ───────────────────────────────
def weighted_frequency(all_draws, decay=0.99):
    weights = [0.0] * N
    for i, d in enumerate(all_draws):
        w = decay ** (len(all_draws) - 1 - i)
        for n in nums(d):
            weights[n - 1] += w
    return sorted(range(1, N + 1), key=lambda x: weights[x - 1], reverse=True)[:PICK]

# ── Predictor: Pair Frequency ───────────────────────────────────
def pair_frequency(all_draws):
    pairs = Counter()
    for d in all_draws:
        ns = sorted(nums(d))
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                pairs[(ns[i], ns[j])] += 1
    top_pairs = [p for p, _ in pairs.most_common(50)]
    picked = []
    for a, b in top_pairs:
        if a not in picked: picked.append(a)
        if len(picked) == PICK: break
        if b not in picked: picked.append(b)
        if len(picked) == PICK: break
    return sorted(picked)

# ── Predictor: Delta System ─────────────────────────────────────
def delta_predict(all_draws):
    if len(all_draws) < 2:
        return list(range(1, PICK + 1))
    deltas = Counter()
    for d in all_draws:
        ns = sorted(nums(d))
        for i in range(len(ns) - 1):
            deltas[ns[i + 1] - ns[i]] += 1
    common_deltas = [d for d, _ in deltas.most_common(10)]
    last = sorted(nums(all_draws[-1]))
    picked = set()
    for start in last:
        picked.add(start)
        for delta in common_deltas:
            n = start + delta
            if 1 <= n <= N and n not in picked:
                picked.add(n)
            if len(picked) >= PICK:
                break
        if len(picked) >= PICK:
            break
    while len(picked) < PICK:
        for i in range(1, N + 1):
            if i not in picked:
                picked.add(i)
                if len(picked) >= PICK:
                    break
    return sorted(list(picked))[:PICK]

# ── Predictor: Hot/Cold Mix ─────────────────────────────────────
def hot_cold_mix(all_draws):
    c = Counter()
    for d in all_draws:
        for n in nums(d):
            c[n] += 1
    ranked = sorted(range(1, N + 1), key=lambda x: c.get(x, 0), reverse=True)
    hot = ranked[:3]
    cold = ranked[-2:]
    return sorted(hot + cold)

# ── Predictor: Ensemble Vote ────────────────────────────────────
def ensemble_vote(all_draws):
    from collections import Counter as C
    # Get individual predictions from frequency and markov
    c = Counter()
    for d in all_draws:
        for n in nums(d):
            c[n] += 1
    freq_picks = set(sorted(range(1, N + 1), key=lambda x: c.get(x, 0), reverse=True)[:PICK])

    # Markov
    if len(all_draws) >= 2:
        matrix = [[0.0] * N for _ in range(N)]
        for i in range(len(all_draws) - 1):
            curr = set(nums(all_draws[i]))
            nxt = set(nums(all_draws[i + 1]))
            for ci in curr:
                for ni in nxt:
                    matrix[ci - 1][ni - 1] += 1
        row_sums = [sum(r) for r in matrix]
        for i in range(N):
            if row_sums[i] > 0:
                matrix[i] = [v / row_sums[i] for v in matrix[i]]
        last = nums(all_draws[-1])
        cand = {}
        for n in last:
            for i in range(N):
                if matrix[n - 1][i] > 0:
                    cand[i + 1] = cand.get(i + 1, 0) + matrix[n - 1][i]
        sc = sorted(cand.items(), key=lambda x: x[1], reverse=True)
        markov_picks = set()
        for num, _ in sc:
            markov_picks.add(num)
            if len(markov_picks) == PICK:
                break
    else:
        markov_picks = set()

    # Weighted freq
    weights = [0.0] * N
    for i, d in enumerate(all_draws):
        w = 0.99 ** (len(all_draws) - 1 - i)
        for n in nums(d):
            weights[n - 1] += w
    wfreq_picks = set(sorted(range(1, N + 1), key=lambda x: weights[x - 1], reverse=True)[:PICK])

    # Vote
    votes = Counter()
    for n in freq_picks: votes[n] += 1
    for n in markov_picks: votes[n] += 1
    for n in wfreq_picks: votes[n] += 1
    return sorted([n for n, _ in votes.most_common(PICK)])

# ── Predictor: Naive Bayes ──────────────────────────────────────
def naive_bayes(all_draws):
    if len(all_draws) < 2:
        return list(range(1, PICK + 1))
    # P(number | previous draw's numbers) ≈ count(co-occurrences) / count(previous appears)
    cooc = [[0] * N for _ in range(N)]
    prev_count = [0] * N
    for i in range(len(all_draws) - 1):
        prev_set = set(nums(all_draws[i]))
        curr_set = set(nums(all_draws[i + 1]))
        for p in prev_set:
            prev_count[p - 1] += 1
            for c in curr_set:
                cooc[p - 1][c - 1] += 1
    last = nums(all_draws[-1])
    scores = [0.0] * N
    for p in last:
        for n in range(1, N + 1):
            prob = cooc[p - 1][n - 1] / max(prev_count[p - 1], 1)
            scores[n - 1] += prob
    return sorted(range(1, N + 1), key=lambda x: scores[x - 1], reverse=True)[:PICK]

# ── Baseline: Frequency ─────────────────────────────────────────
def frequency_predict(all_draws):
    c = Counter()
    for d in all_draws:
        for n in nums(d):
            c[n] += 1
    return sorted(range(1, N + 1), key=lambda x: c.get(x, 0), reverse=True)[:PICK]

# ── Baseline: Markov ────────────────────────────────────────────
def markov_predict(all_draws):
    if len(all_draws) < 2:
        return None
    matrix = [[0.0] * N for _ in range(N)]
    for i in range(len(all_draws) - 1):
        curr = set(nums(all_draws[i]))
        nxt = set(nums(all_draws[i + 1]))
        for ci in curr:
            for ni in nxt:
                matrix[ci - 1][ni - 1] += 1
    row_sums = [sum(r) for r in matrix]
    for i in range(N):
        if row_sums[i] > 0:
            matrix[i] = [v / row_sums[i] for v in matrix[i]]
    last = nums(all_draws[-1])
    cand = {}
    for n in last:
        for i in range(N):
            if matrix[n - 1][i] > 0:
                cand[i + 1] = cand.get(i + 1, 0) + matrix[n - 1][i]
    sc = sorted(cand.items(), key=lambda x: x[1], reverse=True)
    picked = []
    for num, _ in sc:
        if num not in picked: picked.append(num)
        if len(picked) == PICK: break
    while len(picked) < PICK:
        for i in range(1, N + 1):
            if i not in picked:
                picked.append(i)
                if len(picked) == PICK: break
    return picked

# ── Run backtest ────────────────────────────────────────────────
PREDICTORS = [
    ("Weighted Freq", weighted_frequency),
    ("Pair Freq",     pair_frequency),
    ("Delta System",  delta_predict),
    ("Hot/Cold Mix",  hot_cold_mix),
    ("Ensemble Vote", ensemble_vote),
    ("Naive Bayes",   naive_bayes),
    ("Frequency",     frequency_predict),
    ("Markov",        markov_predict),
]

MIN_DRAWS = 100
results = {}

for name, fn in PREDICTORS:
    stats = {"total": 0, "matches": 0, "wins_2plus": 0, "wins_3plus": 0,
             "streak": 0, "best_streak": 0, "max_match": 0}
    for i in range(MIN_DRAWS, len(draws)):
        prior = draws[:i]
        actual = nums(draws[i])
        picks = fn(prior)
        if picks is None:
            continue
        m = match_count(picks, actual)
        stats["total"] += 1
        stats["matches"] += m
        stats["max_match"] = max(stats["max_match"], m)
        if m >= 2:
            stats["wins_2plus"] += 1
            stats["streak"] += 1
        else:
            stats["streak"] = 0
        if m >= 3:
            stats["wins_3plus"] += 1
        stats["best_streak"] = max(stats["best_streak"], stats["streak"])

    avg = round(stats["matches"] / stats["total"], 2) if stats["total"] else 0
    wr2 = round(stats["wins_2plus"] / stats["total"] * 100, 1) if stats["total"] else 0
    wr3 = round(stats["wins_3plus"] / stats["total"] * 100, 1) if stats["total"] else 0
    results[name] = (avg, wr2, wr3, stats["best_streak"], stats["max_match"])
    print(f"  {name:20s}  avg={avg:>4}  2+={wr2:>5.1f}%  3+={wr3:>5.1f}%  streak={stats['best_streak']:>3}  max={stats['max_match']}  (n={stats['total']})")

# ── Summary ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print(f"{'Predictor':20s}  {'Avg':>4}  {'2+ Rate':>7}  {'3+ Rate':>7}  {'Streak':>6}  {'Max':>3}")
print("-" * 70)
for name in ["Weighted Freq", "Pair Freq", "Delta System", "Hot/Cold Mix",
              "Ensemble Vote", "Naive Bayes", "Frequency", "Markov"]:
    avg, wr2, wr3, streak, mx = results[name]
    print(f"{name:20s}  {avg:>4}  {wr2:>6.1f}%  {wr3:>6.1f}%  {streak:>5}   {mx:>2}")
print("-" * 70)
print("Baseline (from VPS backtest): LSTM avg=3.02 2+=96.0% 3+=74.4% (inflated by data overlap)")
print("=" * 70)
