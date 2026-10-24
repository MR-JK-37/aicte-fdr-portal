from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.llm_gateway.client import ProviderCallError, call_chat_completion
from app.llm_gateway.registry import ProviderSpec
from app.llm_gateway.resilience import RateLimitedError


def _provider(**overrides) -> ProviderSpec:
    defaults = {
        "name": "test",
        "verified": True,
        "base_url": "https://example.test/v1",
        "openai_compatible": True,
        "key_env_var": "TEST_PROVIDER_KEY",
        "model_list_endpoint": "/models",
        "models": [],
        "limits": {},
        "data_policy": {},
        "tier_eligibility": ["P"],
    }
    defaults.update(overrides)
    return ProviderSpec(**defaults)


@pytest.fixture(autouse=True)
def _has_key(monkeypatch):
    monkeypatch.setenv("TEST_PROVIDER_KEY", "fake-key-for-tests")


def test_successful_completion_parses_content_and_usage():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "hello world"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 2},
    }
    with patch("app.llm_gateway.client.httpx.post", return_value=mock_response):
        result = call_chat_completion(
            _provider(), "model-a", [{"role": "user", "content": "hi"}]
        )
    assert result.content == "hello world"
    assert result.tokens_in == 10
    assert result.tokens_out == 2


def test_429_raises_rate_limited_with_retry_after_header():
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {"Retry-After": "7"}
    with (
        patch("app.llm_gateway.client.httpx.post", return_value=mock_response),
        pytest.raises(RateLimitedError) as exc_info,
    ):
        call_chat_completion(
            _provider(), "model-a", [{"role": "user", "content": "hi"}]
        )
    assert exc_info.value.retry_after_seconds == 7.0


def test_429_without_retry_after_header_defaults_to_one_second():
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {}
    with (
        patch("app.llm_gateway.client.httpx.post", return_value=mock_response),
        pytest.raises(RateLimitedError) as exc_info,
    ):
        call_chat_completion(
            _provider(), "model-a", [{"role": "user", "content": "hi"}]
        )
    assert exc_info.value.retry_after_seconds == 1.0


def test_server_error_raises_provider_call_error():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "internal error"
    with (
        patch("app.llm_gateway.client.httpx.post", return_value=mock_response),
        pytest.raises(ProviderCallError),
    ):
        call_chat_completion(
            _provider(), "model-a", [{"role": "user", "content": "hi"}]
        )


def test_network_error_raises_provider_call_error():
    with (
        patch(
            "app.llm_gateway.client.httpx.post", side_effect=httpx.ConnectError("boom")
        ),
        pytest.raises(ProviderCallError),
    ):
        call_chat_completion(
            _provider(), "model-a", [{"role": "user", "content": "hi"}]
        )


def test_missing_key_raises_before_any_request(monkeypatch):
    monkeypatch.delenv("TEST_PROVIDER_KEY", raising=False)
    with pytest.raises(ProviderCallError, match="no API key"):
        call_chat_completion(
            _provider(), "model-a", [{"role": "user", "content": "hi"}]
        )


def test_non_openai_compatible_provider_rejected():
    with pytest.raises(ProviderCallError, match="not OpenAI-compatible"):
        call_chat_completion(
            _provider(openai_compatible=False),
            "model-a",
            [{"role": "user", "content": "hi"}],
        )
