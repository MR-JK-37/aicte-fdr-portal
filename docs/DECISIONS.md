# docs/DECISIONS.md — ADR log (v2 fix-and-complete)

## ADR-001 — Identity provider (FINALIZED in R2, was provisional from R0)
**Decision:** Complete the existing API-native identity module (`services/api/app/auth/`) as the
single `IdentityProvider` implementation. Keycloak (running in `infra/docker/docker-compose.yml`,
with a realm JSON and setup script) stays available for a possible future SSO/D-08 federation
decision but is **not** the active identity provider — nothing in the codebase verifies a
Keycloak-issued token; `get_current_principal` only ever decodes this API's own self-issued HS256
JWT, and `AppUser.keycloak_sub` is a vestigial column.
**Why:** R2 found the existing module did NOT cover §2 of `docs/AUTH_ROLES_MATRIX.md` at all —
`/auth/login` had no password check whatsoever (any registered e-mail logged in regardless of what
password was sent) and `/auth/step-up` accepted any syntactically-valid 6-digit code. Given (a) the
13-role model, `ROLE_PERMISSIONS_MATRIX`, and Postgres RLS are already correctly built around
`AppUser` as the source of truth, and (b) `infra/keycloak/fdr-realm.json` /
`scripts/setup_keycloak.py` still encode the stale **8-role** model (never updated for the 13-role
migration) confirming Keycloak was never actually wired in — building out the existing module
(real argon2id passwords + TOTP, now done; sessions/passkeys/invitations, not yet) is lower-risk
than standing up a second, currently-unused identity system from a stale starting point.
**How to apply:** R2 continuation completes sessions, passkeys, invitations, recertification
against this same module. `infra/keycloak/fdr-realm.json`/`scripts/setup_keycloak.py` should be
deleted or clearly marked not-in-use so they stop misleading a future reader — not done yet.

