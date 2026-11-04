"""Policy retriever tests."""

from nexus.adapters.policy_retriever import MarkdownPolicyRetriever


def test_retrieve_utilisation():
    r = MarkdownPolicyRetriever("data/policy")
    hits = r.retrieve("credit utilisation decline", top_k=3)
    assert len(hits) >= 1
    assert any("util" in h.chunk.title.lower() or "util" in h.chunk.text.lower() for h in hits)