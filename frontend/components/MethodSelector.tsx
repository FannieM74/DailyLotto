import { memo, useState, useEffect, useRef } from "react";
import { getRecentMatches } from "@/lib/api";
import { useGame } from "@/context/GameContext";

const METHODS: { key: string; label: string }[] = [
  { key: "all", label: "All Methods" },
  { key: "frequency", label: "Frequency" },
  { key: "weighted_freq", label: "Weighted" },
  { key: "pair_freq", label: "Pair Freq" },
  { key: "delta", label: "Delta" },
  { key: "ensemble", label: "Ensemble" },
  { key: "hot_cold", label: "Hot/Cold" },
  { key: "markov", label: "Markov" },
  { key: "lstm", label: "AI" },
];

function matchBadgeClass(n: number) {
  if (n >= 2) return "match-3";
  if (n === 1) return "match-1";
  return "match-0";
}

interface MethodSelectorTriggerProps {
  value: string;
  onToggle: () => void;
  recentMatches: Record<string, number[]>;
  open: boolean;
}

const MethodSelectorTrigger = memo(({ value, onToggle, recentMatches, open }: MethodSelectorTriggerProps) => {
  const selected = METHODS.find((m) => m.key === value);
  const selectedLabel = selected?.label || value;

  return (
    <div className="method-trigger" onClick={onToggle}>
      <span className="method-trigger-label">{selectedLabel}</span>
      {value !== "all" && recentMatches[value]?.length === 3 && (
        <span className="method-trigger-matches">
          {recentMatches[value].map((n, i) => (
            <span key={i} className={`match-badge ${matchBadgeClass(n)}`} style={{ marginLeft: 2 }}>
              {n}
            </span>
          ))}
        </span>
      )}
      <span className="method-arrow">{open ? "▲" : "▼"}</span>
    </div>
  );
});

interface MethodOptionProps {
  method: { key: string; label: string };
  isSelected: boolean;
  recentMatches: Record<string, number[]>;
  onSelect: (key: string) => void;
}

const MethodOption = memo(({ method, isSelected, recentMatches, onSelect }: MethodOptionProps) => {
  const counts = recentMatches[method.key];

  return (
    <div
      key={method.key}
      className={`method-option${isSelected ? " selected" : ""}`}
      onClick={() => {
        onSelect(method.key);
      }}
    >
      <span className="method-option-label">{method.label}</span>
      {method.key !== "all" && counts?.length === 3 && (
        <span className="method-option-matches">
          {counts.map((n, i) => (
            <span key={i} className={`match-badge ${matchBadgeClass(n)}`}>
              {n}
            </span>
          ))}
        </span>
      )}
    </div>
  );
});

export default function MethodSelector({ value, onChange }: { value: string; onChange: (m: string) => void }) {
  const { game } = useGame();
  const [open, setOpen] = useState(false);
  const [recent, setRecent] = useState<Record<string, number[]>>({});
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getRecentMatches(game).then((d) => {
      if (!d.error) setRecent(d);
    });
  }, [game]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleToggle = () => setOpen((prev) => !prev);
  const handleSelect = (key: string) => {
    onChange(key);
    setOpen(false);
  };

  return (
    <div className="method-selector" ref={ref}>
      <label>Method:</label>
      <MethodSelectorTrigger
        value={value}
        onToggle={handleToggle}
        recentMatches={recent}
        open={open}
      />
      {open && (
        <div className="method-dropdown">
          {METHODS.map((m) => (
            <MethodOption
              key={m.key}
              method={m}
              isSelected=m.key === value
              recentMatches={recent}
              onSelect={handleSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
