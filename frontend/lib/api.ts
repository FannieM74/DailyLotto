const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch(path: string, options?: RequestInit) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const res = await fetch(`${API}${path}`, {
      ...options,
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeout);
    return res.json();
  } catch {
    clearTimeout(timeout);
    return { error: "Network error or timeout" };
  }
}

export function getGames() {
  return apiFetch("/games");
}

export function getLatestDraw(game = "daily_lotto") {
  return apiFetch(`/draws/latest?game=${game}`);
}

export function getRecentDraws(days = 7, game = "daily_lotto") {
  return apiFetch(`/draws/recent?days=${days}&game=${game}`);
}

export function getFrequencyPrediction(game = "daily_lotto") {
  return apiFetch(`/predict/frequency?game=${game}`);
}

export function getMarkovPrediction(game = "daily_lotto") {
  return apiFetch(`/predict/markov?game=${game}`);
}

export function getLstmPrediction(game = "daily_lotto") {
  return apiFetch(`/predict/lstm?game=${game}`);
}

export function getPairFreqPrediction(game = "daily_lotto") {
  return apiFetch(`/predict/pair-freq?game=${game}`);
}

export function getDeltaPrediction(game = "daily_lotto") {
  return apiFetch(`/predict/delta?game=${game}`);
}

export function getEnsemblePrediction(game = "daily_lotto") {
  return apiFetch(`/predict/ensemble?game=${game}`);
}

export function getWeightedFreqPrediction(game = "daily_lotto") {
  return apiFetch(`/predict/weighted-freq?game=${game}`);
}

export function getHotColdPrediction(game = "daily_lotto") {
  return apiFetch(`/predict/hot-cold?game=${game}`);
}

export function checkTicket(n1: number, n2: number, n3: number, n4: number, n5: number, game = "daily_lotto") {
  return apiFetch("/checker", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ n1, n2, n3, n4, n5, game }),
  });
}

export function getTracker(game = "daily_lotto") {
  return apiFetch(`/tracker?game=${game}`);
}

export function getWinRates(game = "daily_lotto") {
  return apiFetch(`/tracker/win-rates?game=${game}`);
}

export function getTodayPredictions(game = "daily_lotto") {
  return apiFetch(`/predict/today?game=${game}`);
}

export function getLatestResults(game = "daily_lotto") {
  return apiFetch(`/results/latest?game=${game}`);
}

export function getRecentMatches(game = "daily_lotto") {
  return apiFetch(`/tracker/recent-matches?game=${game}`);
}
