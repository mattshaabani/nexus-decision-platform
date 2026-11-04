"""FastAPI entrypoint — health + score."""

from __future__ import annotations

import pickle
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from nexus import __version__
from nexus.adapters.sqlite_decision_store import SqliteDecisionStore
from nexus.application.scoring import score_application
from nexus.domain.scorecard.scorecard import Scorecard
from nexus.adapters.champion_store import ChampionStore
from nexus.adapters.llm_echo import EchoLLM, InMemoryCache
from nexus.domain.llm_gateway import LLMMessage, LLMRequest

app = FastAPI(
    title="Nexus Decision Platform",
    description="Governed Decision Intelligence for regulated financial decisions",
    version=__version__,
)

SCORECARD_PATH = Path("artifacts/scorecard_scorecard-v0.1.0.pkl")
MODEL_VERSION = "scorecard-v0.1.0"
_store = SqliteDecisionStore("artifacts/decisions.db")
_llm_cache = InMemoryCache()
_llm = EchoLLM(_llm_cache)
_champion_store = ChampionStore("artifacts/champion.json")
_scorecard: Scorecard | None = None


def _load_scorecard() -> Scorecard:
    global _scorecard
    if _scorecard is not None:
        return _scorecard
    if not SCORECARD_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Scorecard not found at {SCORECARD_PATH}. Run the experiment first.",
        )
    with open(SCORECARD_PATH, "rb") as f:
        _scorecard = pickle.load(f)
    return _scorecard


class ScoreRequest(BaseModel):
    person_id: str
    income: float
    age: float
    utilisation: float = Field(..., ge=0, le=1)


class ScoreResponse(BaseModel):
    decision_id: str
    person_id: str
    model_version: str
    score: float
    probability: float
    outcome: str
    reason_codes: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/champion")
def get_champion() -> dict:
    data = _champion_store.get()
    if data is None:
        raise HTTPException(status_code=404, detail="No champion registered yet")
    return data


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "nexus-decision-platform",
        "version": __version__,
        "docs": "/docs",
    }


@app.get("/decisions/{decision_id}")
def get_decision(decision_id: str) -> dict:
    decision = _store.get(decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {
        "decision_id": decision.decision_id,
        "person_id": decision.person_id,
        "model_version": decision.model_version,
        "score": decision.score,
        "probability": decision.probability,
        "outcome": decision.outcome.value,
        "reason_codes": list(decision.reason_codes),
        "features": decision.features,
        "override": decision.override,
        "created_at": decision.created_at.isoformat(),
    }


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest) -> ScoreResponse:
    sc = _load_scorecard()
    decision = score_application(
        sc,
        {
            "income": req.income,
            "age": req.age,
            "utilisation": req.utilisation,
        },
        person_id=req.person_id,
        model_version=MODEL_VERSION,
        store=_store,
    )
    return ScoreResponse(
        decision_id=decision.decision_id,
        person_id=decision.person_id,
        model_version=decision.model_version,
        score=decision.score,
        probability=decision.probability,
        outcome=decision.outcome.value,
        reason_codes=list(decision.reason_codes),
    )


class ExplainRequest(BaseModel):
    decision_id: str
    question: str = "Why was this decision made?"


@app.post("/support/explain")
def support_explain(req: ExplainRequest) -> dict:
    """Subordinate explanation — never changes the decision outcome."""
    decision = _store.get(req.decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")

    context = (
        f"decision_id={decision.decision_id} outcome={decision.outcome.value} "
        f"score={decision.score:.1f} probability={decision.probability:.4f} "
        f"reason_codes={list(decision.reason_codes)} features={decision.features}"
    )
    llm_req = LLMRequest(
        messages=(
            LLMMessage(
                role="system",
                content=(
                    "You are a support assistant. You explain existing credit decisions. "
                    "You must not approve, decline, or change any decision."
                ),
            ),
            LLMMessage(
                role="user",
                content=f"{req.question}\n\nDecision context:\n{context}",
            ),
        ),
        model_hint="cheap",
    )
    resp = _llm.complete(llm_req)
    return {
        "decision_id": decision.decision_id,
        "outcome": decision.outcome.value,
        "explanation": resp.content,
        "model": resp.model,
        "cached": resp.cached,
        "cost_usd": resp.cost_usd,
        "grounding": "echo-adapter-v1",
    }