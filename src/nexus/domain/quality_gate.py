"""Pure quality-gate logic with fail-closed validation."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from nexus.domain.models import GateResult, GateStatus, MetricResult

REQUIRED_METRICS = frozenset(
    {"gini", "brier", "psi", "four_fifths_ratio", "eo_gap"}
)

DEFAULT_THRESHOLDS: dict[str, float] = {
    "gini_floor": 0.35,
    "gini_uplift_min": 0.01,
    "brier_max": 0.20,
    "psi_max": 0.20,
    "four_fifths_min": 0.80,
    "eo_gap_max": 0.05,
}


def metrics_fingerprint(metrics: dict[str, Any]) -> str:
    """Return a stable SHA-256 fingerprint for the exact metric payload."""
    canonical = json.dumps(metrics, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def evaluate_gate(
    model_version: str,
    metrics: dict[str, Any],
    *,
    thresholds: dict[str, float] | None = None,
    is_first_model: bool = False,
    artifact_hash: str | None = None,
) -> GateResult:
    """Evaluate a candidate. Invalid inputs produce ERROR; missing inputs INCOMPLETE."""
    blockers: list[str] = []
    results: list[MetricResult] = []
    status = GateStatus.PASS

    def set_status(new_status: GateStatus) -> None:
        nonlocal status
        priority = {
            GateStatus.PASS: 0,
            GateStatus.INCOMPLETE: 1,
            GateStatus.FAIL: 2,
            GateStatus.ERROR: 3,
        }
        if priority[new_status] > priority[status]:
            status = new_status

    threshold_values = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    unknown_thresholds = sorted(set(threshold_values) - set(DEFAULT_THRESHOLDS))
    if unknown_thresholds:
        blockers.append(f"Unknown threshold keys: {', '.join(unknown_thresholds)}")
        set_status(GateStatus.ERROR)
    for name, value in threshold_values.items():
        if not _finite(value):
            blockers.append(f"Invalid threshold {name}={value!r}; expected finite number")
            set_status(GateStatus.ERROR)

    missing = sorted(REQUIRED_METRICS - set(metrics))
    if missing:
        blockers.append(f"Missing required metrics: {', '.join(missing)}")
        set_status(GateStatus.INCOMPLETE)

    numeric_metrics: dict[str, float] = {}
    for name, value in metrics.items():
        if name not in REQUIRED_METRICS and name != "gini_champion":
            continue
        if not _finite(value):
            blockers.append(f"Invalid metric {name}={value!r}; expected finite number")
            set_status(GateStatus.ERROR)
            continue
        numeric_metrics[name] = float(value)

    ranges = {
        "gini": (-1.0, 1.0),
        "gini_champion": (-1.0, 1.0),
        "brier": (0.0, 1.0),
        "psi": (0.0, math.inf),
        "four_fifths_ratio": (0.0, 1.0),
        "eo_gap": (0.0, 1.0),
    }
    for name, value in numeric_metrics.items():
        lower, upper = ranges[name]
        if not lower <= value <= upper:
            blockers.append(f"Metric {name}={value} outside valid range [{lower}, {upper}]")
            set_status(GateStatus.ERROR)

    # Do not evaluate comparisons against invalid threshold values.
    if all(_finite(v) for v in threshold_values.values()):
        gini = numeric_metrics.get("gini")
        if gini is not None:
            ok = gini >= threshold_values["gini_floor"]
            results.append(MetricResult(name="gini", value=gini, passed=ok,
                                        threshold=threshold_values["gini_floor"]))
            if not ok:
                blockers.append(f"Gini {gini:.4f} < floor {threshold_values['gini_floor']}")
                set_status(GateStatus.FAIL)

        if not is_first_model:
            champ = numeric_metrics.get("gini_champion")
            if gini is None or champ is None:
                blockers.append("Challenger requires valid gini and gini_champion")
                set_status(GateStatus.INCOMPLETE)
            else:
                uplift = gini - champ
                ok = uplift >= threshold_values["gini_uplift_min"]
                results.append(MetricResult(name="gini_uplift", value=uplift, passed=ok,
                                            threshold=threshold_values["gini_uplift_min"]))
                if not ok:
                    blockers.append(
                        f"Gini uplift {uplift:.4f} < min {threshold_values['gini_uplift_min']}"
                    )
                    set_status(GateStatus.FAIL)

        checks = (
            ("brier", "brier_max", True),
            ("psi", "psi_max", True),
            ("four_fifths_ratio", "four_fifths_min", False),
            ("eo_gap", "eo_gap_max", True),
        )
        for metric_name, threshold_name, upper_bound in checks:
            value = numeric_metrics.get(metric_name)
            if value is None:
                continue
            limit = threshold_values[threshold_name]
            passed = value <= limit if upper_bound else value >= limit
            results.append(MetricResult(name=metric_name, value=value, passed=passed,
                                        threshold=limit))
            if not passed:
                blockers.append(f"{metric_name}={value:.4f} violates {threshold_name}={limit}")
                set_status(GateStatus.FAIL)

    try:
        fingerprint = metrics_fingerprint(metrics)
    except (TypeError, ValueError):
        fingerprint = None
        blockers.append("Metrics payload is not canonical JSON (NaN/Infinity or unsupported type)")
        set_status(GateStatus.ERROR)

    if artifact_hash is not None and (
        not isinstance(artifact_hash, str) or not artifact_hash.strip()
    ):
        blockers.append("artifact_hash must be a non-empty string when supplied")
        set_status(GateStatus.ERROR)

    return GateResult(
        model_version=model_version,
        status=status,
        metrics=results,
        blockers=blockers,
        candidate_artifact_hash=artifact_hash,
        metrics_fingerprint=fingerprint,
    )
