"""Score a single application and optionally audit it."""

from __future__ import annotations

import uuid
from typing import Any

import pandas as pd

from nexus.domain.models import Decision, DecisionOutcome
from nexus.domain.ports import DecisionStorePort
from nexus.domain.scorecard.scorecard import Scorecard


def score_application(
    scorecard: Scorecard,
    features: dict[str, float],
    *,
    person_id: str,
    model_version: str,
    approve_threshold: float = 0.5,
    store: DecisionStorePort | None = None,
) -> Decision:
    """Score one application; optionally persist to audit store."""
    row = pd.Series(features)
    result = scorecard.score_one(row)
    outcome = (
        DecisionOutcome.APPROVE
        if result.probability < approve_threshold
        else DecisionOutcome.DECLINE
    )
    decision = Decision(
        decision_id=str(uuid.uuid4()),
        person_id=person_id,
        model_version=model_version,
        score=result.score,
        probability=result.probability,
        outcome=outcome,
        reason_codes=list(result.reason_codes),
        features=dict(features),
    )
    if store is not None:
        store.save(decision)
    return decision