"""Champion–challenger promotion use case."""

from __future__ import annotations

from typing import Any

from nexus.domain.models import GateResult, GateStatus
from nexus.domain.ports import ChampionStorePort
from nexus.domain.quality_gate import evaluate_gate, metrics_fingerprint


def evaluate_challenger(
    model_version: str,
    metrics: dict[str, float],
    store: ChampionStorePort,
    thresholds: dict[str, float] | None = None,
    *,
    artifact_hash: str,
) -> GateResult:
    """Evaluate candidate metrics and bind the gate to its artifact hash."""
    champion = store.get()
    if champion is None:
        return evaluate_gate(
            model_version,
            metrics,
            thresholds=thresholds,
            is_first_model=True,
            artifact_hash=artifact_hash,
        )

    champion_metrics = champion.get("metrics")
    if not isinstance(champion_metrics, dict) or not isinstance(
        champion_metrics.get("gini"), (int, float)
    ):
        # Missing champion benchmark is a governance-data error, not zero uplift.
        return GateResult(
            model_version=model_version,
            status=GateStatus.INCOMPLETE,
            metrics=[],
            blockers=["Champion registry has no valid Gini metric"],
            candidate_artifact_hash=artifact_hash,
            metrics_fingerprint=metrics_fingerprint(metrics),
        )

    metrics_with_champ = dict(metrics)
    metrics_with_champ["gini_champion"] = float(champion_metrics["gini"])
    return evaluate_gate(
        model_version,
        metrics_with_champ,
        thresholds=thresholds,
        is_first_model=False,
        artifact_hash=artifact_hash,
    )


def promote_if_passed(
    model_version: str,
    metrics: dict[str, float],
    gate: GateResult,
    store: ChampionStorePort,
    *,
    artifact_hash: str,
    extra: dict[str, Any] | None = None,
) -> bool:
    """Promote only when gate/model/artifact/metric snapshot all match."""
    if gate.status != GateStatus.PASS:
        return False
    if gate.model_version != model_version:
        return False
    if gate.candidate_artifact_hash != artifact_hash:
        return False
    try:
        fingerprint = metrics_fingerprint(metrics)
    except (TypeError, ValueError):
        return False
    if gate.metrics_fingerprint != fingerprint:
        return False

    store.set(model_version, metrics, artifact_hash=artifact_hash, extra=extra)
    return True
