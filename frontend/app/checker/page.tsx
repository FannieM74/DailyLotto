"use client";
import { useState } from "react";
import { checkTicket } from "@/lib/api";
import NumberBall from "@/components/NumberBall";

export default function CheckerPage() {
  const [nums, setNums] = useState<number[]>([1, 2, 3, 4, 5]);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleNumChange = (i: number, val: string) => {
    const n = parseInt(val) || 0;
    const next = [...nums];
    next[i] = Math.min(36, Math.max(1, n));
    setNums(next);
  };

  const handleCheck = async () => {
    if (new Set(nums).size !== 5) {
      setError("All 5 numbers must be unique");
      return;
    }
    setError("");
    setLoading(true);
    const res = await checkTicket(nums[0], nums[1], nums[2], nums[3], nums[4]);
    setLoading(false);
    if (res.error) {
      setError(res.error);
      return;
    }
    setResults(res);
  };

  return (
    <div>
      <h1>Ticket Checker</h1>
      <p style={{ color: "var(--text2)", marginBottom: "1rem" }}>
        Enter your 5 numbers to check against historical draws
      </p>

      <div className="card">
        <h2>Your Numbers</h2>
        <div className="checker-inputs">
          {nums.map((n, i) => (
            <input
              key={i}
              type="number"
              min={1}
              max={36}
              value={n}
              onChange={(e) => handleNumChange(i, e.target.value)}
              className="checker-input"
            />
          ))}
        </div>
        <button className="btn btn-block" onClick={handleCheck} disabled={loading} style={{ marginTop: "0.75rem" }}>
          {loading ? "Checking..." : "Check Ticket"}
        </button>
        {error && <p style={{ color: "var(--red)", fontSize: "0.9rem", marginTop: "0.5rem" }}>{error}</p>}
      </div>

      {results && (
        <>
          <div className="card">
            <h2>Your Numbers</h2>
            <div className="balls">
              {nums.map((n, i) => (
                <NumberBall key={i} n={n} />
              ))}
            </div>
            <p style={{ color: "var(--text2)", marginTop: "0.5rem" }}>
              Checked against {results.total_checked} recent draws
            </p>
          </div>

          {results.results && results.results.length > 0 ? (
            <div className="card">
              <h2>Matching Draws</h2>
              <div className="table-wrap">
                <table className="compact">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Draw Numbers</th>
                      <th className="hide-mobile">Matches</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.results.map((r: any, i: number) => (
                      <tr key={i}>
                        <td>{r.date}</td>
                        <td>
                          <div className="balls" style={{ gap: "0.3rem" }}>
                            {r.draw_numbers.map((n: number, j: number) => (
                              <NumberBall key={j} n={n} />
                            ))}
                          </div>
                        </td>
                        <td className="hide-mobile">
                          <span className={`match-badge match-${r.matches}`}>
                            {r.matches} match{r.matches > 1 ? "es" : ""}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="card">
              <p style={{ color: "var(--text2)", textAlign: "center" }}>
                No matching draws found. Your numbers have never won.
              </p>
            </div>
          )}
        </>
      )}

      <style>{`
        .checker-inputs {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }
        .checker-input {
          width: 64px;
          text-align: center;
          flex: 1;
          min-width: 50px;
          max-width: 70px;
        }
        @media (max-width: 480px) {
          .checker-inputs { gap: 0.35rem; }
          .checker-input { min-width: 44px; max-width: 60px; }
        }
      `}</style>
    </div>
  );
}
