import uuid

from app.llm_gateway import resilience


def _unique_provider() -> str:
    return f"test-provider-{uuid.uuid4().hex[:8]}"


def test_token_bucket_allows_up_to_limit_then_blocks():
    provider = _unique_provider()
    assert resilience.token_bucket_allow(provider, limit=3) is True
    assert resilience.token_bucket_allow(provider, limit=3) is True
    assert resilience.token_bucket_allow(provider, limit=3) is True
    assert resilience.token_bucket_allow(provider, limit=3) is False


def test_token_bucket_none_limit_always_allows():
    provider = _unique_provider()
    for _ in range(10):
        assert resilience.token_bucket_allow(provider, limit=None) is True


def test_circuit_opens_after_threshold_failures():
    provider = _unique_provider()
    assert resilience.is_circuit_open(provider) is False
    resilience.record_failure(provider)
    resilience.record_failure(provider)
    assert resilience.is_circuit_open(provider) is False  # below threshold (3)
    resilience.record_failure(provider)
    assert resilience.is_circuit_open(provider) is True


def test_circuit_closes_on_success():
    provider = _unique_provider()
    resilience.record_failure(provider)
    resilience.record_failure(provider)
    resilience.record_failure(provider)
    assert resilience.is_circuit_open(provider) is True
    resilience.record_success(provider)
    assert resilience.is_circuit_open(provider) is False


def test_cache_round_trip():
    provider = _unique_provider()
    messages = [{"role": "user", "content": "hello"}]
    assert resilience.get_cached_response(provider, "model-a", messages) is None
    resilience.set_cached_response(
        provider, "model-a", messages, {"content": "hi there"}
    )
    cached = resilience.get_cached_response(provider, "model-a", messages)
    assert cached == {"content": "hi there"}


def test_cache_key_is_sensitive_to_messages_content():
    provider = _unique_provider()
    resilience.set_cached_response(
        provider, "model-a", [{"role": "user", "content": "A"}], {"content": "x"}
    )
    assert (
        resilience.get_cached_response(
            provider, "model-a", [{"role": "user", "content": "B"}]
        )
        is None
    )


def test_backoff_with_jitter_increases_with_attempt_and_is_capped():
    low = [
        resilience.backoff_with_jitter(0, base_seconds=0.1, max_seconds=5.0)
        for _ in range(20)
    ]
    high = [
        resilience.backoff_with_jitter(10, base_seconds=0.1, max_seconds=5.0)
        for _ in range(20)
    ]
    assert max(low) <= 0.2
    assert max(high) <= 5.0
    assert all(v >= 0 for v in low + high)
