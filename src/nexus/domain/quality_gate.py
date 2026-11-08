"""Pure quality-gate logic – fail-closed."""

from __future__ import annotations

import math

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


def _finite(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def evaluate_gate(
    model_version: str,
    metrics: dict[str, float],
    *,
    thresholds: dict[str, float] | None = None,
    is_first_model: bool = False,
) -> GateResult:
    thr = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    results: list[MetricResult] = []
    blockers: list[str] = []
    status = GateStatus.PASS

    # Required metrics present + finite
    missing = sorted(REQUIRED_METRICS - set(metrics))
    if missing:
        status = GateStatus.INCOMPLETE
        blockers.append(f"Missing required metrics: {', '.join(missing)}")

    for name, value in metrics.items():
        if name in REQUIRED_METRICS or name == "gini_champion":
            if not _finite(float(value)):
                status = GateStatus.ERROR
                blockers.append(f"Non-finite metric: {name}={value!r}")

    def add(name: str, value: float, passed: bool, threshold: float | None = None) -> None:
        results.append(
            MetricResult(name=name, value=float(value), passed=passed, threshold=threshold)
        )
        if not passed and status == GateStatus.PASS:
            nonlocal_status_fail()

    # helper to set FAIL only if still PASS
    def nonlocal_status_fail() -> None:
        nonlocal status
        if status == GateStatus.PASS:
            status = GateStatus.FAIL

    # If ERROR/INCOMPLETE, still compute what we can but do not PASS
    gini = metrics.get("gini")
    if gini is not None and _finite(gini):
        ok = gini >= thr["gini_floor"]
        results.append(
            MetricResult(
                name="gini",
                value=float(gini),
                passed=ok,
                threshold=thr["gini_floor"],
            )
        )
        if not ok:
            blockers.append(f"Gini {gini:.4f} < floor {thr['gini_floor']}")
            if status == GateStatus.PASS:
                status = GateStatus.FAIL

    if not is_first_model:
        champ = metrics.get("gini_champion")
        if gini is not None and champ is not None and _finite(gini) and _finite(champ):
            uplift = float(gini) - float(champ)
            ok = uplift >= thr["gini_uplift_min"]
            results.append(
                MetricResult(
                    name="gini_uplift",
                    value=uplift,
                    passed=ok,
                    threshold=thr["gini_uplift_min"],
                )
            )
            if not ok:
                blockers.append(
                    f"Gini uplift {uplift:.4f} < min {thr['gini_uplift_min']}"
                )
                if status == GateStatus.PASS:
                    status = GateStatus.FAIL
        else:
            if status == GateStatus.PASS:
                status = GateStatus.INCOMPLETE
            blockers.append("Challenger requires gini and gini_champion")

    checks = [
        ("brier", "brier_max", True),
        ("psi", "psi_max", True),
        ("four_fifths_ratio", "four_fifths_min", False),
        ("eo_gap", "eo_gap_max", True),
    ]
    for metric_name, thr_key, upper_bound in checks:
        if metric_name not in metrics or not _finite(metrics[metric_name]):
            continue
        val = float(metrics[metric_name])
        limit = thr[thr_key]
        ok = val <= limit if upper_bound else val >= limit
        results.append(
            MetricResult(name=metric_name, value=val, passed=ok, threshold=limit)
        )
        if not ok:
            blockers.append(f"{metric_name}={val:.4f} violates {thr_key}={limit}")
            if status == GateStatus.PASS:
                status = GateStatus.FAIL

    return GateResult(
        model_version=model_version,
        status=status,
        metrics=results,
        blockers=blockers,
    )