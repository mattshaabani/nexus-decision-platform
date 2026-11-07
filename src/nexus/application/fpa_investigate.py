"""FP&A-style investigation helper — narrative only, no ledger writes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nexus.domain.llm_gateway import LLMMessage, LLMPort, LLMRequest
from nexus.domain.rag import PolicyRetrieverPort


@dataclass(frozen=True)
class FPAInvestigation:
    summary: str
    citations: list[dict[str, Any]]
    model: str
    cached: bool
    cost_usd: float


def investigate_variance(
    *,
    metric_name: str,
    actual: float,
    plan: float,
    period: str,
    llm: LLMPort,
    retriever: PolicyRetrieverPort,
    top_k: int = 3,
) -> FPAInvestigation:
    """Explain variance vs plan using policy context. Does not post journals."""
    variance = actual - plan
    pct = (variance / plan) if plan else 0.0
    hits = retriever.retrieve(
        f"monitoring model risk variance {metric_name} {period}",
        top_k=top_k,
    )
    policy = "\n\n".join(
        f"[{h.chunk.chunk_id}] {h.chunk.title}: {h.chunk.text[:300]}" for h in hits
    ) or "(no policy)"

    req = LLMRequest(
        messages=(
            LLMMessage(
                role="system",
                content=(
                    "You are an FP&A investigation assistant. "
                    "Explain metric variance using only provided numbers and policy. "
                    "Do not book forecasts, post journals, or change credit decisions."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Period={period} metric={metric_name} "
                    f"actual={actual} plan={plan} variance={variance} pct={pct:.2%}\n\n"
                    f"Policy:\n{policy}"
                ),
            ),
        ),
        model_hint="cheap",
    )
    resp = llm.complete(req)
    return FPAInvestigation(
        summary=resp.content,
        citations=[
            {
                "chunk_id": h.chunk.chunk_id,
                "title": h.chunk.title,
                "source": h.chunk.source,
                "score": h.score,
            }
            for h in hits
        ],
        model=resp.model,
        cached=resp.cached,
        cost_usd=resp.cost_usd,
    )