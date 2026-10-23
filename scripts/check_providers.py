#!/usr/bin/env python3
"""Validates configured LLM provider keys, discovers live model IDs
(never trusting the registry's static `models` list as fact), and prints
remaining-quota info where a provider exposes it. Run from services/api:

    uv run python ../../scripts/check_providers.py

Per the brief: "never hard-code unverified IDs" — this is the tool that
makes config/llm_providers.yaml's `verified` flags true, not a guess.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "services" / "api"))

import httpx  # noqa: E402

from app.llm_gateway.registry import load_registry  # noqa: E402


def check_provider(name: str, provider) -> dict:
    result = {"provider": name, "has_key": provider.has_key, "reachable": False, "models": [], "note": provider.note}

    if not provider.has_key:
        result["status"] = "NO KEY CONFIGURED"
        return result

    if not provider.model_list_endpoint:
        result["status"] = "has key, but no model-list endpoint configured to verify against"
        return result

    try:
        resp = httpx.get(
            f"{provider.base_url}{provider.model_list_endpoint}",
            headers={"Authorization": f"Bearer {provider.api_key}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        model_ids = [m.get("id") for m in data.get("data", [])]
        result["reachable"] = True
        result["models"] = model_ids
        result["status"] = f"OK — {len(model_ids)} models discovered live"
    except httpx.HTTPError as exc:
        result["status"] = f"UNREACHABLE/ERROR: {exc}"

    return result


def main() -> int:
    registry = load_registry()
    print(f"{'PROVIDER':<24}{'KEY':<8}{'STATUS'}")
    print("-" * 90)
    any_unverified_but_keyed = False
    for name, provider in sorted(registry.items()):
        result = check_provider(name, provider)
        key_marker = "yes" if result["has_key"] else "no"
        print(f"{name:<24}{key_marker:<8}{result['status']}")
        if result["models"]:
            for model_id in result["models"]:
                print(f"    - {model_id}")
        if result["reachable"] and not provider.verified:
            any_unverified_but_keyed = True

    print()
    if any_unverified_but_keyed:
        print("NOTE: one or more providers have a key but config/llm_providers.yaml still")
        print("marks them unverified — update that file's `verified`/`models`/`limits` from")
        print("this run's output before relying on them for routing decisions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
