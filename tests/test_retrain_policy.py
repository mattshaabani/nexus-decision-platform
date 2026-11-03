"""Tests for retrain trigger policy."""

import numpy as np

from nexus.domain.monitoring import monitor_scores
from nexus.domain.retrain_policy import evaluate_retrain_triggers


def test_no_retrain_when_stable():
    rng = np.random.default_rng(0)
    base = rng.normal(600, 40, 400)
    live = rng.normal(600, 40, 400)
    report = monitor_scores(baseline_scores=base, live_scores=live, psi_threshold=0.25)
    decision = evaluate_retrain_triggers(report, psi_trigger=0.25)
    assert decision.should_retrain is False
    assert decision.reasons == ()


def test_retrain_on_high_psi():
    rng = np.random.default_rng(1)
    base = rng.normal(600, 20, 400)
    live = rng.normal(720, 20, 400)
    report = monitor_scores(baseline_scores=base, live_scores=live, psi_threshold=0.05)
    decision = evaluate_retrain_triggers(report, psi_trigger=0.05)
    assert decision.should_retrain is True
    assert any("PSI" in r for r in decision.reasons)