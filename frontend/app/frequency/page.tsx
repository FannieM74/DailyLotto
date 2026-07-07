"use client";
import { useState, useEffect } from "react";
import { getFrequencyPrediction, getWinRates } from "@/lib/api";
import PredictionCard from "@/components/PredictionCard";
import FrequencyChart from "@/components/FrequencyChart";

export default function FrequencyPage() {
  const [data, setData] = useState<any>(null);
  const [winRate, setWinRate] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getFrequencyPrediction(), getWinRates()]).then(([d, rates]) => {
      if (!d.error) setData(d);
      if (!rates.error && rates.frequency) setWinRate(rates.frequency);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">Loading frequency analysis...</div>;
  if (!data) return <div className="error">Failed to load frequency data</div>;

  return (
    <div>
      <h1>Frequency Analysis</h1>
      <p style={{ color: "var(--text2)", marginBottom: "1rem" }}>
        Based on {data.total_draws} historical draws
      </p>

      <PredictionCard
        title="Hot Numbers (Most Frequent)"
        picks={data.hot}
        extra="Top 5 most frequently drawn numbers"
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

      <div className="grid-2">
        <div className="card">
          <h2>Cold Numbers (Least Frequent)</h2>
          <div className="balls">
            {data.cold.map((n: number, i: number) => (
              <span key={i} className="ball" style={{ background: "var(--surface2)", color: "var(--text2)" }}>{n}</span>
            ))}
          </div>
        </div>
        <div className="card">
          <h2>Overdue Numbers</h2>
          <div className="balls">
            {data.overdue.map((n: number, i: number) => (
              <span key={i} className="ball" style={{ background: "linear-gradient(135deg, #f59e0b, #ef4444)" }}>{n}</span>
            ))}
          </div>
        </div>
      </div>

      <FrequencyChart counts={data.counts} />
    </div>
  );
}
