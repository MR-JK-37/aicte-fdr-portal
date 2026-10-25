"""The LLM gateway's single entry point: `generate()`. Orchestrates
routing, redaction, caching, rate limiting, circuit breaking, retries
with backoff+jitter, JSON-schema validation with repair-then-cross-
provider-reask, and agent_runs logging — so callers (agents, Phase 6's
second half) never talk to a provider directly.
"""

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.llm_gateway import redaction, resilience
from app.llm_gateway.client import (
    ProviderAuthError,
    ProviderCallError,
    call_chat_completion,
)
from app.llm_gateway.registry import load_registry
from app.llm_gateway.routing import get_chain
from app.llm_gateway.schema_validation import (
    build_repair_prompt,
    validate_json_response,
)
from app.models.audit import AgentRun

GatewayStatus = Literal["ok", "human_review_required", "unavailable"]


def is_gateway_disabled() -> bool:
    """Checks the global AI gateway kill switch (config/LLM_PROVIDERS.yaml / SPEC §14.3)."""
    val = os.environ.get("AI_GATEWAY_DISABLED", "").strip().lower()
    return val in ("true", "1", "yes", "on")


def is_ai_available(task_class: str = "rag", tier: str = "P") -> bool:
    """Returns True if the gateway is enabled and at least one provider is configured for the route."""
    if is_gateway_disabled():
        return False
    chain = get_chain(task_class, tier=tier)
    return bool(chain)


@dataclass
class GatewayResult:
    status: GatewayStatus
    content: str | None
    parsed: BaseModel | None
    provider: str | None
    model: str | None
    token_map: dict[str, str]
    attempts: list[dict]


def _log_agent_run(
    session: Session | None,
    *,
    agent_name: str,
    task_class: str,
    provider: str | None,
    model: str | None,
    input_text: str,
    tokens_in: int | None,
    tokens_out: int | None,
    latency_ms: int | None,
    status: str,
) -> None:
    if session is None:
        return
    session.add(
        AgentRun(
            agent_name=agent_name,
            task_class=task_class,
            provider=provider,
            model=model,
            input_hash=hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            status=status,
        )
    )
    session.flush()


