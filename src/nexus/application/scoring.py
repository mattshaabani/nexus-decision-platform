"""Score a single application and optionally audit it."""

from __future__ import annotations

import uuid

import pandas as pd

from nexus.domain.models import Decision, DecisionOutcome
from nexus.domain.ports import DecisionStorePort
from nexus.domain.scorecard.scorecard import Scorecard
from nexus.domain.policy import PolicyConfig, apply_policy


def score_application(
    scorecard: Scorecard,
    features: dict[str, float],
    *,
    person_id: str,
    model_version: str,
    ead: float = 10_000.0,
    policy: PolicyConfig | None = None,
    store: DecisionStorePort | None = None,
) -> Decision:
    row = pd.Series(features)
    result = scorecard.score_one(row)
    pol = apply_policy(result.probability, ead=ead, config=policy)
    decision = Decision(
        decision_id=str(uuid.uuid4()),
        person_id=person_id,
        model_version=model_version,
        score=result.score,
        probability=result.probability,
        outcome=pol.outcome,
        reason_codes=list(result.reason_codes),
        features=dict(features),
    )
    if store is not None:
        store.save(decision)
    return decision