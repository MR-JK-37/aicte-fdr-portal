"""CLAUDE.md non-negotiable #10 / MASTER_PROMPT §17.4: production startup
must refuse to proceed if the environment asks for anything simulated.

These tests exercise app.core.prod_guard directly (unit-level, one env
var at a time) and then prove the same thing at the level the brief
actually cares about: importing app.main with APP_ENV=production and a
forbidden var set must raise, not start a server.
"""

import importlib
import sys

import pytest

from app.core.prod_guard import (
    ProductionSimulationGuardError,
    assert_no_simulation_flags,
    enforce_production_guard,
)

FORBIDDEN_TRUTHY_VARS = [
    "DEMO_MODE",
    "MOCK_BANK_PROVIDER",
    "FAKE_PUSH_SUCCESS",
    "SIMULATE_ANYTHING",
]


@pytest.mark.parametrize("var_name", FORBIDDEN_TRUTHY_VARS)
def test_truthy_forbidden_var_is_rejected(var_name):
    with pytest.raises(ProductionSimulationGuardError):
        assert_no_simulation_flags({var_name: "true"})


@pytest.mark.parametrize("var_name", FORBIDDEN_TRUTHY_VARS)
def test_falsy_forbidden_var_is_allowed(var_name):
    assert_no_simulation_flags({var_name: "false"})  # does not raise


def test_simulated_clock_override_is_rejected_even_if_falsy():
    # The point of this one is that it must not exist in production at
    # all — "false" still means someone wired up a simulated-clock
    # override, which is itself the violation.
    with pytest.raises(ProductionSimulationGuardError):
        assert_no_simulation_flags({"SIMULATED_CLOCK": "false"})


def test_clean_environment_passes():
    assert_no_simulation_flags(
        {"APP_ENV": "production", "DATABASE_URL": "postgresql://x"}
    )  # does not raise


def test_enforce_production_guard_is_a_noop_outside_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("DEMO_MODE", "true")
    enforce_production_guard()  # must not raise — not production


def test_enforce_production_guard_raises_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("MOCK_BANK_PROVIDER", "1")
    with pytest.raises(ProductionSimulationGuardError):
        enforce_production_guard()


@pytest.mark.parametrize(
    "var_name,value",
    [(v, "true") for v in FORBIDDEN_TRUTHY_VARS] + [("SIMULATED_CLOCK", "1")],
)
def test_importing_app_main_in_production_refuses_to_start(
    monkeypatch, var_name, value
):
    """The real acceptance test: a production boot with a forbidden flag
    set must fail at import time, not serve traffic."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(var_name, value)
    sys.modules.pop("app.main", None)
    try:
        with pytest.raises(ProductionSimulationGuardError):
            importlib.import_module("app.main")
    finally:
        sys.modules.pop("app.main", None)
