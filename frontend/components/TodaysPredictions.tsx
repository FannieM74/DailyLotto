import { useGame } from "@/context/GameContext";
import NumberBall from "@/components/NumberBall";
import { METHOD_NAMES } from "@/lib/constants";

interface TodaysPredictionsProps {
  todaysPicks: Record<string, number[]>;
  method: string;
}

export default function TodaysPredictions({ todaysPicks, method }: TodaysPredictionsProps) {
  if (Object.keys(todaysPicks).length === 0) {
    return null;
  }

  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <h3 style={{ margin: "0 0 0.5rem" }}>Today's Predictions</h3>
      {(Object.entries(todaysPicks) as [string, number[]][]).map(([methodKey, picks]) => (
        <div key={methodKey} style={{
          display: "flex", alignItems: "center", gap: "0.75rem",
          marginBottom: "0.4rem", fontSize: "0.85rem"
        }}>
          <span style={{ textTransform: "capitalize", fontWeight: 600, minWidth: "5rem" }}>
            {METHOD_NAMES[methodKey] || methodKey}
          </span>
          {picks.map((n, i) => (
            <NumberBall key={i} n={n} small={method !== "all"} />
          ))}
        </div>
      ))}
    </div>
  );
}
