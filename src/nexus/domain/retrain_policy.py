"""Policies that decide whether a retrain candidate should be started."""

from __future__ import annotations

from dataclasses import dataclass

from nexus.domain.monitoring import MonitoringReport


@dataclass(frozen=True)
class RetrainDecision:
    should_retrain: bool
    reasons: tuple[str, ...]


def evaluate_retrain_triggers(
    report: MonitoringReport,
    *,
    psi_trigger: float = 0.20,
    gini_drop_trigger: float = 0.05,
) -> RetrainDecision:
    """Recommend retrain when live monitoring breaches policy thresholds.

    Uses MonitoringReport alerts plus explicit numeric checks so policy
    stays testable even if alert text changes.
    """
    reasons: list[str] = []

    if report.psi_score > psi_trigger:
        reasons.append(
            f"PSI {report.psi_score:.4f} exceeds trigger {psi_trigger}"
        )

    if (
        report.gini_baseline is not None
        and (report.gini_baseline - report.gini_live) > gini_drop_trigger
    ):
        drop = report.gini_baseline - report.gini_live
        reasons.append(
            f"Gini drop {drop:.4f} exceeds trigger {gini_drop_trigger}"
        )

    # Also surface any monitoring alerts not already covered
    for alert in report.alerts:
        if alert not in reasons:
            reasons.append(alert)

    return RetrainDecision(
        should_retrain=len(reasons) > 0,
        reasons=tuple(reasons),
    )