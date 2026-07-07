"use client";
import { useState, useEffect } from "react";
import { getTracker, getWinRates,
  getPairFreqPrediction, getDeltaPrediction, getEnsemblePrediction,
  getWeightedFreqPrediction, getHotColdPrediction, getLstmPrediction } from "@/lib/api";
import NumberBall from "@/components/NumberBall";

const METHOD_COLORS: Record<string, string> = {
  frequency: "var(--accent)",
  markov: "#f59e0b",
  lstm: "var(--accent2)",
  pair_freq: "#10b981",
  delta: "#8b5cf6",
  ensemble: "#f97316",
  weighted_freq: "#06b6d4",
  hot_cold: "#ec4899",
};

const METHOD_LABELS: Record<string, string> = {
  frequency: "F",
  markov: "M",
  lstm: "L",
  pair_freq: "PF",
  delta: "D",
  ensemble: "E",
  weighted_freq: "W",
  hot_cold: "HC",
};

function TrackerBall({ n, matched }: { n: number; matched: boolean }) {
  const hue = (n * 10) % 360;
  return (
    <span
      className={`ball${matched ? " matched" : ""}`}
      style={{
        background: `linear-gradient(135deg, hsl(${hue}, 70%, 50%), hsl(${hue + 40}, 70%, 55%))`,
      }}
    >
      {n}
    </span>
  );
}

function MethodBadge({ method }: { method: string }) {
  return (
    <span
      className="method-badge"
      style={{ background: METHOD_COLORS[method] || "var(--accent)" }}
    >
      {METHOD_LABELS[method] || method[0].toUpperCase()}
    </span>
  );
}

const TODAY_FETCHERS: { key: string; fn: () => Promise<any> }[] = [
  { key: "pair_freq", fn: () => getPairFreqPrediction().catch(() => ({ picks: [] })) },
  { key: "delta", fn: () => getDeltaPrediction().catch(() => ({ picks: [] })) },
  { key: "ensemble", fn: () => getEnsemblePrediction().catch(() => ({ picks: [] })) },
  { key: "weighted_freq", fn: () => getWeightedFreqPrediction().catch(() => ({ picks: [] })) },
  { key: "hot_cold", fn: () => getHotColdPrediction().catch(() => ({ picks: [] })) },
  { key: "lstm", fn: () => getLstmPrediction().catch(() => ({ picks: [] })) },
];

const METHOD_NAMES: Record<string, string> = {
  pair_freq: "Pair Freq",
  delta: "Delta",
  ensemble: "Ensemble",
  weighted_freq: "Weighted",
  hot_cold: "Hot/Cold",
  lstm: "LSTM",
  frequency: "Frequency",
  markov: "Markov",
};

