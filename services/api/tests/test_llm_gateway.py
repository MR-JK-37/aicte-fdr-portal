import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
import redis
from pydantic import BaseModel
from sqlalchemy import select

from app.llm_gateway.gateway import generate
from app.llm_gateway.registry import load_registry
from app.models.audit import AgentRun
from tests.conftest import VALKEY_URL


class ToyFields(BaseModel):
    name: str
    amount: int


# Captured before the autouse _groq_key fixture below ever overwrites
# GROQ_API_KEY with a fake value — the live test needs the real one back.
_REAL_GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


@pytest.fixture(autouse=True)
def _groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key-for-gateway-tests")


@pytest.fixture(autouse=True)
def _reset_llm_gateway_state_per_test():
    """Function-scoped, unlike the session-scoped DB/Valkey reset in
    conftest.py: tests in this file (e.g. the circuit-breaker test)
    deliberately put "groq"'s circuit/token-bucket state into a tripped
    condition, which must not leak into the next test in the same run —
    the 60s circuit-open TTL comfortably outlives the milliseconds
    between two tests. This is exactly what caused two tests here to
    fail with zero HTTP calls made despite fresh, unique request
    content: not stale state from an old process, but from an earlier
    test *in the same run* that never cleaned up after itself."""
    client = redis.Redis.from_url(VALKEY_URL)
    for key in client.scan_iter("llm_*"):
        client.delete(key)
    client.close()
    yield


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    # These tests exercise retry/backoff/rate-limit paths; they must not
    # actually wait in real time.
    monkeypatch.setattr("app.llm_gateway.gateway.time.sleep", lambda *_: None)


