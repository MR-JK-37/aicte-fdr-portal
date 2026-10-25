from app.llm_gateway.registry import load_registry, providers_with_keys


def test_groq_is_registered_and_verified():
    registry = load_registry()
    assert "groq" in registry
    assert registry["groq"].verified is True
    assert registry["groq"].openai_compatible is True


def test_groq_has_the_live_discovered_models():
    registry = load_registry()
    model_ids = {m.id for m in registry["groq"].models}
    assert "openai/gpt-oss-120b" in model_ids
    assert "openai/gpt-oss-20b" in model_ids


def test_openrouter_is_registered_and_verified():
    registry = load_registry()
    assert "openrouter" in registry
    assert registry["openrouter"].verified is True
    assert registry["openrouter"].openai_compatible is True


def test_unverified_providers_have_empty_model_lists():
    registry = load_registry()
    for name, provider in registry.items():
        if name in ("groq", "ollama_local", "openrouter"):
            continue
        assert provider.verified is False
        assert provider.models == [], f"{name} is unverified but has hard-coded models"


def test_gemini_is_tier_p_only():
    registry = load_registry()
    assert registry["gemini"].tier_eligibility == ["P"]


def test_providers_with_keys_reflects_environment(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    names = {p.name for p in providers_with_keys()}
    assert "groq" not in names
    assert "ollama_local" in names  # no key required

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    names = {p.name for p in providers_with_keys()}
    assert "groq" in names