export default function TrackerPage() {
  const [predictions, setPredictions] = useState<any[]>([]);
  const [winRates, setWinRates] = useState<Record<string, any> | null>(null);
  const [todaysPicks, setTodaysPicks] = useState<Record<string, number[]>>({});
  const [loading, setLoading] = useState(true);
  const [filterMethod, setFilterMethod] = useState("all");

  useEffect(() => {
    Promise.all([
      getTracker(),
      getWinRates(),
      ...TODAY_FETCHERS.map(t => t.fn()),
    ]).then(([preds, rates, ...predResults]) => {
      if (Array.isArray(preds)) setPredictions(preds);
      if (!rates.error) setWinRates(rates);
      const picks: Record<string, number[]> = {};
      predResults.forEach((r, i) => { if (r.picks?.length) picks[TODAY_FETCHERS[i].key] = r.picks; });
      setTodaysPicks(picks);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">Loading tracker...</div>;

  const filteredPreds = filterMethod === "all"
    ? predictions
    : predictions.filter((p) => p.method === filterMethod);

  const filteredWinRates = winRates && filterMethod !== "all"
    ? { [filterMethod]: winRates[filterMethod] }
    : winRates;

  const filteredTodaysPicks = filterMethod === "all"
    ? todaysPicks
    : { [filterMethod]: todaysPicks[filterMethod] };

  return (
    <div>
      <h1>Prediction Tracker</h1>
      <p style={{ color: "var(--text2)", marginBottom: "1rem" }}>
        Tracks accuracy of stored predictions vs actual draw results
      </p>

      <div className="filter-bar">
        <label>Method:</label>
        <select value={filterMethod} onChange={(e) => setFilterMethod(e.target.value)}>
          <option value="all">All Methods</option>
          <option value="pair_freq">Pair Freq</option>
          <option value="delta">Delta</option>
          <option value="ensemble">Ensemble</option>
          <option value="weighted_freq">Weighted</option>
          <option value="hot_cold">Hot/Cold</option>
          <option value="lstm">LSTM</option>
          <option value="frequency">Frequency</option>
          <option value="markov">Markov</option>
        </select>
      </div>

      {Object.keys(filteredTodaysPicks).length > 0 && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ margin: "0 0 0.5rem" }}>Today's Predictions</h3>
          {(Object.entries(filteredTodaysPicks) as [string, number[]][]).map(([method, picks]) => (
            <div key={method} style={{
              display: "flex", alignItems: "center", gap: "0.75rem",
              marginBottom: "0.4rem", fontSize: "0.85rem"
            }}>
              <span style={{ textTransform: "capitalize", fontWeight: 600, minWidth: "5rem" }}>{METHOD_NAMES[method] || method}</span>
              {picks.map((n, i) => <NumberBall key={i} n={n} small />)}
            </div>
          ))}
        </div>
      )}

      {filteredWinRates && (
        <div className="grid-3" style={{ marginBottom: "1.5rem" }}>
          {Object.entries(filteredWinRates).map(([method, stats]: [string, any]) => (
            <div className="card" key={method} style={{ margin: 0 }}>
              <h2 style={{ textTransform: "capitalize" }}>{method}</h2>
              <div className="stats-row">
                <div className="stat">
                  <div className="stat-value">{stats.total_predictions}</div>
                  <div className="stat-label">Total</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{stats.avg_matches}</div>
                  <div className="stat-label">Avg</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{(stats.win_rate_2plus * 100).toFixed(0)}%</div>
                  <div className="stat-label">Win (2+)</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{stats.best_streak}</div>
                  <div className="stat-label">Streak</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <h2 style={{ marginBottom: "0.75rem" }}>
        Recent Predictions
        {filterMethod !== "all" && (
          <span style={{ textTransform: "capitalize", color: "var(--text2)", fontWeight: 400, fontSize: "0.9rem" }}>
            {" "}({filterMethod})
          </span>
        )}
      </h2>

      {filteredPreds.length === 0 ? (
        <div className="card">
          <p style={{ color: "var(--text2)" }}>
            No predictions found{filterMethod !== "all" ? ` for ${filterMethod}` : ""}.
            {predictions.length === 0 && <> Run <code>POST /retrain</code> to generate daily predictions.</>}
          </p>
        </div>
      ) : (
        <div className="pred-list">
          {filteredPreds.map((p) => {
            const matchSet = new Set(p.matching_numbers || []);
            return (
              <div key={p.id} className="pred-card">
                <div className="pred-card-header">
                  <div className="pred-card-date">
                    {p.date}
                    <MethodBadge method={p.method} />
                  </div>
                  <div>
                    {p.matches !== null ? (
                      <span className={`match-badge match-${p.matches}`}>
                        {p.matches} match{p.matches !== 1 ? "es" : ""}
                      </span>
                    ) : (
                      <span style={{ color: "var(--text2)", fontSize: "0.8rem" }}>Pending</span>
                    )}
                  </div>
                </div>
                <div className="pred-row">
                  <div className="balls">
                    {p.prediction.map((n: number, i: number) => (
                      <TrackerBall key={i} n={n} matched={matchSet.has(n)} />
                    ))}
                  </div>
                </div>
                <div className="pred-actual-row">
                  {p.draw_numbers ? (
                    <div className="actual-balls">
                      {p.draw_numbers.map((n: number, i: number) => (
                        <span key={i} className="actual-ball">{n}</span>
                      ))}
                    </div>
                  ) : (
                    <span style={{ color: "var(--text2)", fontSize: "0.8rem" }}>No draw yet</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
