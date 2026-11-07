import { useEffect, useState } from "react";
import { api } from "./api";
import type { Champion, ScoreResponse } from "./api";
import "./App.css";

export default function App() {
  const [health, setHealth] = useState<string>("…");
  const [champion, setChampion] = useState<Champion | null>(null);
  const [champError, setChampError] = useState<string | null>(null);
  const [form, setForm] = useState({
    person_id: "ui-demo-1",
    income: 55000,
    age: 35,
    utilisation: 0.35,
  });
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .health()
      .then((h) => setHealth(`${h.status} · v${h.version}`))
      .catch((e) => setHealth(`down (${e.message})`));
    api
      .champion()
      .then(setChampion)
      .catch((e) => setChampError(e.message));
  }, []);

  async function onScore(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api.score(form);
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="layout">
      <header>
        <h1>Nexus Decision Platform</h1>
        <p className="muted">Governed credit decisioning · API: {health}</p>
      </header>

      <section className="card">
        <h2>Champion</h2>
        {champError && <p className="error">{champError}</p>}
        {champion && (
          <div>
            <p>
              <strong>{champion.model_version}</strong>
            </p>
            <ul>
              {Object.entries(champion.metrics).map(([k, v]) => (
                <li key={k}>
                  {k}: {typeof v === "number" ? v.toFixed(4) : String(v)}
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="card">
        <h2>Score application</h2>
        <form onSubmit={onScore} className="form">
          <label>
            Person ID
            <input
              value={form.person_id}
              onChange={(e) => setForm({ ...form, person_id: e.target.value })}
            />
          </label>
          <label>
            Income
            <input
              type="number"
              value={form.income}
              onChange={(e) =>
                setForm({ ...form, income: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Age
            <input
              type="number"
              value={form.age}
              onChange={(e) =>
                setForm({ ...form, age: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Utilisation (0–1)
            <input
              type="number"
              step="0.01"
              min={0}
              max={1}
              value={form.utilisation}
              onChange={(e) =>
                setForm({ ...form, utilisation: Number(e.target.value) })
              }
            />
          </label>
          <button type="submit" disabled={busy}>
            {busy ? "Scoring…" : "Score"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
        {result && (
          <div className="result">
            <p>
              Outcome: <strong>{result.outcome}</strong> · Score{" "}
              {result.score.toFixed(1)} · PD {result.probability.toFixed(4)}
            </p>
            <p>Decision ID: {result.decision_id}</p>
            <p>Reasons: {result.reason_codes.join(", ")}</p>
          </div>
        )}
      </section>
    </div>
  );
}