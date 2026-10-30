"""Load gate thresholds and other config from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_GATE_THRESHOLDS: dict[str, float] = {
    "gini_floor": 0.35,
    "gini_uplift_min": 0.01,
    "brier_max": 0.20,
    "psi_max": 0.20,
    "four_fifths_min": 0.80,
    "eo_gap_max": 0.05,
}


def load_gate_thresholds(
    path: str | Path | None = None,
) -> dict[str, float]:
    """Merge YAML file over defaults. Missing file → defaults only."""
    thresholds = dict(DEFAULT_GATE_THRESHOLDS)
    if path is None:
        path = Path("config/gate_thresholds.yaml")
    else:
        path = Path(path)
    if path.exists():
        data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for key, value in data.items():
            if key in thresholds:
                thresholds[key] = float(value)
    return thresholds