"""FP&A investigation is narrative-only."""

from nexus.adapters.llm_echo import EchoLLM, InMemoryCache
from nexus.adapters.policy_retriever import MarkdownPolicyRetriever
from nexus.application.fpa_investigate import investigate_variance


def test_investigate_returns_summary():
    result = investigate_variance(
        metric_name="default_rate",
        actual=0.042,
        plan=0.035,
        period="2026-Q3",
        llm=EchoLLM(InMemoryCache()),
        retriever=MarkdownPolicyRetriever("data/policy"),
    )
    assert (\n        "does not change the credit decision" in result.summary.lower()\n        or len(result.summary) > 20\n    )
    assert result.cost_usd >= 0