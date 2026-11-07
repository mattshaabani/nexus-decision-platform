"""FastAPI entrypoint — health + score."""

from __future__ import annotations

import pickle
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from nexus import __version__
from nexus.adapters.champion_store import ChampionStore
from nexus.adapters.llm_echo import InMemoryCache, build_default_llm
from nexus.adapters.policy_retriever import MarkdownPolicyRetriever
from nexus.adapters.sqlite_agent_audit import SqliteAgentAuditStore
from nexus.adapters.sqlite_decision_store import SqliteDecisionStore
from nexus.application.scoring import score_application
from nexus.domain.llm_gateway import LLMMessage, LLMRequest
from nexus.domain.scorecard.scorecard import Scorecard
from nexus.application.fpa_investigate import investigate_variance
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Nexus Decision Platform",
    description="Governed Decision Intelligence for regulated financial decisions",
    version=__version__,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCORECARD_PATH = Path("artifacts/scorecard_scorecard-v0.1.0.pkl")
MODEL_VERSION = "scorecard-v0.1.0"
_store = SqliteDecisionStore("artifacts/decisions.db")
_llm_cache = InMemoryCache()
_llm = build_default_llm(_llm_cache)
_agent_audit = SqliteAgentAuditStore("artifacts/agent_audit.db")
_retriever = MarkdownPolicyRetriever("data/policy")
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


class FPARequest(BaseModel):
    metric_name: str
    actual: float
    plan: float
    period: str = "current"


@app.post("/support/fpa-investigate")
def fpa_investigate(req: FPARequest) -> dict:
    result = investigate_variance(
        metric_name=req.metric_name,
        actual=req.actual,
        plan=req.plan,
        period=req.period,
        llm=_llm,
        retriever=_retriever,
    )
    return {
        "summary": result.summary,
        "citations": result.citations,
        "model": result.model,
        "cached": result.cached,
        "cost_usd": result.cost_usd,
        "grounding": "fpa-narrative-only",
    }


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
    hits = _retriever.retrieve(
        f"{req.question} {' '.join(decision.reason_codes)}",
        top_k=3,
    )
    policy_block = "\n\n".join(
        f"[{h.chunk.chunk_id}] {h.chunk.title}: {h.chunk.text[:400]}"
        for h in hits
    ) or "(no policy chunks retrieved)"

    llm_req = LLMRequest(
        messages=(
            LLMMessage(
                role="system",
                content=(
                    "You are a support assistant. Explain existing credit decisions "
                    "using only the provided decision context and policy chunks. "
                    "You must not approve, decline, or change any decision. "
                    "Cite chunk ids when you use policy text."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"{req.question}\n\nDecision context:\n{context}\n\n"
                    f"Policy chunks:\n{policy_block}"
                ),
            ),
        ),
        model_hint="cheap",
    )
    resp = _llm.complete(llm_req)

    prompt_text = f"{req.question}\n{context}\n{policy_block}"
    _agent_audit.log_turn(
        turn_id=str(uuid.uuid4()),
        decision_id=decision.decision_id,
        endpoint="/support/explain",
        prompt_text=prompt_text,
        tools=["get_decision", "policy_retrieve", "llm_complete"],
        citations=[
            {
                "chunk_id": h.chunk.chunk_id,
                "title": h.chunk.title,
                "source": h.chunk.source,
                "score": h.score,
            }
            for h in hits
        ],
        model=resp.model,
        cached=resp.cached,
        cost_usd=resp.cost_usd,
        latency_ms=resp.latency_ms,
    )

    return {
        "decision_id": decision.decision_id,
        "outcome": decision.outcome.value,
        "explanation": resp.content,
        "citations": [
            {
                "chunk_id": h.chunk.chunk_id,
                "title": h.chunk.title,
                "source": h.chunk.source,
                "score": h.score,
            }
            for h in hits
        ],
        "model": resp.model,
        "cached": resp.cached,
        "cost_usd": resp.cost_usd,
        "grounding": "policy-rag+echo-v1",
    }