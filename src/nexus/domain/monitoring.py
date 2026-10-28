"""Drift / stability monitoring — pure domain."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from nexus.domain.evaluation import brier_score, gini_coefficient, psi


@dataclass(frozen=True)
class MonitoringReport:
    psi_score: float
    gini_live: float
    brier_live: float
    gini_baseline: float | None
    n_live: int
    alerts: tuple[str, ...]


def monitor_scores(
    *,
    baseline_scores: np.ndarray,
    live_scores: np.ndarray,
    live_y: np.ndarray | None = None,
    live_proba: np.ndarray | None = None,
    baseline_gini: float | None = None,
    psi_threshold: float = 0.20,
    gini_drop_max: float = 0.05,
) -> MonitoringReport:
    """Compare live scoring window to training baseline.

    Alerts when PSI exceeds threshold or live Gini drops too far vs baseline.
    """
    baseline_scores = np.asarray(baseline_scores, dtype=float)
    live_scores = np.asarray(live_scores, dtype=float)

    psi_val = psi(baseline_scores, live_scores)
    alerts: list[str] = []

    if psi_val > psi_threshold:
        alerts.append(f"PSI {psi_val:.4f} > {psi_threshold}")

    gini_live = 0.0
    brier_live = 0.0
    if live_y is not None and live_proba is not None:
        gini_live = gini_coefficient(live_y, live_proba)
        brier_live = brier_score(live_y, live_proba)
        if baseline_gini is not None and (baseline_gini - gini_live) > gini_drop_max:
            alerts.append(
                f"Gini drop {baseline_gini - gini_live:.4f} > {gini_drop_max} "
                f"(baseline={baseline_gini:.4f}, live={gini_live:.4f})"
            )

    return MonitoringReport(
        psi_score=float(psi_val),
        gini_live=float(gini_live),
        brier_live=float(brier_live),
        gini_baseline=baseline_gini,
        n_live=int(len(live_scores)),
        alerts=tuple(alerts),
    )