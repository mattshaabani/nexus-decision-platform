"""Score a single application and optionally audit it."""

from __future__ import annotations

import uuid

import pandas as pd

from nexus.adapters.config_loader import load_policy_config
from nexus.domain.models import Decision
from nexus.domain.policy import PolicyConfig, apply_policy
from nexus.domain.ports import DecisionStorePort
from nexus.domain.scorecard.scorecard import Scorecard


def score_application(
    scorecard: Scorecard,
    features: dict[str, float],
    *,
    person_id: str,
    model_version: str,
    ead: float = 10_000.0,
    policy: PolicyConfig | None = None,
    policy_version: str | None = None,
    store: DecisionStorePort | None = None,
) -> Decision:
    row = pd.Series(features)
    result = scorecard.score_one(row)

    version = policy_version
    if policy is None:
        cfg = load_policy_config()
        policy = PolicyConfig(
            approve_max_pd=float(cfg["approve_max_pd"]),
            refer_max_pd=float(cfg["refer_max_pd"]),
            default_lgd=float(cfg["default_lgd"]),
        )
        version = str(cfg["policy_version"])

    pol = apply_policy(
        result.probability,
        ead=ead,
        config=policy,
        policy_version=version,
    )
    decision = Decision(
        decision_id=str(uuid.uuid4()),
        person_id=person_id,
        model_version=model_version,
        score=result.score,
        probability=result.probability,
        outcome=pol.outcome,
        reason_codes=list(result.reason_codes),
        features=dict(features),
        lgd=pol.lgd,
        ead=pol.ead,
        expected_loss=pol.expected_loss,
        policy_version=pol.policy_version,
    )
    if store is not None:
        store.save(decision)
    return decision