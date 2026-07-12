import { memo } from "react";

interface NumberBallProps {
  n: number;
  small?: boolean;
  matched?: boolean;
}

const NumberBall = memo(({ n, small, matched }: NumberBallProps) => {
  const hue = (n * 10) % 360;
  return (
    <span
      className={`ball${small ? " ball-small" : ""}${matched ? " matched" : ""}`}
      style={{
        background: `linear-gradient(135deg, hsl(${hue}, 70%, 50%), hsl(${hue + 40}, 70%, 55%))`,
      }}
    >
      {n}
    </span>
  );
});

export default NumberBall;
