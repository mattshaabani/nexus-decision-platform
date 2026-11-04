"""LLM gateway contracts — pure domain (no vendor SDKs)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class LLMMessage:
    role: str  # system | user | assistant
    content: str


@dataclass(frozen=True)
class LLMRequest:
    messages: tuple[LLMMessage, ...]
    model_hint: str = "cheap"  # cheap | strong
    temperature: float = 0.0
    max_tokens: int = 512
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    cached: bool
    latency_ms: float
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@runtime_checkable
class LLMPort(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...


@runtime_checkable
class SemanticCachePort(Protocol):
    def get(self, key: str) -> LLMResponse | None: ...
    def set(self, key: str, value: LLMResponse) -> None: ...


def cache_key(request: LLMRequest) -> str:
    """Deterministic key for exact-match cache (v1)."""
    parts = [request.model_hint, str(request.temperature), str(request.max_tokens)]
    for m in request.messages:
        parts.append(f"{m.role}:{m.content.strip()}")
    return "|".join(parts)


def estimate_cost_usd(
    model: str, prompt_tokens: int, completion_tokens: int
) -> float:
    """Rough default tariff table — override in adapters."""
    # per 1M tokens (illustrative)
    rates = {
        "cheap": (0.15, 0.60),
        "strong": (2.50, 10.00),
    }
    inp, out = rates.get(model, rates["cheap"])
    return (prompt_tokens * inp + completion_tokens * out) / 1_000_000