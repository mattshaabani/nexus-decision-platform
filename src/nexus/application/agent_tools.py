"""Read-only tools for support agents (MCP-ready shape)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from nexus.adapters.champion_store import ChampionStore
from nexus.adapters.policy_retriever import MarkdownPolicyRetriever
from nexus.domain.ports import DecisionStorePort
from nexus.domain.rag import RetrievalHit


class AgentToolError(Exception):
    pass


class AgentToolbox:
    """Explicit allow-list of tools. No promote / no threshold writes."""

    def __init__(
        self,
        decisions: DecisionStorePort,
        champion: ChampionStore,
        retriever: MarkdownPolicyRetriever,
    ) -> None:
        self._decisions = decisions
        self._champion = champion
        self._retriever = retriever

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": "get_decision", "description": "Fetch a scored decision by id"},
            {"name": "get_champion", "description": "Read current champion model metadata"},
            {"name": "get_policy", "description": "Retrieve policy chunks for a query"},
        ]

    def get_decision(self, decision_id: str) -> dict[str, Any]:
        d = self._decisions.get(decision_id)
        if d is None:
            raise AgentToolError(f"decision not found: {decision_id}")
        return {
            "decision_id": d.decision_id,
            "person_id": d.person_id,
            "model_version": d.model_version,
            "score": d.score,
            "probability": d.probability,
            "outcome": d.outcome.value,
            "reason_codes": list(d.reason_codes),
            "features": d.features,
        }

    def get_champion(self) -> dict[str, Any]:
        data = self._champion.get()
        if data is None:
            raise AgentToolError("no champion registered")
        return data

    def get_policy(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        hits: list[RetrievalHit] = self._retriever.retrieve(query, top_k=top_k)
        return [
            {
                "chunk_id": h.chunk.chunk_id,
                "title": h.chunk.title,
                "text": h.chunk.text,
                "source": h.chunk.source,
                "score": h.score,
            }
            for h in hits
        ]

    def call(self, name: str, **kwargs: Any) -> Any:
        allowed = {
            "get_decision": self.get_decision,
            "get_champion": self.get_champion,
            "get_policy": self.get_policy,
            "list_tools": lambda: self.list_tools(),
        }
        if name not in allowed:
            raise AgentToolError(f"tool not allowed: {name}")
        return allowed[name](**kwargs) if name != "list_tools" else allowed[name]()