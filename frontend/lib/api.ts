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

export function getLatestDraw() {
  return apiFetch("/draws/latest");
}

export function getRecentDraws(days = 7) {
  return apiFetch(`/draws/recent?days=${days}`);
}

export function getFrequencyPrediction() {
  return apiFetch("/predict/frequency");
}

export function getMarkovPrediction() {
  return apiFetch("/predict/markov");
}

export function getLstmPrediction() {
  return apiFetch("/predict/lstm");
}

export function checkTicket(n1: number, n2: number, n3: number, n4: number, n5: number) {
  return apiFetch("/checker", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ n1, n2, n3, n4, n5 }),
  });
}

export function getTracker() {
  return apiFetch("/tracker");
}

export function getWinRates() {
  return apiFetch("/tracker/win-rates");
}
