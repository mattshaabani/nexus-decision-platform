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

app = FastAPI(
    title="Nexus Decision Platform",
    description="Governed Decision Intelligence for regulated financial decisions",
    version=__version__,
)

SCORECARD_PATH = Path("artifacts/scorecard_scorecard-v0.1.0.pkl")
MODEL_VERSION = "scorecard-v0.1.0"
_store = SqliteDecisionStore("artifacts/decisions.db")
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


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "nexus-decision-platform",
        "version": __version__,
        "docs": "/docs",
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