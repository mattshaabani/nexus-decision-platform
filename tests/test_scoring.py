"""Tests for application scoring use case."""

import numpy as np
import pandas as pd

from nexus.application.scoring import score_application
from nexus.domain.models import DecisionOutcome
from nexus.domain.scorecard import fit_scorecard


def test_score_application_returns_decision():
    rng = np.random.default_rng(0)
    n = 300
    df = pd.DataFrame(
        {
            "income": rng.normal(50_000, 10_000, n),
            "age": rng.integers(25, 60, n),
            "utilisation": rng.uniform(0, 1, n),
            "default": rng.integers(0, 2, n),
        }
    )
    sc = fit_scorecard(
        df, target="default", features=["income", "age", "utilisation"], min_bin_size=20
    )
    d = score_application(
        sc,
        {"income": 45_000, "age": 35, "utilisation": 0.4},
        person_id="p-1",
        model_version="test-v1",
    )
    assert d.person_id == "p-1"
    assert d.outcome in {DecisionOutcome.APPROVE, DecisionOutcome.DECLINE}
    assert len(d.reason_codes) <= 3
    assert d.score > 0