"""Retrieval eval harness tests."""

from nexus.adapters.policy_retriever import MarkdownPolicyRetriever
from nexus.domain.retrieval_eval import RetrievalCase, evaluate_retriever


def test_recall_on_policy_corpus():
    r = MarkdownPolicyRetriever("data/policy")
    cases = [
        RetrievalCase(
            query="high utilisation risk",
            relevant_chunk_ids=frozenset({"underwriting_basics-1"}),
        ),
        RetrievalCase(
            query="income and default risk",
            relevant_chunk_ids=frozenset({"underwriting_basics-2"}),
        ),
    ]
    result = evaluate_retriever(r, cases, k=3)
    assert result.n_cases == 2
    assert result.recall_at_k >= 0.5