"use client";

export default function NumberBall({ n, small }: { n: number; small?: boolean }) {
  const hue = (n * 10) % 360;
  return (
    <span
      className={`ball${small ? " ball-small" : ""}`}
      style={{
        background: `linear-gradient(135deg, hsl(${hue}, 70%, 50%), hsl(${hue + 40}, 70%, 55%))`,
      }}
    >
      {n}
    </span>
  );
}
