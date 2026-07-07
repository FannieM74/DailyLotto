"use client";
import NumberBall from "./NumberBall";

export default function PredictionCard({
  title,
  picks,
  extra,
}: {
  title: string;
  picks: number[];
  extra?: React.ReactNode;
}) {
  if (!picks || picks.length === 0) return null;
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
