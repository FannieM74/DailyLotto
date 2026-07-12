"use client";
import { useState, useEffect } from "react";
import { getTracker, getWinRates, getTodayPredictions } from "@/lib/api";
import { useGame } from "@/context/GameContext";
import NumberBall from "@/components/NumberBall";
import TodaysPredictions from "@/components/TodaysPredictions";
import { METHOD_COLORS, METHOD_LABELS, METHOD_NAMES } from "@/lib/constants";

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

function ConsensusRow({ picks }: { picks: Record<string, number[]> }) {
  const counter: Record<number, number> = {};
  const totalMethods = Object.keys(picks).length;
  for (const nums of Object.values(picks)) {
    for (const n of nums) {
      counter[n] = (counter[n] || 0) + 1;
    }
  }
  const sorted = Object.entries(counter).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const maxCount = sorted[0]?.[1] || 0;
  return (
    <div className="consensus-row">
      <span className="consensus-label">Consensus</span>
      {sorted.map(([num, count]) => (
        <span key={num} className={`consensus-ball${count === totalMethods ? " consensus-unanimous" : ""}`}>
          <span className="consensus-num">{num}</span>
          <span className="consensus-count">×{count}</span>
        </span>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const { game, method } = useGame();
  const [predictions, setPredictions] = useState<any[]>([]);
  const [winRates, setWinRates] = useState<Record<string, any> | null>(null);
  const [todaysPicks, setTodaysPicks] = useState<Record<string, number[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getTracker(game),
      getWinRates(game),
      getTodayPredictions(game),
    ]).then(([preds, rates, today]) => {
      if (Array.isArray(preds)) setPredictions(preds);
      if (!rates.error) setWinRates(rates);
      if (today?.picks) setTodaysPicks(today.picks);
      else setTodaysPicks({});
      setLoading(false);
    });
  }, [game]);

  if (loading) return <div className="loading">Loading...</div>;

  const filteredPreds = method === "all"
    ? predictions
    : predictions.filter((p) => p.method === method);

  const filteredWinRates = winRates && method !== "all"
    ? { [method]: winRates[method] }
    : winRates;

  const filteredTodaysPicks = method === "all"
    ? todaysPicks
    : todaysPicks[method] ? { [method]: todaysPicks[method] } : {};

  // Consensus is only shown when method is "all" and we have multiple methods with picks
  const consensusPicks = method === "all" && Object.keys(todaysPicks).length > 0
    ? (() => {
        const byDate: Record<string, Record<string, number[]>> = {};
        for (const p of predictions) {
          if (!byDate[p.date]) byDate[p.date] = {};
          const nums = [p.prediction].flat();
          byDate[p.date][p.method] = nums;
        }
        const dates = Object.keys(byDate).sort().reverse();
        return dates.length > 0 ? byDate[dates[0]] : {};
      })()
    : {};

  return (
    <div>
      <h1>Dashboard</h1>

      <TodaysPredictions todaysPicks={filteredTodaysPicks} method={method} />

      {method === "all" && Object.keys(consensusPicks).length > 1 && (
        <ConsensusRow picks={consensusPicks} />
      )}

      {filteredWinRates && (
        <div className="grid-3" style={{ marginBottom: "1.5rem" }}>
          {Object.entries(filteredWinRates).map(([methodKey, stats]: [string, any]) => (
            stats && (
              <div className="card" key={methodKey} style={{ margin: 0 }}>
                <h2>{METHOD_NAMES[methodKey] || methodKey}</h2>
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
            )
          ))}
        </div>
      )}

      <h2 style={{ marginBottom: "0.75rem" }}>
        Recent Predictions
        {method !== "all" && (
          <span style={{ color: "var(--text2)", fontWeight: 400, fontSize: "0.9rem" }}>
            {" "}({METHOD_NAMES[method] || method})
          </span>
        )}
      </h2>

      {filteredPreds.length === 0 ? (
        <div className="card">
          <p style={{ color: "var(--text2)" }}>
            No predictions found{method !== "all" ? ` for ${method}` : ""}.
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
