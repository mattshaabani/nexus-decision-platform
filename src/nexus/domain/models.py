"""Core domain value objects and entities."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DecisionOutcome(str, Enum):
    APPROVE = "approve"
    REFER = "refer"
    DECLINE = "decline"


class ModelStatus(str, Enum):
    CANDIDATE = "candidate"
    CHAMPION = "champion"
    RETIRED = "retired"
    REJECTED = "rejected"


class GateStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class Decision(BaseModel):
    """A single regulated decision with full audit context."""

    decision_id: str
    person_id: str
    model_version: str
    score: float
    probability: float
    outcome: DecisionOutcome
    reason_codes: list[str] = Field(default_factory=list)
    features: dict[str, Any] = Field(default_factory=dict)
    override: bool = False
    override_by: str | None = None
    override_reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MetricResult(BaseModel):
    name: str
    value: float
    threshold: float | None = None
    passed: bool | None = None
    person_level: bool = True
    n_persons: int | None = None
    n_observations: int | None = None
    notes: str | None = None


class GateResult(BaseModel):
    """Result of the quality / promotion gate."""

    status: GateStatus
    model_version: str
    metrics: list[MetricResult]
    blockers: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def passed(self) -> bool:
        return self.status == GateStatus.PASS


class ModelCard(BaseModel):
    """Machine- and human-readable model card produced by the gate."""

    model_version: str
    status: ModelStatus
    training_window: str | None = None
    evaluation_window: str | None = None
    metrics: list[MetricResult] = Field(default_factory=list)
    fairness_summary: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    gate_result: GateResult | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
