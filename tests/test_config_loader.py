"""Tests for gate threshold config loading."""

from pathlib import Path

from nexus.adapters.config_loader import DEFAULT_GATE_THRESHOLDS, load_gate_thresholds


def test_defaults_when_missing(tmp_path: Path):
    t = load_gate_thresholds(tmp_path / "nope.yaml")
    assert t == DEFAULT_GATE_THRESHOLDS


def test_yaml_override(tmp_path: Path):
    p = tmp_path / "gate.yaml"
    p.write_text("gini_floor: 0.50\npsi_max: 0.10\n", encoding="utf-8")
    t = load_gate_thresholds(p)
    assert t["gini_floor"] == 0.50
    assert t["psi_max"] == 0.10
    assert t["brier_max"] == DEFAULT_GATE_THRESHOLDS["brier_max"]