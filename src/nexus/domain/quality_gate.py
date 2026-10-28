"""Pure quality-gate logic – no I/O."""

from __future__ import annotations

from nexus.domain.models import GateResult, GateStatus, MetricResult

# Default thresholds – override via config in adapters / scripts
DEFAULT_THRESHOLDS = {
    "gini_floor": 0.35,
    "gini_uplift_min": 0.01,
    "brier_max": 0.20,
    "psi_max": 0.20,
    "four_fifths_min": 0.80,
    "eo_gap_max": 0.05,
}


def evaluate_gate(
    model_version: str,
    metrics: dict[str, float],
    thresholds: dict[str, float] | None = None,
    is_first_model: bool = False,
) -> GateResult:
    """Evaluate a candidate model against governance thresholds.

    Parameters
    ----------
    model_version:
        Identifier of the candidate.
    metrics:
        Flat dict of metric name → value. Expected keys include:
        gini, gini_champion, brier, psi, four_fifths_ratio, eo_gap.
    thresholds:
        Override defaults if provided.
    is_first_model:
        If True, skip uplift check and only apply absolute floors.
    """
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    results: list[MetricResult] = []
    blockers: list[str] = []

    # --- Gini / ranking ---
    gini = metrics.get("gini")
    if gini is not None:
        passed = gini >= th["gini_floor"]
        results.append(
            MetricResult(
                name="gini",
                value=gini,
                threshold=th["gini_floor"],
                passed=passed,
                person_level=True,
            )
        )
        if not passed:
            blockers.append(f"Gini {gini:.4f} < floor {th['gini_floor']}")

        if not is_first_model:
            gini_champ = metrics.get("gini_champion")
            if gini_champ is not None:
                uplift = gini - gini_champ
                uplift_ok = uplift >= th["gini_uplift_min"]
                results.append(
                    MetricResult(
                        name="gini_uplift",
                        value=uplift,
                        threshold=th["gini_uplift_min"],
                        passed=uplift_ok,
                        person_level=True,
                    )
                )
                if not uplift_ok:
                    blockers.append(
                        f"Gini uplift {uplift:.4f} < min {th['gini_uplift_min']}"
                    )

    # --- Calibration ---
    brier = metrics.get("brier")
    if brier is not None:
        passed = brier <= th["brier_max"]
        results.append(
            MetricResult(
                name="brier",
                value=brier,
                threshold=th["brier_max"],
                passed=passed,
                person_level=True,
            )
        )
        if not passed:
            blockers.append(f"Brier {brier:.4f} > max {th['brier_max']}")

    # --- Stability ---
    psi = metrics.get("psi")
    if psi is not None:
        passed = psi <= th["psi_max"]
        results.append(
            MetricResult(
                name="psi",
                value=psi,
                threshold=th["psi_max"],
                passed=passed,
                person_level=False,
            )
        )
        if not passed:
            blockers.append(f"PSI {psi:.4f} > max {th['psi_max']}")

    # --- Fairness ---
    four_fifths = metrics.get("four_fifths_ratio")
    if four_fifths is not None:
        passed = four_fifths >= th["four_fifths_min"]
        results.append(
            MetricResult(
                name="four_fifths_ratio",
                value=four_fifths,
                threshold=th["four_fifths_min"],
                passed=passed,
                person_level=True,
            )
        )
        if not passed:
            blockers.append(
                f"Four-fifths ratio {four_fifths:.4f} < min {th['four_fifths_min']}"
            )

    eo_gap = metrics.get("eo_gap")
    if eo_gap is not None:
        passed = abs(eo_gap) <= th["eo_gap_max"]
        results.append(
            MetricResult(
                name="eo_gap",
                value=eo_gap,
                threshold=th["eo_gap_max"],
                passed=passed,
                person_level=True,
            )
        )
        if not passed:
            blockers.append(f"EO gap {eo_gap:.4f} exceeds ±{th['eo_gap_max']}")

    status = GateStatus.PASS if not blockers else GateStatus.FAIL
    return GateResult(
        status=status,
        model_version=model_version,
        metrics=results,
        blockers=blockers,
    )
