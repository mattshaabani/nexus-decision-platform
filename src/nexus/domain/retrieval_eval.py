"""Retrieval evaluation — recall@k style helpers."""

from __future__ import annotations

from dataclasses import dataclass

from nexus.domain.rag import PolicyRetrieverPort


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    relevant_chunk_ids: frozenset[str]


@dataclass(frozen=True)
class RetrievalEvalResult:
    n_cases: int
    recall_at_k: float
    mean_hits: float


def evaluate_retriever(
    retriever: PolicyRetrieverPort,
    cases: list[RetrievalCase],
    *,
    k: int = 3,
) -> RetrievalEvalResult:
    if not cases:
        return RetrievalEvalResult(n_cases=0, recall_at_k=0.0, mean_hits=0.0)

    recalls: list[float] = []
    hits_counts: list[int] = []
    for case in cases:
        hits = retriever.retrieve(case.query, top_k=k)
        got = {h.chunk.chunk_id for h in hits}
        inter = got & set(case.relevant_chunk_ids)
        hits_counts.append(len(inter))
        if case.relevant_chunk_ids:
            recalls.append(len(inter) / len(case.relevant_chunk_ids))
        else:
            recalls.append(0.0)

    return RetrievalEvalResult(
        n_cases=len(cases),
        recall_at_k=float(sum(recalls) / len(recalls)),
        mean_hits=float(sum(hits_counts) / len(hits_counts)),
    )