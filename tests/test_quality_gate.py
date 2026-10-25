"""Unit tests for pure quality-gate rules."""

from nexus.domain.models import GateStatus
from nexus.domain.quality_gate import evaluate_gate


def test_first_model_passes_with_good_metrics():
    metrics = {
        "gini": 0.42,
        "brier": 0.15,
        "psi": 0.05,
        "four_fifths_ratio": 0.92,
        "eo_gap": 0.01,
    }
    result = evaluate_gate("v0.1", metrics, is_first_model=True)
    assert result.status == GateStatus.PASS
    assert not result.blockers


def test_gini_floor_blocks():
    metrics = {"gini": 0.20, "brier": 0.15}
    result = evaluate_gate("v0.1", metrics, is_first_model=True)
    assert result.status == GateStatus.FAIL
    assert any("Gini" in b for b in result.blockers)


def test_uplift_required_when_champion_exists():
    metrics = {
        "gini": 0.40,
        "gini_champion": 0.42,
        "brier": 0.15,
        "psi": 0.05,
        "four_fifths_ratio": 0.90,
        "eo_gap": 0.01,
    }
    result = evaluate_gate("v0.2", metrics, is_first_model=False)
    assert result.status == GateStatus.FAIL
    assert any("uplift" in b.lower() for b in result.blockers)


def test_fairness_four_fifths_blocks():
    metrics = {
        "gini": 0.45,
        "brier": 0.12,
        "four_fifths_ratio": 0.70,
    }
    result = evaluate_gate("v0.1", metrics, is_first_model=True)
    assert result.status == GateStatus.FAIL
    assert any("Four-fifths" in b for b in result.blockers)
