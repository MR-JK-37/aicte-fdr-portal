.PHONY: all help api-dev api-test api-lint migrate openapi verify test lint audit-verify

SHELL := /bin/bash
UV ?= $(HOME)/.local/bin/uv

all: verify

help:
	@echo "AICTE Security Deposit / FDR Portal — Build & Verification Tasks"
	@echo ""
	@echo "Targets:"
	@echo "  api-dev       Start FastAPI development server"
	@echo "  api-test      Run backend test suite with pytest"
	@echo "  api-lint      Run ruff check and format check on backend"
	@echo "  migrate       Run Alembic database migrations"
	@echo "  openapi       Export OpenAPI specification to packages/api-client/openapi.json"
	@echo "  audit-verify  Run the Ed25519 audit chain integrity verifier script"
	@echo "  verify        Run all verification gates (lint, tests, prod guard, audit chain)"

api-dev:
	cd services/api && $(UV) run uvicorn app.main:app --reload --port 8000

api-test:
	cd services/api && $(UV) run pytest

api-lint:
	cd services/api && $(UV) run ruff check .

migrate:
	cd services/api && $(UV) run alembic upgrade head

openapi:
	cd services/api && $(UV) run python -c "import json; from app.main import app; open('../../packages/api-client/openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"
	@echo "OpenAPI schema written to packages/api-client/openapi.json"

audit-verify:
	cd services/api && $(UV) run python ../../scripts/verify_audit_chain.py

lint: api-lint
	pnpm -r lint

test: api-test
	pnpm -r test

verify:
	@echo "==> Running backend linting..."
	cd services/api && $(UV) run ruff check .
	@echo "==> Running backend test suite..."
	cd services/api && $(UV) run pytest
	@echo "==> Running frontend workspace packages build & tests..."
	pnpm -r build
	pnpm -r test
	@echo "==> Running production guard verification..."
	cd services/api && $(UV) run pytest tests/test_prod_guard.py
	@echo "==> Running audit chain verifier..."
	cd services/api && $(UV) run python ../../scripts/verify_audit_chain.py
	@echo "========================================================"
	@echo "ALL GATES GREEN (Phase 1 Platform verification complete)"
	@echo "========================================================"
