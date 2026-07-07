"use client";
import { useState, useEffect } from "react";
import { getMarkovPrediction, getWinRates } from "@/lib/api";
import PredictionCard from "@/components/PredictionCard";

export default function MarkovPage() {
  const [data, setData] = useState<any>(null);
  const [winRate, setWinRate] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getMarkovPrediction(), getWinRates()]).then(([d, rates]) => {
      if (!d.error) setData(d);
      if (!rates.error && rates.markov) setWinRate(rates.markov);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">Loading Markov chain analysis...</div>;
  if (!data) return <div className="error">Failed to load Markov data</div>;

  return (
    <div>
      <h1>Markov Chain Analysis</h1>
      <p style={{ color: "var(--text2)", marginBottom: "1rem" }}>
        Predicts numbers based on transition probabilities from the last draw
      </p>

      <PredictionCard
        title="Markov Prediction"
        picks={data.picks}
        extra={`Confidence: ${((data.confidence || 0) * 100).toFixed(1)}%`}
      />

      {winRate && (
        <div className="card">
          <h2>Prediction Win Rate</h2>
          <div className="grid-4">
            <div className="stat">
              <div className="stat-value">{winRate.total_predictions}</div>
              <div className="stat-label">Predictions</div>
            </div>
            <div className="stat">
              <div className="stat-value">{winRate.avg_matches}</div>
              <div className="stat-label">Avg Matches</div>
            </div>
            <div className="stat">
              <div className="stat-value">{(winRate.win_rate_2plus * 100).toFixed(0)}%</div>
              <div className="stat-label">Win (2+)</div>
            </div>
            <div className="stat">
              <div className="stat-value">{winRate.best_streak}</div>
              <div className="stat-label">Best Streak</div>
            </div>
          </div>
        </div>
      )}

      {data.last_draw && (
        <div className="card">
          <h2>Last Draw (Reference)</h2>
          <p style={{ color: "var(--text2)", marginBottom: "0.5rem" }}>{data.last_draw.date}</p>
          <div className="balls">
            {data.last_draw.numbers.map((n: number, i: number) => (
              <span key={i} className="ball" style={{ background: "var(--surface2)", color: "var(--text2)" }}>{n}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
