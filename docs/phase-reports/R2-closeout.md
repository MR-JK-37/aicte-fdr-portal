# Stream R2 Close-Out — Staging Seed, Negative Drift Matrix, Process Debt Closure, and Exit Gate (2026-10-24)

Concludes Stream R2 (Authentication and the 13 roles) per `docs/MASTER_PROMPT_V2.md` and `docs/AUTH_ROLES_MATRIX.md`.

## 1. Process Debt & Live Container Drift Closed
- **Root cause flagged in R2.5:** Docker images bake source at build time; local `uv run pytest` tests run against a local venv and never test the running container. Stale containers could silently diverge from source.
- **Fix:** Authored `scripts/smoke_test_live_api.sh` and wired `make redeploy` and `make smoke-test` into `Makefile`.
- **Verified live:** Hits the live `http://localhost:8000`:
  - OpenAPI schema reachable (200)
  - Intentionally wrong-password login rejected (401, not a 200 bypass)
  - CORS preflight for mobile dev origin (`http://localhost:8082`) verified.

## 2. Test/DB Isolation & Full Suite Green
- **Root cause:** `test_outbox_scheduler.py` failed because running worker containers in Docker held the singleton advisory lock `0x46445253` on the shared development database.
- **Fix:** Parameterized `try_acquire_scheduler_lease(session, key=...)` and `release_scheduler_lease(session, key=...)` in `app/outbox/scheduler.py` with backward-compatible defaults. In `tests/test_outbox_scheduler.py`, used a dedicated test key `0x46445259`.
- **Result:** `test_outbox_scheduler.py` passes 4/4; full backend suite `pytest -m "not slow" -q` passes **616 passed, 1 skipped, 0 failed**.

## 3. Drift Verification & Role Permissions Matrix (R2.7)
- **Built `tests/test_authz_drift.py`:** Automatically parses the markdown table in `docs/AUTH_ROLES_MATRIX.md` §3 and asserts that `ROLE_PERMISSIONS_MATRIX` in `app/authz.py` matches it verbatim.
- **Fixed matrix gaps:** Aligned `ROLE_PERMISSIONS_MATRIX` with `AUTH_ROLES_MATRIX.md` §3 across all 12 human roles (added missing permissions for `ORG_ADMIN`, `REGIONAL_SUPERVISOR`, `FINANCE_VERIFIER`, `COMPETENT_AUTHORITY`, `AUDIT_REVIEWER`, `IDENTITY_ADMIN`, `PLATFORM_OPERATOR`, and adjusted `BANK_VERIFIER`).
- Both `test_authz_drift.py` and `test_authz_negative_matrix.py` pass.

## 4. Staging Seed (R2.6, AUTH §4)
- **Built `scripts/seed_staging.py` and `make seed-staging`:**
  - Refuses to execute if `APP_ENV=production` or `ENV=production`.
  - Creates 2 synthetic tenants:
    - `1-1000000001`: Apex Institute of Technology (Synthetic Tenant A)
    - `1-1000000002`: Beacon College of Engineering (Synthetic Tenant B)
  - Creates 1 synthetic bank (`State Bank of India (Synthetic Staging Bank)`) with branch `SBIN0099999`.
  - Seeds 1 user per role across all 12 human roles (plus tenant B Org Admin for cross-tenant testing).
  - Pre-enrolls argon2id hashed passwords, encrypted TOTP secrets (`mfa_enrolled=True`), and 10 single-use hashed recovery codes.
  - Safely outputs credentials to `.local/staging-users.json` (file mode `0600`, gitignored, never printed to console logs).

## 5. Live End-to-End Verification of Seeded Roles
Executed automated verification against the running API (`:8000`):
- All 13 accounts successfully authenticated with password + generated TOTP code.
- Each account received valid access token + refresh token.
- Each account called `GET /v1/me/navigation` and received their role-specific landing route and mobile tab set verbatim matching `AUTH_ROLES_MATRIX.md` §1:
  - `org_admin`: landing `/home`, tabs `['nav.home', 'nav.deposits', 'nav.inbox', 'nav.profile']`
  - `intake_officer`: landing `/intake-queue`, tabs `['nav.home', 'nav.queue', 'nav.inbox', 'nav.more']`
  - `scrutiny_officer`: landing `/my-queue`, tabs `['nav.home', 'nav.cases', 'nav.inbox', 'nav.more']`
  - `finance_verifier`: landing `/verification-requests`, tabs `['nav.home', 'nav.verify', 'nav.inbox', 'nav.more']`
  - `regional_supervisor`: landing `/workload-board`, tabs `['nav.home', 'nav.cases', 'nav.inbox', 'nav.more']`
  - `competent_authority`: landing `/decisions`, tabs `['nav.home', 'nav.decisions', 'nav.inbox', 'nav.more']`
  - `audit_reviewer`: landing `/audit-timeline`, tabs `['nav.home', 'nav.audit', 'nav.inbox', 'nav.more']`
  - `identity_admin`: landing `/access-admin`, tabs `['nav.home', 'nav.access', 'nav.inbox', 'nav.more']`
  - `platform_operator`: landing `/system-health`, tabs `['nav.home', 'nav.system', 'nav.inbox', 'nav.more']`
  - `bank_verifier`: landing `/assigned-requests`, tabs `['nav.requests', 'nav.inbox', 'nav.profile']`

## 6. Verification Status (`make verify`)
- `ruff check .`: clean
- `pytest -m "not slow"`: 616 passed, 1 skipped, 0 failed
- `pnpm -r build`: clean
- `pnpm -r test`: 18/18 passed on web, 2/2 passed on shared, 23/23 files clean in mobile icon verifier
- `forbidden-strings.mjs`: OK across `apps/web/src`, `apps/mobile`, `services/api/app`
- `pytest tests/test_prod_guard.py`: 17/17 passed
- `scripts/verify_audit_chain.py`: PASS (0 tamper points)
- `scripts/smoke_test_live_api.sh`: 3/3 checks passed

---
**STREAM R2: PASS** — Exit gates G-08, G-09, G-10, G-11, G-12, G-29 met.
Ready to proceed to Stream R3 (Contract, generated clients, real data everywhere).
