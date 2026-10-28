"""Tests for monitoring / drift checks."""

import numpy as np

from nexus.domain.monitoring import monitor_scores


def test_no_drift():
    rng = np.random.default_rng(0)
    base = rng.normal(600, 40, 500)
    live = rng.normal(600, 40, 500)
    report = monitor_scores(
        baseline_scores=base,
        live_scores=live,
        psi_threshold=0.25,
    )
    assert report.psi_score < 0.25
    assert report.alerts == ()


def test_psi_alert():
    rng = np.random.default_rng(1)
    base = rng.normal(600, 20, 400)
    live = rng.normal(700, 20, 400)  # shifted
    report = monitor_scores(
        baseline_scores=base,
        live_scores=live,
        psi_threshold=0.1,
    )
    assert report.psi_score > 0.1
    assert any("PSI" in a for a in report.alerts)