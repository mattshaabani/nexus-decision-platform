import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { api } from "./api";
import type { Champion, ExplainResponse, FPAResponse, ScoreResponse } from "./api";
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

  const [lookupId, setLookupId] = useState("");
  const [lookup, setLookup] = useState<Record<string, unknown> | null>(null);
  const [lookupError, setLookupError] = useState<string | null>(null);

  const [explainText, setExplainText] = useState<ExplainResponse | null>(null);
  const [explainError, setExplainError] = useState<string | null>(null);
  const [explainBusy, setExplainBusy] = useState(false);

  const [fpaForm, setFpaForm] = useState({
    metric_name: "default_rate",
    actual: 0.042,
    plan: 0.035,
    period: "2026-Q3",
  });
  const [fpaResult, setFpaResult] = useState<FPAResponse | null>(null);
  const [fpaError, setFpaError] = useState<string | null>(null);
  const [fpaBusy, setFpaBusy] = useState(false);

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
      setLookupId(r.decision_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const championCard = (
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
                <strong>{k}</strong>:{" "}
                {typeof v === "number" ? v.toFixed(4) : String(v)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );

  const decisioning = (
    <>
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
              onChange={(e) => setForm({ ...form, age: Number(e.target.value) })}
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

      <section className="card">
        <h2>Lookup decision</h2>
        <form
          className="form"
          onSubmit={async (e) => {
            e.preventDefault();
            setLookupError(null);
            setLookup(null);
            try {
              const d = await api.decision(lookupId.trim());
              setLookup(d);
            } catch (err) {
              setLookupError(err instanceof Error ? err.message : String(err));
            }
          }}
        >
          <label>
            Decision ID
            <input
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              placeholder="paste decision_id from score result"
            />
          </label>
          <button type="submit">Lookup</button>
        </form>
        {lookupError && <p className="error">{lookupError}</p>}
        {lookup && (
          <pre
            className="result"
            style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem" }}
          >
            {JSON.stringify(lookup, null, 2)}
          </pre>
        )}
      </section>

      <section className="card">
        <h2>Support explain</h2>
        <p className="muted">
          Uses decision id from lookup / score. Never changes the outcome.
        </p>
        <button
          type="button"
          disabled={explainBusy || !lookupId.trim()}
          onClick={async () => {
            setExplainBusy(true);
            setExplainError(null);
            setExplainText(null);
            try {
              const r = await api.explain(
                lookupId.trim(),
                "Why was this decision made?"
              );
              setExplainText(r);
            } catch (err) {
              setExplainError(err instanceof Error ? err.message : String(err));
            } finally {
              setExplainBusy(false);
            }
          }}
        >
          {explainBusy ? "Explaining…" : "Explain decision"}
        </button>
        {explainError && <p className="error">{explainError}</p>}
        {explainText && (
          <div className="result">
            <p>{explainText.explanation}</p>
            <p className="muted">
              grounding={explainText.grounding} · model={explainText.model} ·
              cached={String(explainText.cached)}
            </p>
            {explainText.citations && explainText.citations.length > 0 && (
              <ul>
                {explainText.citations.map((c) => (
                  <li key={c.chunk_id}>
                    {c.title} ({c.chunk_id}) · score {c.score.toFixed(2)}
                  </li>
                ))}
              </ul>
            )}
            <section className="card">
        <h2>FP&A investigate</h2>
        <p className="muted">Narrative only — does not book forecasts or change decisions.</p>
        <form
          className="form"
          onSubmit={async (e) => {
            e.preventDefault();
            setFpaBusy(true);
            setFpaError(null);
            setFpaResult(null);
            try {
              const r = await api.fpaInvestigate(fpaForm);
              setFpaResult(r);
            } catch (err) {
              setFpaError(err instanceof Error ? err.message : String(err));
            } finally {
              setFpaBusy(false);
            }
          }}
        >
          <label>
            Metric
            <input
              value={fpaForm.metric_name}
              onChange={(e) =>
                setFpaForm({ ...fpaForm, metric_name: e.target.value })
              }
            />
          </label>
          <label>
            Actual
            <input
              type="number"
              step="0.001"
              value={fpaForm.actual}
              onChange={(e) =>
                setFpaForm({ ...fpaForm, actual: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Plan
            <input
              type="number"
              step="0.001"
              value={fpaForm.plan}
              onChange={(e) =>
                setFpaForm({ ...fpaForm, plan: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Period
            <input
              value={fpaForm.period}
              onChange={(e) =>
                setFpaForm({ ...fpaForm, period: e.target.value })
              }
            />
          </label>
          <button type="submit" disabled={fpaBusy}>
            {fpaBusy ? "Investigating…" : "Investigate"}
          </button>
        </form>
        {fpaError && <p className="error">{fpaError}</p>}
        {fpaResult && (
          <div className="result">
            <p>{fpaResult.summary}</p>
            <p className="muted">
              {fpaResult.grounding} · {fpaResult.model}
            </p>
          </div>
        )}
      </section>
          </div>
        )}
      </section>
    </>
  );

  return (
    <div className="layout">
      <header>
        <h1>Nexus Decision Platform</h1>
        <p className="muted">Governed credit decisioning · API: {health}</p>
        <nav className="nav">
          <Link to="/">Decisioning</Link>
          <Link to="/champion">Champion</Link>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={decisioning} />
        <Route path="/champion" element={championCard} />
      </Routes>
    </div>
  );
}