"""CLI smoke tests."""

import json
from pathlib import Path

from typer.testing import CliRunner

from nexus.entrypoints.cli import app

runner = CliRunner()


def test_quality_gate_cli_passes_for_valid_metrics(tmp_path: Path):
    metrics = {
        "gini": 0.42,
        "brier": 0.15,
        "psi": 0.05,
        "four_fifths_ratio": 0.9,
        "eo_gap": 0.02,
    }
    file_path = tmp_path / "metrics.json"
    file_path.write_text(json.dumps(metrics), encoding="utf-8")

    result = runner.invoke(
        app,
        ["quality-gate", "--metrics", str(file_path), "--model-version", "v1", "--first-model"],
    )
    assert result.exit_code == 0
    assert "PASS" in result.stdout


def test_quality_gate_cli_fails_for_missing_metrics(tmp_path: Path):
    file_path = tmp_path / "metrics.json"
    file_path.write_text(json.dumps({"gini": 0.4}), encoding="utf-8")

    result = runner.invoke(
        app,
        ["quality-gate", "--metrics", str(file_path), "--model-version", "v1", "--first-model"],
    )
    assert result.exit_code == 1
    assert "INCOMPLETE" in result.stdout