def _mock_response(status_code=200, json_body=None, headers=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {}
    resp.headers = headers or {}
    resp.text = text
    return resp


def _chat_json(content_str: str, tokens_in=10, tokens_out=5):
    return {
        "choices": [{"message": {"content": content_str}}],
        "usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out},
    }


def test_successful_call_returns_parsed_schema_and_logs_agent_run(db_session):
    good = _mock_response(200, _chat_json('{"name": "FDR001", "amount": 5}'))
    with patch("app.llm_gateway.client.httpx.post", return_value=good) as mock_post:
        result = generate(
            "extraction",
            [{"role": "user", "content": "extract fields"}],
            response_schema=ToyFields,
            agent_name="test-agent",
            session=db_session,
            use_cache=False,
        )
    assert mock_post.call_count == 1
    assert result.status == "ok"
    assert result.parsed.name == "FDR001"
    assert result.provider == "groq"

    run = (
        db_session.execute(select(AgentRun).where(AgentRun.agent_name == "test-agent"))
        .scalars()
        .first()
    )
    assert run is not None
    assert run.status == "ok"
    assert run.tokens_in == 10


def test_sensitive_agent_with_no_s_provider_goes_to_human_review(db_session):
    with patch("app.llm_gateway.client.httpx.post") as mock_post:
        result = generate(
            "sensitive-agent",
            [{"role": "user", "content": "do something sensitive"}],
            tier="S",
            agent_name="test-agent-sensitive",
            session=db_session,
        )
    mock_post.assert_not_called()
    assert result.status == "human_review_required"

    run = (
        db_session.execute(
            select(AgentRun).where(AgentRun.agent_name == "test-agent-sensitive")
        )
        .scalars()
        .first()
    )
    assert run.status == "human_review_required"


def test_malformed_json_triggers_repair_retry_then_succeeds(db_session):
    bad = _mock_response(200, _chat_json("not valid json at all"))
    good = _mock_response(200, _chat_json('{"name": "FDR002", "amount": 7}'))
    with patch(
        "app.llm_gateway.client.httpx.post", side_effect=[bad, good]
    ) as mock_post:
        result = generate(
            "extraction",
            [{"role": "user", "content": "extract fields"}],
            response_schema=ToyFields,
            agent_name="test-repair",
            session=db_session,
            use_cache=False,
        )
    assert mock_post.call_count == 2
    assert result.status == "ok"
    assert result.parsed.amount == 7


def test_persistent_malformed_json_falls_through_to_human_review(db_session):
    always_bad = _mock_response(200, _chat_json("still not json"))
    with patch("app.llm_gateway.client.httpx.post", return_value=always_bad):
        result = generate(
            "extraction",
            [{"role": "user", "content": "extract fields"}],
            response_schema=ToyFields,
            agent_name="test-always-bad",
            session=db_session,
            use_cache=False,
        )
    # Every provider in the chain exhausted (repair didn't fix it, no
    # further provider configured) -> fail-closed, not a guessed answer.
    assert result.status == "human_review_required"


def test_rate_limit_storm_honours_retry_after_then_eventually_queues(db_session):
    rate_limited = _mock_response(429, headers={"Retry-After": "2"})
    with patch(
        "app.llm_gateway.client.httpx.post", return_value=rate_limited
    ) as mock_post:
        # voice-intent's chain has exactly one (provider, model) step, so
        # the call count below isolates the per-provider retry count from
        # chain depth (extraction's 2-step chain would double it).
        result = generate(
            "voice-intent",
            [{"role": "user", "content": "extract fields"}],
            agent_name="test-ratelimit",
            session=db_session,
            use_cache=False,
        )
    # max_retries=2 -> 3 attempts against the one available model before
    # giving up on that provider; no other provider configured -> queued.
    assert mock_post.call_count == 3
    assert result.status == "human_review_required"


def test_circuit_breaker_skips_provider_after_repeated_failures(db_session):
    server_error = _mock_response(500, text="boom")
    with patch("app.llm_gateway.client.httpx.post", return_value=server_error):
        # Each generate() call retries up to 3 times against the single
        # chain step; three separate calls (>=3 recorded failures) should
        # trip the circuit breaker.
        for _ in range(3):
            generate(
                "extraction",
                [{"role": "user", "content": "x"}],
                agent_name="test-circuit",
                session=db_session,
                use_cache=False,
            )

    with patch(
        "app.llm_gateway.client.httpx.post", return_value=server_error
    ) as mock_post:
        result = generate(
            "extraction",
            [{"role": "user", "content": "x"}],
            agent_name="test-circuit",
            session=db_session,
            use_cache=False,
        )
    assert mock_post.call_count == 0  # circuit open: never even attempted
    assert result.status == "human_review_required"


def test_cache_hit_avoids_a_second_network_call(db_session):
    good = _mock_response(200, _chat_json('{"name": "FDR003", "amount": 1}'))
    messages = [{"role": "user", "content": f"extract fields {uuid.uuid4()}"}]
    with patch("app.llm_gateway.client.httpx.post", return_value=good) as mock_post:
        first = generate(
            "extraction", messages, response_schema=ToyFields, session=db_session
        )
    assert mock_post.call_count == 1
    assert first.status == "ok"

    with patch(
        "app.llm_gateway.client.httpx.post", return_value=good
    ) as mock_post_second:
        second = generate(
            "extraction", messages, response_schema=ToyFields, session=db_session
        )
    mock_post_second.assert_not_called()
    assert second.status == "ok"
    assert second.parsed.name == "FDR003"


def test_pii_in_user_message_is_redacted_before_leaving_the_process(db_session):
    good = _mock_response(200, _chat_json('{"name": "FDR004", "amount": 1}'))
    sensitive = "Contact 9876543210 regarding IFSC SBIN0001234."
    with patch("app.llm_gateway.client.httpx.post", return_value=good) as mock_post:
        generate(
            "extraction",
            [{"role": "user", "content": sensitive}],
            response_schema=ToyFields,
            session=db_session,
            use_cache=False,
        )
    sent_payload = mock_post.call_args.kwargs["json"]
    sent_text = str(sent_payload["messages"])
    assert "9876543210" not in sent_text
    assert "SBIN0001234" not in sent_text


@pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY_LIVE_TEST"),
    reason="set GROQ_API_KEY_LIVE_TEST=1 to hit the real Groq API",
)
def test_live_groq_call_end_to_end(monkeypatch):
    """Not mocked: a real call to the real Groq API with this session's
    actual key, proving the gateway works against a live provider, not
    just mocks. Opt-in via GROQ_API_KEY_LIVE_TEST=1 so normal test runs
    (and CI without that flag) don't depend on network/quota."""
    assert _REAL_GROQ_API_KEY, (
        "GROQ_API_KEY_LIVE_TEST=1 was set but no real GROQ_API_KEY was found in the environment"
    )
    monkeypatch.setenv(
        "GROQ_API_KEY", _REAL_GROQ_API_KEY
    )  # undo the file's autouse fake-key fixture for this test
    load_registry.cache_clear()
    result = generate(
        "voice-intent",
        [{"role": "user", "content": "Reply with exactly the word: OK"}],
        use_cache=False,
    )
    assert result.status == "ok"
    assert result.provider == "groq"
    assert result.content
