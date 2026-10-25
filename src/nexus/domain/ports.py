"""Ports (interfaces) that adapters must implement."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from nexus.domain.models import Decision, GateResult, ModelCard


@runtime_checkable
class ModelRegistryPort(Protocol):
    def get_champion(self) -> str | None: ...
    def register_candidate(self, model_version: str, artifact_uri: str, metrics: dict[str, Any]) -> None: ...
    def promote_to_champion(self, model_version: str) -> None: ...


@runtime_checkable
class DecisionStorePort(Protocol):
    def save(self, decision: Decision) -> None: ...
    def get(self, decision_id: str) -> Decision | None: ...


@runtime_checkable
class QualityGatePort(Protocol):
    def evaluate(self, model_version: str, metrics: dict[str, float]) -> GateResult: ...
    def produce_model_card(self, model_version: str, gate_result: GateResult) -> ModelCard: ...
