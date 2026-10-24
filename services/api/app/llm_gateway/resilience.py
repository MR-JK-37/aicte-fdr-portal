"""Resilience primitives backed by Valkey (Redis-compatible), shared
across API/worker/voice processes — per-process in-memory state would be
useless the moment there's more than one worker. Implements the pieces
the brief's LLM gateway spec calls for: per-provider token buckets,
circuit breaker (open 60s after 3 failures), exponential backoff with
jitter, and a 24h response cache keyed by normalised prompt hash.
"""

import hashlib
import json
import random
import time
from functools import lru_cache

import redis

from app.config import settings

CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_OPEN_SECONDS = 60
CACHE_TTL_SECONDS = 24 * 60 * 60


@lru_cache
def _redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.valkey_url, decode_responses=True)


def normalise_prompt_key(provider: str, model: str, messages: list[dict]) -> str:
    canonical = json.dumps(
        {"provider": provider, "model": model, "messages": messages}, sort_keys=True
    )
    return "llm_cache:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_cached_response(provider: str, model: str, messages: list[dict]) -> dict | None:
    client = _redis_client()
    raw = client.get(normalise_prompt_key(provider, model, messages))
    return json.loads(raw) if raw else None


def set_cached_response(
    provider: str, model: str, messages: list[dict], response: dict
) -> None:
    client = _redis_client()
    client.set(
        normalise_prompt_key(provider, model, messages),
        json.dumps(response),
        ex=CACHE_TTL_SECONDS,
    )


class CircuitOpenError(Exception):
    pass


def _circuit_key(provider: str) -> str:
    return f"llm_circuit:{provider}"


def is_circuit_open(provider: str) -> bool:
    client = _redis_client()
    state = client.get(_circuit_key(provider))
    return state == "open"


def record_failure(provider: str) -> None:
    client = _redis_client()
    failures_key = f"llm_circuit_failures:{provider}"
    failures = client.incr(failures_key)
    client.expire(failures_key, CIRCUIT_OPEN_SECONDS)
    if failures >= CIRCUIT_FAILURE_THRESHOLD:
        client.set(_circuit_key(provider), "open", ex=CIRCUIT_OPEN_SECONDS)


def record_success(provider: str) -> None:
    client = _redis_client()
    client.delete(f"llm_circuit_failures:{provider}")
    client.delete(_circuit_key(provider))


class RateLimitedError(Exception):
    def __init__(self, retry_after_seconds: float):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"rate limited, retry after {retry_after_seconds}s")


def token_bucket_allow(provider: str, *, limit: int, window_seconds: int = 60) -> bool:
    """A simple fixed-window counter (not a true leaky bucket, but
    sufficient for respecting a provider's rpm limit across processes
    without a fully separate scheduler). Returns False when the provider
    should be skipped this request, not raised — callers fall through to
    the next provider in the chain rather than blocking."""
    if limit is None:
        return True
    client = _redis_client()
    window = int(time.time() // window_seconds)
    key = f"llm_bucket:{provider}:{window}"
    count = client.incr(key)
    client.expire(key, window_seconds)
    return count <= limit


def backoff_with_jitter(
    attempt: int, base_seconds: float = 0.5, max_seconds: float = 8.0
) -> float:
    delay = min(max_seconds, base_seconds * (2**attempt))
    return random.uniform(0, delay)
