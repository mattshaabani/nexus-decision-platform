"""Policy RAG contracts — pure domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class PolicyChunk:
    chunk_id: str
    title: str
    text: str
    source: str  # e.g. policy doc name


@dataclass(frozen=True)
class RetrievalHit:
    chunk: PolicyChunk
    score: float


@runtime_checkable
class PolicyRetrieverPort(Protocol):
    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievalHit]: ...