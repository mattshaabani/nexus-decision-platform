"""MLflow adapter for experiment tracking and model registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import mlflow

from nexus.domain.models import GateResult
from nexus.domain.scorecard.scorecard import Scorecard


def start_run(
    experiment_name: str = "nexus-scorecard",
    run_name: str | None = None,
    tracking_uri: str | None = None,
) -> mlflow.ActiveRun:
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    return mlflow.start_run(run_name=run_name)


def log_scorecard_run(
    *,
    scorecard: Scorecard,
    metrics: dict[str, float],
    gate: GateResult,
    model_card_markdown: str,
    params: dict[str, Any] | None = None,
    artifact_dir: str | Path = "artifacts",
) -> str:
    """Log params, metrics, gate status, model card, and a pickle of the scorecard.

    Returns the MLflow run_id.
    """
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Params
    mlflow.log_param("model_version", gate.model_version)
    mlflow.log_param("features", ",".join(scorecard.features))
    mlflow.log_param("base_score", scorecard.base_score)
    mlflow.log_param("pdo", scorecard.pdo)
    mlflow.log_param("gate_status", gate.status.value)
    if params:
        for k, v in params.items():
            mlflow.log_param(k, v)

    # Metrics
    for k, v in metrics.items():
        mlflow.log_metric(k, float(v))
    mlflow.log_metric("gate_passed", 1.0 if gate.passed else 0.0)

    # Model card artifact
    card_path = artifact_dir / f"model_card_{gate.model_version}.md"
    card_path.write_text(model_card_markdown, encoding="utf-8")
    mlflow.log_artifact(str(card_path))

    # Scorecard domain object (pickle)
    import pickle

    pkl_path = artifact_dir / f"scorecard_{gate.model_version}.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(scorecard, f)
    mlflow.log_artifact(str(pkl_path))

    return mlflow.active_run().info.run_id