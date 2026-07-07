"use client";

export default function NumberBall({ n }: { n: number }) {
  const hue = (n * 10) % 360;
  return (
    <span
      className="ball"
      style={{
        background: `linear-gradient(135deg, hsl(${hue}, 70%, 50%), hsl(${hue + 40}, 70%, 55%))`,
      }}
    >
      {n}
    </span>
  );
}
