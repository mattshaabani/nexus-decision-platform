"""Deterministic echo adapter for tests and offline demos (no external API)."""

from __future__ import annotations

import time

from nexus.domain.llm_gateway import (
    LLMPort,
    LLMRequest,
    LLMResponse,
    SemanticCachePort,
    cache_key,
    estimate_cost_usd,
)


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, LLMResponse] = {}

    def get(self, key: str) -> LLMResponse | None:
        return self._store.get(key)

    def set(self, key: str, value: LLMResponse) -> None:
        self._store[key] = value


class EchoLLM:
    """Returns a fixed grounded-style reply; respects cache if provided."""

    def __init__(self, cache: SemanticCachePort | None = None) -> None:
        self.cache = cache

    def complete(self, request: LLMRequest) -> LLMResponse:
        key = cache_key(request)
        if self.cache is not None:
            hit = self.cache.get(key)
            if hit is not None:
                return LLMResponse(
                    content=hit.content,
                    model=hit.model,
                    prompt_tokens=hit.prompt_tokens,
                    completion_tokens=hit.completion_tokens,
                    cost_usd=0.0,
                    cached=True,
                    latency_ms=0.0,
                )

        t0 = time.perf_counter()
        last_user = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            "",
        )
        content = (
            "[grounded-echo] This support reply does not change the credit decision. "
            f"Query summary: {last_user[:200]}"
        )
        model = request.model_hint
        prompt_tokens = sum(len(m.content.split()) for m in request.messages)
        completion_tokens = len(content.split())
        cost = estimate_cost_usd(model, prompt_tokens, completion_tokens)
        latency_ms = (time.perf_counter() - t0) * 1000
        resp = LLMResponse(
            content=content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            cached=False,
            latency_ms=latency_ms,
        )
        if self.cache is not None:
            self.cache.set(key, resp)
        return resp



def build_default_llm(cache: SemanticCachePort | None = None) -> LLMPort:
    """Prefer OpenAI-compatible if NEXUS_LLM_API_KEY is set; else echo."""
    try:
        from nexus.adapters.llm_openai import OpenAICompatibleLLM

        real = OpenAICompatibleLLM(cache)
        if real.available:
            return real
    except Exception:
        pass
    return EchoLLM(cache)