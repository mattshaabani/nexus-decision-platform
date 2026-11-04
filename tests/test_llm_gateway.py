"""LLM gateway + echo adapter tests."""

from nexus.adapters.llm_echo import EchoLLM, InMemoryCache
from nexus.domain.llm_gateway import LLMMessage, LLMRequest, cache_key


def test_echo_and_cache():
    cache = InMemoryCache()
    llm = EchoLLM(cache)
    req = LLMRequest(messages=(LLMMessage(role="user", content="why was I declined?"),))
    r1 = llm.complete(req)
    r2 = llm.complete(req)
    assert r1.cached is False
    assert r2.cached is True
    assert "does not change the credit decision" in r1.content
    assert r2.cost_usd == 0.0


def test_cache_key_stable():
    req = LLMRequest(messages=(LLMMessage(role="user", content="x"),), model_hint="cheap")
    assert cache_key(req) == cache_key(req)