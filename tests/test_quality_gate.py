"""Unit tests for pure quality-gate rules."""

import math

import pytest

from nexus.domain.models import GateStatus
from nexus.domain.quality_gate import evaluate_gate


def _good_metrics(**overrides: float) -> dict[str, float]:
    metrics = {
        "gini": 0.42,
        "brier": 0.15,
        "psi": 0.05,
        "four_fifths_ratio": 0.92,
        "eo_gap": 0.01,
    }
    metrics.update(overrides)
    return metrics


def test_first_model_passes_with_good_metrics():
    result = evaluate_gate("v0.1", _good_metrics(), is_first_model=True)
    assert result.status == GateStatus.PASS
    assert not result.blockers


def test_gini_floor_blocks():
    result = evaluate_gate("v0.1", _good_metrics(gini=0.20), is_first_model=True)
    assert result.status == GateStatus.FAIL


def test_uplift_required_when_champion_exists():
    metrics = _good_metrics(gini=0.40, gini_champion=0.42)
    result = evaluate_gate("v0.2", metrics, is_first_model=False)
    assert result.status == GateStatus.FAIL
    assert any("uplift" in blocker.lower() for blocker in result.blockers)


def test_fairness_four_fifths_blocks():
    result = evaluate_gate(
        "v0.1", _good_metrics(four_fifths_ratio=0.70), is_first_model=True
    )
    assert result.status == GateStatus.FAIL


def test_missing_metric_incomplete():
    result = evaluate_gate("v", {"gini": 0.5}, is_first_model=True)
    assert result.status == GateStatus.INCOMPLETE


@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf, "abc", None, True])
def test_invalid_metric_value_error(bad_value):
    result = evaluate_gate(
        "v", _good_metrics(gini=bad_value), is_first_model=True
    )
    assert result.status == GateStatus.ERROR
    assert any("invalid metric" in blocker.lower() for blocker in result.blockers)


def test_metric_out_of_range_error():
    result = evaluate_gate("v", _good_metrics(brier=1.2), is_first_model=True)
    assert result.status == GateStatus.ERROR


def test_invalid_threshold_error():
    result = evaluate_gate(
        "v", _good_metrics(), thresholds={"brier_max": math.nan}, is_first_model=True
    )
    assert result.status == GateStatus.ERROR


def test_unknown_threshold_error():
    result = evaluate_gate(
        "v", _good_metrics(), thresholds={"unrecognized": 0.1}, is_first_model=True
    )
    assert result.status == GateStatus.ERROR


def test_gate_result_binds_artifact_and_metric_fingerprint():
    result = evaluate_gate(
        "v1", _good_metrics(), is_first_model=True, artifact_hash="sha256:abc"
    )
    assert result.candidate_artifact_hash == "sha256:abc"
    assert result.metrics_fingerprint


def test_threshold_out_of_range_error():
    result = evaluate_gate(
        "v", _good_metrics(), thresholds={"four_fifths_min": 1.5}, is_first_model=True
    )
    assert result.status == GateStatus.ERROR
    assert any("threshold" in blocker.lower() for blocker in result.blockers)
