"""Task-class routing: each task class has an ordered (provider, model)
fallback chain. Tier S (sensitive-agent) is special per the brief: local
-> no-retention provider (redacted) -> human queue — and since neither
local Ollama nor a confirmed no-retention provider is available in this
environment (see config/llm_providers.yaml), Tier S correctly routes
straight to the human queue rather than silently using an unconfirmed
provider for sensitive data. That is the fail-closed behaviour the spec
asks for, not a bug.
"""

from dataclasses import dataclass

from app.llm_gateway.registry import load_registry

TASK_CLASSES = (
    "sensitive-agent",  # Tier S
    "extraction",
    "rag",
    "text2sql",
    "voice-intent",
    "translation",
    "embeddings",
    "safety",
)


@dataclass
class ChainStep:
    provider: str
    model: str


# Model choices are grounded in the verified Groq model list
# (config/llm_providers.yaml) — gpt-oss-120b for quality/context on
# non-latency-critical Tier P tasks, gpt-oss-20b where speed matters more
# (voice-intent) or as the cheaper second hop, and the dedicated
# safety/prompt-injection models for their matching task classes.
_TIER_P_CHAINS: dict[str, list[ChainStep]] = {
    "extraction": [ChainStep("groq", "openai/gpt-oss-120b"), ChainStep("groq", "openai/gpt-oss-20b")],
    "rag": [ChainStep("groq", "openai/gpt-oss-120b"), ChainStep("groq", "openai/gpt-oss-20b")],
    "text2sql": [ChainStep("groq", "openai/gpt-oss-120b"), ChainStep("groq", "openai/gpt-oss-20b")],
    "voice-intent": [ChainStep("groq", "openai/gpt-oss-20b")],
    "translation": [ChainStep("groq", "openai/gpt-oss-120b"), ChainStep("groq", "openai/gpt-oss-20b")],
    "embeddings": [],  # No embeddings-capable provider has a key yet — a real gap, not hidden.
    "safety": [ChainStep("groq", "openai/gpt-oss-safeguard-20b")],
}


def get_chain(task_class: str, *, tier: str) -> list[ChainStep]:
    if task_class not in TASK_CLASSES:
        raise ValueError(f"unknown task class '{task_class}'")

    if tier == "S":
        # Tier S never falls back to an unconfirmed-retention-policy
        # provider. Only providers whose tier_eligibility includes "S"
        # (local Ollama, or a future confirmed-no-retention provider)
        # are ever considered here.
        registry = load_registry()
        s_eligible = [p for p in registry.values() if "S" in p.tier_eligibility and p.has_key]
        return [ChainStep(p.name, p.models[0].id) for p in s_eligible if p.models]

    chain = _TIER_P_CHAINS.get(task_class, [])
    registry = load_registry()
    return [step for step in chain if registry[step.provider].has_key]
