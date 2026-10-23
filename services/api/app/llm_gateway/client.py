"""Thin OpenAI-compatible chat-completion client. All registered providers
(verified or not) speak this wire format per config/llm_providers.yaml's
`openai_compatible` flag — that's why one client class covers all of
them, Sarvam's STT/TTS endpoints (Phase 8) being the one exception.
"""

import time
from dataclasses import dataclass

import httpx

from app.llm_gateway.registry import ProviderSpec
from app.llm_gateway.resilience import RateLimitedError


@dataclass
class CompletionResult:
    content: str
    raw_response: dict
    tokens_in: int | None
    tokens_out: int | None
    latency_ms: int


class ProviderCallError(Exception):
    pass


def call_chat_completion(
    provider: ProviderSpec,
    model_id: str,
    messages: list[dict],
    *,
    json_mode: bool = False,
    timeout_seconds: float = 30.0,
) -> CompletionResult:
    if not provider.openai_compatible:
        raise ProviderCallError(f"provider '{provider.name}' is not OpenAI-compatible; use its dedicated client")
    if not provider.has_key:
        raise ProviderCallError(f"provider '{provider.name}' has no API key configured ({provider.key_env_var})")

    headers = {"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"}
    payload: dict = {"model": model_id, "messages": messages}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    start = time.monotonic()
    try:
        response = httpx.post(
            f"{provider.base_url}/chat/completions", headers=headers, json=payload, timeout=timeout_seconds
        )
    except httpx.RequestError as exc:
        raise ProviderCallError(f"{provider.name}: request failed: {exc}") from exc
    latency_ms = int((time.monotonic() - start) * 1000)

    if response.status_code == 429:
        retry_after = float(response.headers.get("Retry-After", "1"))
        raise RateLimitedError(retry_after)
    if response.status_code >= 400:
        raise ProviderCallError(f"{provider.name}: HTTP {response.status_code}: {response.text[:500]}")

    data = response.json()
    choice = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return CompletionResult(
        content=choice,
        raw_response=data,
        tokens_in=usage.get("prompt_tokens"),
        tokens_out=usage.get("completion_tokens"),
        latency_ms=latency_ms,
    )