## ADR-002 — Design system: v2 "Lavender Ledger" supersedes v1 dark/Liquid-Glass
**Decision:** The v2.1 light "Lavender Ledger" design system
(`docs/MASTER_PROMPT_V2.md` design parts referenced from `docs/MASTER_PROMPT_COMPLETE.md`,
`design/DESIGN_SPEC.md` content pending activation, `design/tokens.ts`/`tokens.css` pending
activation, `design/preview.html`) **supersedes** the v1 dark/violet/cyan Liquid-Glass system
currently described in `CLAUDE.md`'s "Design rules" section and still live at
`design/DESIGN_SPEC.md`/`design/tokens.*`.
**Why:** the user supplied the full v2 work order (which explicitly states "where v1 §13 ...
design conflicts with v2, v2 wins") and then separately posted a screenshot of
`design/preview.html` labelled "this [is] the ui reference" — an explicit, direct confirmation of
the new visual direction, not just inclusion in a large pasted document.
**How to apply:** R5 (`docs/MASTER_PROMPT_V2.md` §8) is where the cutover actually happens: write
the design-contract tests first (R5.0), then replace `design/DESIGN_SPEC.md`, `design/tokens.ts`,
`design/tokens.css`, `design/check_tokens.py` with the v2 versions (currently staged as copies
under `design/archive-v1-dark/` in reverse — i.e. the *old* v1 files are archived there; the *new*
v2 files are not yet activated at the canonical paths because that would be a source/build change,
out of scope for a plan-only session). `CLAUDE.md`'s "Design rules" section should be updated to
match in the same stream, since it is checked-in project config that currently states the v1
palette as binding — note this explicitly in the R5 phase report rather than silently drifting
from it.

## ADR-003 — Do not trust prior "done" claims without re-verification
**Decision:** `docs/FINAL_AUDIT.md`, `docs/TRACEABILITY.md`, and the phase-report history
(phases 0–9 against the old Blueprint/MASTER_PROMPT v1 build) are **not** treated as evidence of
current state for this v2 effort. Every gate in `docs/MASTER_PROMPT_V2.md` §2 will be re-earned
with fresh evidence (command output, screenshots) in this stream's own phase reports.
**Why:** `docs/FINAL_AUDIT.md` claims PS-08 (dashboards/reports), §17/§18 (audit), and F-19 (admin)
are all "DONE", but `docs/INVENTORY.md` §5 shows none of `dashboard`, `search`, `audit`, `users`,
`reports`, `admin`, `help`, `retention` exist as backend modules, and `apps/web/src` has zero
`fetch()` calls — the web app cannot be rendering real dashboards/reports/audit data because it
calls no API at all. This is a direct, source-verified contradiction of a document that described
itself as "VERIFIED (PASS)" with "588 passed" tests. Whatever produced that report either audited
a different checkout, ran against stale assumptions, or self-graded without reading the actual
source — the cause doesn't matter; the fix is to stop trusting self-reported completion summaries
and re-check against running code and tests every time, per CLAUDE.md's "Verify, don't recall" and
the work order's "Evidence or it did not happen."
**How to apply:** every future phase report in `docs/phase-reports/R<n>.md` must link to command
output or a screenshot for each gate it claims green; a report that only asserts "DONE" without
evidence should be treated the same way `FINAL_AUDIT.md` was — unverified until re-checked.

## Resolved during R0 (were open items in the PROMPT A version of this file)
- **RLS exists and is real**: first-pass grep targeted a nonexistent `services/api/alembic`
  directory; the actual migrations are in `services/api/migrations/versions/`, and
  `a821603301c6_rls_policies_and_audit_immutability.py` enables it. Confirmed live against the dev
  DB: `relrowsecurity = true` on 19+ tables. CLAUDE.md non-negotiable #6 holds. G-29 still needs
  its own dedicated pool-isolation test run, but there is no "app-layer only" gap to close.
- **`test_extraction_accuracy.py` was never hung**, just slow (real OCR over 100 docs, ~5 min).
  Marked `@pytest.mark.slow` (registered in `services/api/pyproject.toml`), excluded from
  `make api-test`/`make verify` by default, runnable via the new `make api-test-slow`. A clean
  `pytest -m "not slow"` run now completes in ~28s: 597 passed, 1 skipped, 3 failed, 1 deselected.
- **ADR-004 — the 3 `test_outbox_scheduler.py` failures are a test-isolation gap, not a bug.**
  `docker ps` shows the full `fdr-portal-*` compose stack has been running for 19 hours
  (independent of this session), including `fdr-portal-worker-1`
  (`app.outbox.run_worker`), which holds the real Postgres advisory lock
  (`pg_try_advisory_lock`) the scheduler-lease tests also contend for — because
  `tests/conftest.py`'s `TEST_DATABASE_URL` points at the same `localhost:5434` dev database the
  live stack uses, not an isolated test DB. **Do not "fix" this by stopping the live stack** (it
  may be in use for other work outside this session) or by weakening the test's assertion — fix it
  by giving the test suite its own database/schema, tracked for R4/R8.

## Still open
- Minor content diffs between the zip's `CLAUDE.md`/`docs/MASTER_PROMPT.md`/`docs/OPEN_DECISIONS.md`/
  `docs/VERIFY_AT_BUILD.md`/`docs/TRACEABILITY.md`/`docs/PHASED_PROMPTS.md` and the repo's current
  versions — not reconciled; left as-is (repo versions remain authoritative) pending a deliberate
  review, since CLAUDE.md is project-owned config.
- No Playwright-compatible Chromium is installable in this sandbox (`npx playwright install`
  needs `sudo apt`, unavailable). **Resolved for manual verification**: `mcp__claude-in-chrome`
  works (used in R2.5 to drive a real end-to-end mobile login/MFA-enrolment flow with screenshots
  and console/network inspection). Still open: an *automated, scripted* equivalent (Playwright-style
  `e2e:roles` test suites G-23/G-24 call for) — `mcp__claude-in-chrome` is an interactive tool
  for this session, not a CI-runnable test framework.
- **Found in R2.5**: the live `fdr-portal-api-1`/`worker`/`migrate` Docker containers were running
  code from **before this entire R2 stream** (image built 2026-10-24T10:21:30Z) — confirmed by
  `curl`ing the live `:8000` login endpoint with a wrong password and getting HTTP 200. No volume
  mount; the image bakes in source at build time and nothing had rebuilt it. Backend `pytest` runs
  against a separate local `uv` venv, which is why 613 passing tests never caught this. **Fixed**:
  rebuilt and redeployed all three services, re-verified live via `curl`. **Not fixed**: there is no
  automated check that the live container matches source — worth a `make redeploy` step or a
  live-smoke-test gate in a future session. See `docs/phase-reports/R2-mobile-ui.md`.
- **Found in R2, not fixed**: `app/auth/deps.py` (~line 111–119) scopes `BANK_VERIFIER` users to a
  bank purely by checking whether the user's own e-mail contains a substring like `"@sbi."` —
  not validated against any onboarding-approved domain allowlist. `attacker@sbi.evil.com` would be
  granted SBI's verifier scope today. Pre-dates this session; needs the bank-onboarding
  domain-allowlist data model (doesn't exist yet) to fix correctly. See `docs/phase-reports/R2.md`.
- `settings.totp_encryption_key` (new in R2) has a fixed, checked-in dev default — `prod_guard`
  should reject it in production the same way it rejects the other dev-only defaults; not done.

## Genuine blockers (none new this session)
`docs/PREFLIGHT.md` already tracks every external credential/input gap (FCM/APNs, bank statement
samples, policy sign-off, named approvers, hosting). Nothing in this session surfaced a new
blocker; R0/R1 can proceed without any of them.
