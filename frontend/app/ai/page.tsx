"use client";
import { useState, useEffect } from "react";
import { getLstmPrediction, getWinRates } from "@/lib/api";
import PredictionCard from "@/components/PredictionCard";

export default function AiPage() {
  const [data, setData] = useState<any>(null);
  const [winRate, setWinRate] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getLstmPrediction(), getWinRates()]).then(([d, rates]) => {
      if (!d.error) setData(d);
      if (!rates.error && rates.lstm) setWinRate(rates.lstm);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">Loading AI prediction...</div>;

  return (
    <div>
      <h1>AI Prediction (LSTM)</h1>
      <p style={{ color: "var(--text2)", marginBottom: "1rem" }}>
        Deep learning model trained on historical draw sequences
      </p>

      {data && !data.error ? (
        <>
          <PredictionCard
            title="LSTM Prediction"
            picks={data.picks}
            extra={data.probabilities ? `Top probability: ${(data.probabilities[0] * 100).toFixed(1)}%` : undefined}
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

          {data.probabilities && (
            <div className="card">
              <h2>Probability Distribution</h2>
              {data.picks.map((n: number, i: number) => (
                <div className="chart-bar" key={i}>
                  <span className="chart-bar-label">{n}</span>
                  <div
                    className="chart-bar-fill"
                    style={{ width: `${data.probabilities[i] * 100}%` }}
                  />
                  <span className="chart-bar-count">
                    {(data.probabilities[i] * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <div className="card" style={{ textAlign: "center" }}>
          <p style={{ color: "var(--yellow)", marginBottom: "0.5rem" }}>
            {data?.error || "No trained model available"}
          </p>
          <p style={{ color: "var(--text2)", fontSize: "0.9rem" }}>
            Run the retrain endpoint to train the LSTM model: <code>POST /retrain</code>
          </p>
        </div>
      )}
    </div>
  );
}
