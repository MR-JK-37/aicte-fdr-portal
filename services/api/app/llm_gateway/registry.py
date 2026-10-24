"""Loads config/llm_providers.yaml into typed objects. See that file's
header for what "verified: false" means — do not treat an unverified
entry's `models` list as fact; it exists to be overwritten by
scripts/check_providers.py once a key is supplied.
"""

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "llm_providers.yaml"
)


@dataclass
class ModelSpec:
    id: str
    context_window: int | None = None
    max_output_tokens: int | None = None
    capabilities: dict = field(default_factory=dict)
    role: str | None = None


@dataclass
class ProviderSpec:
    name: str
    verified: bool
    base_url: str
    openai_compatible: bool
    key_env_var: str | None
    model_list_endpoint: str | None
    models: list[ModelSpec]
    limits: dict
    data_policy: dict
    tier_eligibility: list[str]
    note: str | None = None

    @property
    def api_key(self) -> str | None:
        if self.key_env_var is None:
            return None
        return os.environ.get(self.key_env_var)

    @property
    def has_key(self) -> bool:
        return self.key_env_var is None or bool(self.api_key)

    def model(self, model_id: str) -> ModelSpec | None:
        return next((m for m in self.models if m.id == model_id), None)


@lru_cache
def load_registry() -> dict[str, ProviderSpec]:
    with open(CONFIG_PATH) as f:
        raw = yaml.safe_load(f)
    registry = {}
    for name, entry in raw["providers"].items():
        models = [ModelSpec(**m) for m in entry.get("models", [])]
        registry[name] = ProviderSpec(
            name=name,
            verified=entry.get("verified", False),
            base_url=entry["base_url"],
            openai_compatible=entry.get("openai_compatible", True),
            key_env_var=entry.get("key_env_var"),
            model_list_endpoint=entry.get("model_list_endpoint"),
            models=models,
            limits=entry.get("limits", {}),
            data_policy=entry.get("data_policy", {}),
            tier_eligibility=entry.get("tier_eligibility", []),
            note=entry.get("note"),
        )
    return registry


def providers_with_keys() -> list[ProviderSpec]:
    """Providers that actually have a usable key in this environment —
    the set routing can consider right now, as opposed to the full
    registry (which includes documented-but-unconfigured providers)."""
    return [p for p in load_registry().values() if p.has_key]
