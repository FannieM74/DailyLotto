"use client";

const GAMES = [
  { key: "daily_lotto", label: "Daily Lotto" },
  { key: "lotto", label: "Lotto" },
  { key: "lotto_plus", label: "Lotto Plus" },
  { key: "powerball", label: "PowerBall" },
  { key: "powerball_xtra", label: "PowerBall XTRA" },
];

export default function GameSelector({ value, onChange }: { value: string; onChange: (game: string) => void }) {
  return (
    <div className="game-selector">
      <label>Game:</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {GAMES.map((g) => (
          <option key={g.key} value={g.key}>{g.label}</option>
        ))}
      </select>
    </div>
  );
}
