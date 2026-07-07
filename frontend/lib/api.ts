const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getLatestDraw() {
  const res = await fetch(`${API}/draws/latest`, { cache: "no-store" });
  return res.json();
}

export async function getRecentDraws(days = 7) {
  const res = await fetch(`${API}/draws/recent?days=${days}`, { cache: "no-store" });
  return res.json();
}

export async function getFrequencyPrediction() {
  const res = await fetch(`${API}/predict/frequency`, { cache: "no-store" });
  return res.json();
}

export async function getMarkovPrediction() {
  const res = await fetch(`${API}/predict/markov`, { cache: "no-store" });
  return res.json();
}

export async function getLstmPrediction() {
  const res = await fetch(`${API}/predict/lstm`, { cache: "no-store" });
  return res.json();
}

export async function checkTicket(n1: number, n2: number, n3: number, n4: number, n5: number) {
  const res = await fetch(`${API}/checker`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ n1, n2, n3, n4, n5 }),
  });
  return res.json();
}

export async function getTracker() {
  const res = await fetch(`${API}/tracker`, { cache: "no-store" });
  return res.json();
}

export async function getWinRates() {
  const res = await fetch(`${API}/tracker/win-rates`, { cache: "no-store" });
  return res.json();
}
