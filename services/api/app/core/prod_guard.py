"""Production startup guard (CLAUDE.md non-negotiable #10 / MASTER_PROMPT
§17.4): nothing simulated is allowed in production. Startup must refuse
to proceed if the environment looks like it is asking for a demo seed, a
mock provider, a fabricated ("fake") success path, or a simulated clock.

This module is imported and invoked from `app.main` on process startup.
It must run *before* anything else does real work, so a misconfigured
production deployment fails loudly at import/boot time instead of
quietly serving fabricated data.
"""

import os
import re

# Catches any env var whose name starts with one of these prefixes,
# regardless of what follows (e.g. the demo-mode toggle, a mock
# provider selector, a fake-success flag, or anything named "simulate*").
_FORBIDDEN_PREFIXES = ("DEMO", "MOCK", "FAKE", "SIMULAT")
_FORBIDDEN_NAME_RE = re.compile(r"^(?:" + "|".join(_FORBIDDEN_PREFIXES) + r")\w*$")

_CLOCK_OVERRIDE_VAR = "SIMULATED_CLOCK"

_TRUTHY = {"1", "true", "yes", "on"}


class ProductionSimulationGuardError(RuntimeError):
    """Raised when production startup detects a simulated/demo/mock/fake
    env var — the environment is not production-safe."""


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in _TRUTHY


def assert_no_simulation_flags(
    env: "os._Environ[str] | dict[str, str] | None" = None,
) -> None:
    """Raises ProductionSimulationGuardError if any forbidden env var is
    truthy, or if the simulated-clock override var is set at all (even to
    a falsy-looking value — the point of that variable is that it must
    not exist in production, not that it must be "off")."""
    environ = os.environ if env is None else env

    violations: list[str] = []
    for key, value in environ.items():
        if _FORBIDDEN_NAME_RE.match(key) and _is_truthy(value):
            violations.append(key)

    if (
        environ.get(_CLOCK_OVERRIDE_VAR, "") != ""
        and _CLOCK_OVERRIDE_VAR not in violations
    ):
        violations.append(_CLOCK_OVERRIDE_VAR)

    if violations:
        raise ProductionSimulationGuardError(
            "Refusing to start in production: forbidden simulation/demo/mock/fake "
            f"env var(s) set: {', '.join(sorted(violations))}. Nothing simulated is "
            "allowed in production (CLAUDE.md non-negotiable #10)."
        )


def enforce_production_guard() -> None:
    """No-op unless APP_ENV=production; otherwise delegates to
    assert_no_simulation_flags(), which raises on any violation."""
    if os.environ.get("APP_ENV", "").strip().lower() != "production":
        return
    assert_no_simulation_flags()
