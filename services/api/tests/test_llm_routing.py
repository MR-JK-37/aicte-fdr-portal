import pytest

from app.llm_gateway.routing import get_chain


def test_extraction_tier_p_returns_groq_steps(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    chain = get_chain("extraction", tier="P")
    assert len(chain) >= 1
    assert all(step.provider == "groq" for step in chain)


def test_extraction_tier_p_empty_without_any_keyed_provider(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    chain = get_chain("extraction", tier="P")
    assert chain == []


def test_sensitive_agent_tier_s_is_empty_without_a_confirmed_s_provider(monkeypatch):
    # Groq is Tier P only (unconfirmed retention policy) — Tier S must
    # never silently fall back to it. Ensure no accidental S eligibility.
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    chain = get_chain("sensitive-agent", tier="S")
    assert all(step.provider != "groq" for step in chain)


def test_embeddings_chain_is_empty_known_gap(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    assert get_chain("embeddings", tier="P") == []


def test_unknown_task_class_raises():
    with pytest.raises(ValueError, match="unknown task class"):
        get_chain("not-a-real-task-class", tier="P")
