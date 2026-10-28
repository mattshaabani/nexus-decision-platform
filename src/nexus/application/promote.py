"""Champion–challenger promotion use case."""

from __future__ import annotations

from typing import Any

from nexus.adapters.champion_store import ChampionStore
from nexus.domain.models import GateResult, GateStatus
from nexus.domain.quality_gate import evaluate_gate


def evaluate_challenger(
    model_version: str,
    metrics: dict[str, float],
    store: ChampionStore,
    thresholds: dict[str, float] | None = None,
) -> GateResult:
    """Run quality gate as first model or as challenger vs champion."""
    champion = store.get()
    if champion is None:
        return evaluate_gate(
            model_version, metrics, thresholds=thresholds, is_first_model=True
        )

    # Inject champion Gini for uplift check
    metrics_with_champ = dict(metrics)
    metrics_with_champ["gini_champion"] = float(champion["metrics"].get("gini", 0.0))
    return evaluate_gate(
        model_version,
        metrics_with_champ,
        thresholds=thresholds,
        is_first_model=False,
    )


def promote_if_passed(
    model_version: str,
    metrics: dict[str, float],
    gate: GateResult,
    store: ChampionStore,
    *,
    extra: dict[str, Any] | None = None,
) -> bool:
    """Write champion only if gate passed. Returns True if promoted."""
    if gate.status != GateStatus.PASS:
        return False
    store.set(model_version, metrics, extra=extra)
    return True