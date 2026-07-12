"use client";
import NumberBall from "./NumberBall";

export default function PredictionCard({
  title,
  picks,
  drawNumbers,
  matches,
  extra,
}: {
  title: string;
  picks: number[];
  drawNumbers?: number[];
  matches?: number | null;
  extra?: React.ReactNode;
}) {
  if (!picks || picks.length === 0) return null;

  if (drawNumbers) {
    const drawSet = new Set(drawNumbers);
    return (
      <div className="card result-card">
        <div className="pred-card-header">
          <h2 style={{ margin: 0, fontSize: "1rem" }}>{title}</h2>
          {matches !== undefined && matches !== null && (
            <span className={`match-badge match-${matches}`}>
              {matches} match{matches !== 1 ? "es" : ""}
            </span>
          )}
        </div>
        <div className="result-row">
          <span className="result-label">Pred:</span>
          <div className="balls">
            {picks.map((n, i) => (
              <NumberBall key={i} n={n} small matched={drawSet.has(n)} />
            ))}
          </div>
        </div>
        <div className="result-row">
          <span className="result-label">Draw:</span>
          <div className="balls">
            {drawNumbers.map((n, i) => (
              <NumberBall key={i} n={n} small matched={drawSet.has(n)} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>{title}</h2>
      <div className="balls" style={{ marginBottom: "0.75rem" }}>
        {picks.map((n, i) => (
          <NumberBall key={i} n={n} />
        ))}
      </div>
      {extra && <div style={{ color: "var(--text2)", fontSize: "0.9rem" }}>{extra}</div>}
    </div>
  );
}
