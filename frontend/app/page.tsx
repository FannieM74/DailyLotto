"use client";
import { useState, useEffect } from "react";
import { getLatestDraw, getRecentDraws, getWinRates,
  getLstmPrediction, getPairFreqPrediction, getDeltaPrediction,
  getEnsemblePrediction, getWeightedFreqPrediction, getHotColdPrediction } from "@/lib/api";
import NumberBall from "@/components/NumberBall";
import DrawHistory from "@/components/DrawHistory";
import PredictionCard from "@/components/PredictionCard";

interface DrawData {
  id: number;
  date: string;
  numbers: number[];
}

const PREDICTORS: { key: string; label: string; fetcher: () => Promise<any> }[] = [
  { key: "pair_freq", label: "Pair Freq", fetcher: getPairFreqPrediction },
  { key: "delta", label: "Delta", fetcher: getDeltaPrediction },
  { key: "ensemble", label: "Ensemble", fetcher: getEnsemblePrediction },
  { key: "weighted_freq", label: "Weighted", fetcher: getWeightedFreqPrediction },
  { key: "hot_cold", label: "Hot/Cold", fetcher: getHotColdPrediction },
  { key: "lstm", label: "AI", fetcher: getLstmPrediction },
];

export default function Dashboard() {
  const [latest, setLatest] = useState<DrawData | null>(null);
  const [recent, setRecent] = useState<DrawData[]>([]);
  const [winRates, setWinRates] = useState<Record<string, any> | null>(null);
  const [picks, setPicks] = useState<Record<string, number[]>>({});
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    const fallback = setTimeout(() => setLoadError(true), 20000);
    const fetchers = PREDICTORS.map(p => p.fetcher().catch(() => ({ picks: [] })));
    Promise.all([
      getLatestDraw(),
      getRecentDraws(7),
      getWinRates(),
      ...fetchers,
    ]).then(([latestData, recentData, rates, ...predResults]) => {
      clearTimeout(fallback);
      if (!latestData.error) setLatest(latestData);
      setRecent(Array.isArray(recentData) ? recentData : []);
      if (!rates.error) setWinRates(rates);
      const p: Record<string, number[]> = {};
      predResults.forEach((r, i) => { if (r.picks?.length) p[PREDICTORS[i].key] = r.picks; });
      setPicks(p);
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
        {PREDICTORS.map(p => picks[p.key] && <PredictionCard key={p.key} title={p.label} picks={picks[p.key]} />)}
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
