#!/usr/bin/env bash
# Render.com start command for the FastAPI backend.
#
# MIGRATION_DATABASE_URL (Render's admin role on the free Postgres plan)
# runs Alembic, which creates the restricted `fdr_app` runtime role and its
# RLS policies (migrations/versions/a821603301c6_...py — hardcoded password
# fdr_app_dev_password, pre-existing in this repo, not introduced for this
# deploy). DATABASE_URL is derived from it here so the app actually
# connects as fdr_app at runtime, not the admin role — running as admin
# would bypass RLS entirely and defeat the tenant-isolation layer this
# app's authz model depends on (CLAUDE.md non-negotiable #6).
set -euo pipefail

uv run alembic upgrade head

# Best-effort: seeds the staging roster if the DB has none yet. Never fails
# the deploy — scripts/seed_staging.py already refuses to run in production.
uv run python ../../scripts/seed_staging.py || true

export DATABASE_URL="$(uv run python -c '
import os
from urllib.parse import urlsplit, urlunsplit
p = urlsplit(os.environ["MIGRATION_DATABASE_URL"])
netloc = f"fdr_app:fdr_app_dev_password@{p.hostname}" + (f":{p.port}" if p.port else "")
print(urlunsplit(("postgresql+psycopg", netloc, p.path, p.query, "")))
')"

exec uv run uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
