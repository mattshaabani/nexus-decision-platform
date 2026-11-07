const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export type ScoreResponse = {
  decision_id: string;
  person_id: string;
  model_version: string;
  score: number;
  probability: number;
  outcome: string;
  reason_codes: string[];
};

export type Champion = {
  model_version: string;
  metrics: Record<string, number>;
  extra?: Record<string, unknown>;
};

export const api = {
  health: () => request<{ status: string; version: string }>("/health"),
  champion: () => request<Champion>("/champion"),
  score: (body: {
    person_id: string;
    income: number;
    age: number;
    utilisation: number;
  }) =>
    request<ScoreResponse>("/score", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  decision: (id: string) =>
    request<Record<string, unknown>>(`/decisions/${id}`),
};