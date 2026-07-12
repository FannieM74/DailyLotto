export const METHOD_COLORS: Record<string, string> = {
  frequency: "var(--accent)",
  markov: "#f59e0b",
  lstm: "var(--accent2)",
  pair_freq: "#10b981",
  delta: "#8b5cf6",
  ensemble: "#f97316",
  weighted_freq: "#06b6d4",
  hot_cold: "#ec4899",
};

export const METHOD_LABELS: Record<string, string> = {
  frequency: "F",
  markov: "M",
  lstm: "AI",
  pair_freq: "PF",
  delta: "D",
  ensemble: "E",
  weighted_freq: "W",
  hot_cold: "HC",
};

export const METHOD_ORDER: string[] = [
  "frequency",
  "weighted_freq",
  "pair_freq",
  "delta",
  "ensemble",
  "hot_cold",
  "markov",
  "lstm",
];

export const METHOD_NAMES: Record<string, string> = {
  pair_freq: "Pair Freq",
  delta: "Delta",
  ensemble: "Ensemble",
  weighted_freq: "Weighted",
  hot_cold: "Hot/Cold",
  lstm: "AI",
  frequency: "Frequency",
  markov: "Markov",
};
