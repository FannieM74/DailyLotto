"use client";
import NumberBall from "./NumberBall";

interface DrawData {
  id: number;
  date: string;
  numbers: number[];
}

export default function DrawHistory({ draws }: { draws: DrawData[] }) {
  if (!draws || draws.length === 0) return null;
  return (
    <div>
      <h2 style={{ marginBottom: "0.75rem" }}>Recent Draws</h2>
      <div className="pred-list">
        {draws.map((d) => (
          <div key={d.id} className="pred-card">
            <div className="pred-card-header">
              <div className="pred-card-date">{d.date}</div>
              <div style={{ color: "var(--text2)", fontSize: "0.85rem" }}>#{d.id}</div>
            </div>
            <div className="balls">
              {d.numbers.map((n: number, i: number) => (
                <NumberBall key={i} n={n} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
