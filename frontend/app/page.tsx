"use client";
import { useState, useEffect } from "react";
import { getLatestDraw, getRecentDraws, getWinRates, getFrequencyPrediction, getMarkovPrediction, getLstmPrediction } from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import DrawHistory from "@/components/DrawHistory";
import PredictionCard from "@/components/PredictionCard";

interface DrawData {
  id: number;
  date: string;
  numbers: number[];
}

export default function Dashboard() {
  const [latest, setLatest] = useState<DrawData | null>(null);
  const [recent, setRecent] = useState<DrawData[]>([]);
  const [winRates, setWinRates] = useState<Record<string, any> | null>(null);
  const [freqPicks, setFreqPicks] = useState<number[] | null>(null);
  const [markovPicks, setMarkovPicks] = useState<number[] | null>(null);
  const [lstmPicks, setLstmPicks] = useState<number[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    const fallback = setTimeout(() => setLoadError(true), 20000);
    Promise.all([
      getLatestDraw(),
      getRecentDraws(7),
      getWinRates(),
      getFrequencyPrediction(),
      getMarkovPrediction(),
      getLstmPrediction(),
    ]).then(([latestData, recentData, rates, freq, markov, lstm]) => {
      clearTimeout(fallback);
      if (!latestData.error) setLatest(latestData);
      setRecent(Array.isArray(recentData) ? recentData : []);
      if (!rates.error) setWinRates(rates);
      if (!freq.error) setFreqPicks(freq.picks);
      if (!markov.error) setMarkovPicks(markov.picks);
      if (!lstm.error) setLstmPicks(lstm.picks);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">{loadError ? "Dashboard timed out — please refresh" : "Loading dashboard..."}</div>;

  return (
    <div>
      <h1>DailyLotto Dashboard</h1>

      {latest && (
        <div className="pred-card" style={{ marginBottom: "1.25rem" }}>
          <div className="pred-card-header">
            <div className="pred-card-date">{latest.date}</div>
            <div style={{ color: "var(--text2)", fontSize: "0.85rem" }}>#{latest.id}</div>
          </div>
          <div className="balls">
            {latest.numbers.map((n, i) => (
              <NumberBall key={i} n={n} />
            ))}
          </div>
        </div>
      )}

      <div className="grid-3">
        <h2 style={{gridColumn: "1 / -1", marginBottom: 0}}>Today's Predictions</h2>
        {freqPicks && <PredictionCard title="Frequency" picks={freqPicks} />}
        {markovPicks && <PredictionCard title="Markov" picks={markovPicks} />}
        {lstmPicks && <PredictionCard title="AI" picks={lstmPicks} />}
      </div>

      {winRates && (
        <div className="card">
          <h2>Win Rates</h2>
          <div className="grid-2">
            {Object.entries(winRates).map(([method, stats]: [string, any]) => (
              <div key={method} className="card" style={{ margin: 0 }}>
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
        </div>
      )}

      <DrawHistory draws={recent} />
    </div>
  );
}
