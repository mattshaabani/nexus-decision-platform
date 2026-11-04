"""OpenAI-compatible chat adapter. Disabled unless NEXUS_LLM_API_KEY is set."""

from __future__ import annotations

import os
import time
from typing import Any

from nexus.domain.llm_gateway import (
    LLMPort,
    LLMRequest,
    LLMResponse,
    SemanticCachePort,
    cache_key,
    estimate_cost_usd,
)


class OpenAICompatibleLLM:
    """Uses the official openai package if installed and key is present."""

    def __init__(
        self,
        cache: SemanticCachePort | None = None,
        *,
        model_cheap: str = "gpt-4o-mini",
        model_strong: str = "gpt-4o",
        base_url: str | None = None,
    ) -> None:
        self.cache = cache
        self.model_cheap = model_cheap
        self.model_strong = model_strong
        self.api_key = os.environ.get("NEXUS_LLM_API_KEY", "")
        self.base_url = base_url or os.environ.get("NEXUS_LLM_BASE_URL")
        self._client: Any = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _client_or_raise(self) -> Any:
        if not self.api_key:
            raise RuntimeError(
                "NEXUS_LLM_API_KEY not set — use EchoLLM or set the env var"
            )
        if self._client is None:
            from openai import OpenAI

            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

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

        model = (
            self.model_strong if request.model_hint == "strong" else self.model_cheap
        )
        client = self._client_or_raise()
        t0 = time.perf_counter()
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        content = completion.choices[0].message.content or ""
        usage = completion.usage
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        cost = estimate_cost_usd(
            "strong" if request.model_hint == "strong" else "cheap",
            prompt_tokens,
            completion_tokens,
        )
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