def generate(
    task_class: str,
    messages: list[dict],
    *,
    tier: str = "P",
    response_schema: type[BaseModel] | None = None,
    agent_name: str = "unnamed-agent",
    session: Session | None = None,
    use_cache: bool = True,
) -> GatewayResult:
    redacted_messages = [
        {**m, "content": redaction.redact(m["content"])[0]}
        if m.get("role") == "user"
        else m
        for m in messages
    ]
    token_map: dict[str, str] = {}
    for m in messages:
        if m.get("role") == "user":
            _, tm = redaction.redact(m["content"])
            token_map.update(tm)

    if is_gateway_disabled():
        _log_agent_run(
            session,
            agent_name=agent_name,
            task_class=task_class,
            provider=None,
            model=None,
            input_text=str(redacted_messages),
            tokens_in=None,
            tokens_out=None,
            latency_ms=0,
            status="gateway_disabled",
        )
        return GatewayResult(
            "unavailable",
            None,
            None,
            None,
            None,
            token_map,
            [
                {
                    "skipped": "ai_gateway_disabled",
                    "reason": "AI_GATEWAY_DISABLED kill switch active",
                }
            ],
        )

    registry = load_registry()
    chain = get_chain(task_class, tier=tier)
    attempts: list[dict] = []

    if not chain:
        _log_agent_run(
            session,
            agent_name=agent_name,
            task_class=task_class,
            provider=None,
            model=None,
            input_text=str(redacted_messages),
            tokens_in=None,
            tokens_out=None,
            latency_ms=None,
            status="human_review_required",
        )
        return GatewayResult(
            "human_review_required", None, None, None, None, token_map, attempts
        )

    original_redacted_messages = redacted_messages

    for step in chain:
        provider = registry[step.provider]

        if resilience.is_circuit_open(step.provider):
            attempts.append(
                {
                    "provider": step.provider,
                    "model": step.model,
                    "skipped": "circuit_open",
                }
            )
            continue

        rpm = provider.limits.get("rpm")
        if not resilience.token_bucket_allow(step.provider, limit=rpm):
            attempts.append(
                {
                    "provider": step.provider,
                    "model": step.model,
                    "skipped": "rate_bucket_exhausted",
                }
            )
            continue

        if use_cache:
            cached = resilience.get_cached_response(
                step.provider, step.model, original_redacted_messages
            )
            if cached is not None:
                attempts.append(
                    {"provider": step.provider, "model": step.model, "cache_hit": True}
                )
                _log_agent_run(
                    session,
                    agent_name=agent_name,
                    task_class=task_class,
                    provider=step.provider,
                    model=step.model,
                    input_text=str(original_redacted_messages),
                    tokens_in=cached.get("tokens_in"),
                    tokens_out=cached.get("tokens_out"),
                    latency_ms=0,
                    status="ok_cached",
                )
                parsed = None
                if response_schema:
                    validation = validate_json_response(
                        cached["content"], response_schema
                    )
                    parsed = validation.parsed
                return GatewayResult(
                    "ok",
                    cached["content"],
                    parsed,
                    step.provider,
                    step.model,
                    token_map,
                    attempts,
                )

        result = _call_with_retry(
            provider,
            step.model,
            original_redacted_messages,
            attempts,
            json_mode=response_schema is not None,
        )
        if result is None:
            continue  # exhausted this provider's retries; try the next one in the chain

        if response_schema:
            validation = validate_json_response(result.content, response_schema)
            if not validation.ok:
                repair_messages = build_repair_prompt(
                    original_redacted_messages,
                    result.content,
                    validation.error,
                    response_schema,
                )
                repair_result = _call_with_retry(
                    provider,
                    step.model,
                    repair_messages,
                    attempts,
                    json_mode=True,
                    label="repair",
                )
                if repair_result is not None:
                    repair_validation = validate_json_response(
                        repair_result.content, response_schema
                    )
                    if repair_validation.ok:
                        result = repair_result
                        validation = repair_validation
                if not validation.ok:
                    attempts.append(
                        {
                            "provider": step.provider,
                            "model": step.model,
                            "schema_invalid": True,
                        }
                    )
                    resilience.record_failure(step.provider)
                    continue  # cross-provider re-ask: try the next provider in the chain
            parsed = validation.parsed
        else:
            parsed = None

        resilience.record_success(step.provider)
        if use_cache:
            resilience.set_cached_response(
                step.provider,
                step.model,
                original_redacted_messages,
                {
                    "content": result.content,
                    "tokens_in": result.tokens_in,
                    "tokens_out": result.tokens_out,
                },
            )
        _log_agent_run(
            session,
            agent_name=agent_name,
            task_class=task_class,
            provider=step.provider,
            model=step.model,
            input_text=str(original_redacted_messages),
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            latency_ms=result.latency_ms,
            status="ok",
        )
        return GatewayResult(
            "ok", result.content, parsed, step.provider, step.model, token_map, attempts
        )

    # Every provider in the chain failed or was skipped — fail-closed to
    # the human review queue rather than returning a guessed/empty answer.
    _log_agent_run(
        session,
        agent_name=agent_name,
        task_class=task_class,
        provider=None,
        model=None,
        input_text=str(original_redacted_messages),
        tokens_in=None,
        tokens_out=None,
        latency_ms=None,
        status="human_review_required",
    )
    return GatewayResult(
        "human_review_required", None, None, None, None, token_map, attempts
    )


def _call_with_retry(
    provider,
    model_id: str,
    messages: list[dict],
    attempts: list[dict],
    *,
    json_mode: bool = False,
    max_retries: int = 2,
    label: str = "call",
):
    for attempt in range(max_retries + 1):
        try:
            result = call_chat_completion(
                provider, model_id, messages, json_mode=json_mode
            )
            attempts.append(
                {
                    "provider": provider.name,
                    "model": model_id,
                    label: True,
                    "attempt": attempt,
                }
            )
            return result
        except resilience.RateLimitedError as exc:
            wait = min(exc.retry_after_seconds, 10.0)
            attempts.append(
                {
                    "provider": provider.name,
                    "model": model_id,
                    "rate_limited": True,
                    "retry_after": wait,
                }
            )
            time.sleep(wait)
        except ProviderAuthError as exc:
            attempts.append(
                {
                    "provider": provider.name,
                    "model": model_id,
                    "auth_error": str(exc),
                    "attempt": attempt,
                }
            )
            resilience.record_failure(provider.name)
            # Permanent key/credential error: do not retry this provider; failover to next provider immediately
            break
        except ProviderCallError as exc:
            attempts.append(
                {
                    "provider": provider.name,
                    "model": model_id,
                    "error": str(exc),
                    "attempt": attempt,
                }
            )
            resilience.record_failure(provider.name)
            if attempt < max_retries:
                time.sleep(resilience.backoff_with_jitter(attempt))
    return None
