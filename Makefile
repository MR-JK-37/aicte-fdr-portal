.PHONY: all help api-dev api-test api-test-slow api-lint migrate openapi verify test lint audit-verify dev dev-stop mobile-doctor forbidden-strings redeploy smoke-test

SHELL := /bin/bash
UV ?= $(HOME)/.local/bin/uv
COMPOSE := docker compose -f infra/docker/docker-compose.yml

all: verify

help:
	@echo "AICTE Security Deposit / FDR Portal — Build & Verification Tasks"
	@echo ""
	@echo "Targets:"
	@echo "  dev           Start infra (docker compose) + web (:3000) + mobile (:8082); API already runs as a long-lived dev process on :8000"
	@echo "  dev-stop      Stop the docker compose infra stack"
	@echo "  api-dev       Start FastAPI development server directly (no docker)"
	@echo "  api-test      Run backend test suite with pytest (excludes @pytest.mark.slow)"
	@echo "  api-test-slow Run only the @pytest.mark.slow tests (real OCR benchmark, ~5min)"
	@echo "  api-lint      Run ruff check and format check on backend"
	@echo "  migrate       Run Alembic database migrations"
	@echo "  openapi       Export OpenAPI specification to packages/api-client/openapi.json"
	@echo "  audit-verify  Run the Ed25519 audit chain integrity verifier script"
	@echo "  verify        Run all verification gates (lint, tests, prod guard, audit chain)"
	@echo "  mobile-doctor Run expo-doctor against apps/mobile"
	@echo "  redeploy      Rebuild + restart the live api/worker/migrate containers from current source"
	@echo "  smoke-test    Hit the LIVE :8000 and confirm it matches source (catches stale-deployment drift — see docs/phase-reports/R2-mobile-ui.md)"
	@echo "  seed-staging  Seed synthetic staging users and institutions into database (AUTH §4)"

dev:
	$(COMPOSE) up -d db valkey garage clamav keycloak migrate mailpit
	@echo "------------------------------------------------------------------"
	@echo " Infra up. Start these in separate terminals (not backgrounded by"
	@echo " this target, so you see their logs):"
	@echo "   API      : make api-dev                 -> http://localhost:8000/docs"
	@echo "   Web      : pnpm --filter web dev         -> http://localhost:3000"
	@echo "   Mobile   : pnpm --filter mobile start --port 8082  -> http://localhost:8082 (scan QR for Expo Go/LAN)"
	@echo "------------------------------------------------------------------"

dev-stop:
	$(COMPOSE) down

# Rebuilds AND restarts api/worker/migrate from current source. Each has its own
# image despite sharing a Dockerfile (docker compose build api worker alone
# silently leaves migrate on a stale image — this is exactly what bit R2.5,
# see docs/phase-reports/R2-mobile-ui.md). Run this, then `make smoke-test`,
# after any backend change if the live containers are how you're testing —
# `uv run pytest` passing does NOT mean the deployed container matches source.
redeploy:
	$(COMPOSE) build api worker migrate
	$(COMPOSE) up -d api worker migrate
	@echo "Redeployed. Run 'make smoke-test' to confirm the live API now matches source."

smoke-test:
	bash scripts/smoke_test_live_api.sh

seed-staging:
	cd services/api && $(UV) run python ../../scripts/seed_staging.py

api-dev:
	cd services/api && $(UV) run uvicorn app.main:app --reload --port 8000

api-test:
	cd services/api && $(UV) run pytest -m "not slow"

api-test-slow:
	cd services/api && $(UV) run pytest -m "slow" -v

api-lint:
	cd services/api && $(UV) run ruff check .

mobile-doctor:
	cd apps/mobile && npx expo-doctor

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

forbidden-strings:
	node scripts/forbidden-strings.mjs apps/web/src apps/mobile services/api/app

verify:
	@echo "==> Running backend linting..."
	cd services/api && $(UV) run ruff check .
	@echo "==> Running backend test suite (excludes @pytest.mark.slow — run 'make api-test-slow' separately)..."
	cd services/api && $(UV) run pytest -m "not slow"
	@echo "==> Running frontend workspace packages build & tests..."
	pnpm -r build
	pnpm -r test
	@echo "==> Running forbidden-strings scan..."
	node scripts/forbidden-strings.mjs apps/web/src apps/mobile services/api/app
	@echo "==> Running no-business-literals scan (R3.3)..."
	node scripts/no-business-literals.mjs apps/web/src apps/mobile/src
	@echo "==> Running production guard verification..."
	cd services/api && $(UV) run pytest tests/test_prod_guard.py
	@echo "==> Running audit chain verifier..."
	cd services/api && $(UV) run python ../../scripts/verify_audit_chain.py
	@echo "========================================================"
	@echo "ALL GATES GREEN (Phase 1 Platform verification complete)"
	@echo "========================================================"
