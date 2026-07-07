"use client";

export default function FrequencyChart({ counts }: { counts: number[] }) {
  if (!counts || counts.length === 0) return null;
  const maxCount = Math.max(...counts);
  return (
    <div className="card">
      <h2>Number Frequency (1-36)</h2>
      <div style={{ maxHeight: 500, overflowY: "auto", paddingRight: 8 }}>
        {counts.map((c, i) => (
          <div className="chart-bar" key={i}>
            <span className="chart-bar-label">{i + 1}</span>
            <div
              className="chart-bar-fill"
              style={{ width: `${(c / maxCount) * 100}%` }}
            />
            <span className="chart-bar-count">{c}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
