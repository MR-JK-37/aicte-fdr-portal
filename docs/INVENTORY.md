# docs/INVENTORY.md — live repo inventory (2026-10-24, PROMPT A)

Everything below was verified by reading code and running commands in this session — nothing is
carried over from `docs/FINAL_AUDIT.md`, `docs/TRACEABILITY.md`, or any prior phase report without
re-checking, because those documents' claims (see §5) do not match what the source actually does.

## 1. Directory map
```
apps/web          Vite + React 19 + TS, Tailwind. No API client wiring.
apps/mobile        Expo SDK 58 (~58.0.17), RN 0.88. NOT using Expo Router.
services/api       FastAPI backend, uv-managed Python venv, Alembic migrations, 71 test files.
packages/
  api-client       Exists (workspace pkg) — unclear if generated from OpenAPI or hand-written.
  design-tokens    Re-exports design/tokens.ts (still v1 dark).
  i18n, schemas, shared
config/            policy-drafts (DRAFT-only, per D-01), connectors.example.yaml, LLM_PROVIDERS.yaml
docs/, design/     see §6
```

## 2. Stack/versions (STACK_LOCK.md exists; not re-verified against upstream docs this session)
- Mobile: Expo `~58.0.17`, React Native `0.88.0`, React `19.3.0`, `expo-symbols` 58.0.4,
  `expo-glass-effect` 58.0.5. **No `expo-router`, `react-native-web`, `react-dom`,
  `@expo/metro-runtime` anywhere in the monorepo** (`node_modules/expo-router` absent).
- Web: React 19, Vite, Tailwind 3.4 (spec wants Tailwind v4 `@theme` — not yet done).
- Backend: FastAPI + uv; Alembic migrations present; Celery beat + outbox worker run as root
  services (already running at session start, PIDs predate this session — likely from a prior
  `make dev`/systemd-style setup, not started by me).

## 3. How each app starts today
- `make api-dev` → `uvicorn app.main:app --reload --port 8000` (works; a uvicorn instance was
  already running on :8000 at session start).
- `apps/web`: `pnpm --filter web dev` (not run this session; no reason to suspect it fails to
  boot — Vite/React is a solid pattern — but it will render **only the hard-coded mock**, see §4).
- `apps/mobile`: `package.json` `"main": "node_modules/expo/AppEntry.js"`; `expo start --port 8082`.
  Entry is NOT `expo-router/entry`. This reproduces defect **A-01** from the work order: the app
  has no router, so there is no multi-screen navigation, no floating tab bar, and (per the Expo
  docs cited in `docs/DESIGN_RESEARCH.md`) the web/Metro bundle will fail to resolve
  `react-native-web` the same way the original audit found. Not re-run live this session (R0 owns
  the fix+proof); config inspection alone is conclusive enough to confirm the defect exists.
  `app.json` also: `userInterfaceStyle: "dark"`, splash `#050505` (v1 dark theme baked in), and
  Android `permissions: ["RECORD_AUDIO", "VIBRATE", "USE_FULL_SCREEN_INTENT"]` — `RECORD_AUDIO` is
  a leftover from the removed voice-call feature (matches A-04) and must be deleted in R1, not
  just the UI for it.
- `Makefile` has no `dev`/`dev-stop`/`seed-staging` targets yet (only `api-dev`, `api-test`,
  `api-lint`, `migrate`, `openapi`, `audit-verify`, `lint`, `test`, `verify`). R0.4 needs to add
  the combined dev-stack target the work order expects.

## 4. Honesty / reality check (CLAUDE.md non-negotiable #1, work order §1 defects A-01…A-16)
All still present, verified by reading the actual source (not assumed from any audit doc):

| Defect | Evidence (this session) |
|---|---|
| A-01 mobile bundler | `apps/mobile/package.json` `main` ≠ router entry; `expo-router` not installed anywhere in the monorepo (confirmed via `find`). |
| A-02 web never calls API | `grep -rl "fetch(" apps/web/src` → **0 files**. |
| A-04 simulation/demo UI | `apps/web/src/components/SimClockControl.tsx` ("Simulation Clock (Time Travel)"), `VerificationView.tsx` ("Simulate Statement Ingestion", "Simulate L2 Reply"), `NewFDRSubmission.tsx` ("(Demo FDR)") all present and imported into the live component tree, not dead code. |
| A-16 hard-coded sample data | `apps/web/src/App.tsx` hard-codes `AXIS-FDR-99201`, `SBI-881920`, `HDFC-441029`, `PNB-771829` as instrument records; `VerificationView.tsx` repeats them with real-looking bank names. |
| A-03 no real auth/roles in UI | Not re-verified live this session (no browser run), but zero `fetch(` calls means no `/auth/*` or `/me/*` call exists either — the mock cannot be driving real auth. |
| Test suite protects the mocks | `apps/web/src/App.test.tsx` asserts `getByText(/AXIS-FDR-99201/i)` and `getByRole('button', {name: /AI Voice Call/i})` — a green `pnpm test` here is evidence the fakes are *intact*, not evidence of correctness. R1 must delete these assertions along with the fakes. |

## 5. Backend: real but incomplete, and NOT what `FINAL_AUDIT.md` claims
`services/api/app/main.py` mounts 17 routers: `auth, registry, receipts, institutions, instruments,
observations, queues, documents, verification, statements, discrepancies, policy, renewals,
release, notifications, realtime, agents`.

**Missing entirely** (no directory under `services/api/app/`, confirmed by listing): `dashboard`,
`search`, `audit`, `users` (access/roles/invitations as a dedicated module — `auth` only covers
login/sessions), `reports`/`exports`, `admin`, `help`, `retention`. This directly contradicts
`docs/FINAL_AUDIT.md` rows for PS-08 (Dashboards & Reports — claimed DONE), §17/§18 (Audit —
claimed DONE), F-19 (Admin — claimed DONE), F-16/F-17/F-18/F-21/F-22 — **all still open**, matching
work order defect A-10 exactly.

**Correction (first-pass grep targeted the wrong directory, `services/api/alembic`, which doesn't
exist):** the real migrations live in `services/api/migrations/versions/`, and
`a821603301c6_rls_policies_and_audit_immutability.py` does enable it. Verified directly against
the live dev DB (`SELECT relname FROM pg_class ... WHERE relrowsecurity = true`): RLS is actually
**ON** for 19+ tables (`documents`, `audit_log`, `release_requests`, `discrepancies`,
`verification_records`, `device_tokens`, `reminders`, `escalations`, etc.). CLAUDE.md non-negotiable
#6 is genuinely implemented at the DB layer here, not just in `authorise()`. G-29 (RLS
pool-isolation + missing-context-zero-rows tests) still needs its own dedicated test run before
being called green, but the earlier "no RLS anywhere" claim in this file was wrong — struck
through for the record, not deleted, so future readers see the correction.

`authorise()`-style authorization usage found in 5 files via grep (narrow signal; not a full
coverage count — R2.3's job is to make this universal and testable).

## 6. Backend test suite — resolved in R0 (`docs/phase-reports/R0.md` has the full evidence)
`tests/test_extraction_accuracy.py::test_extraction_benchmark_across_all_layouts` was not hung —
it does real PDF rendering + Tesseract OCR over 100 synthetic documents and genuinely takes
several minutes. R0 marked it `@pytest.mark.slow` (registered in `services/api/pyproject.toml`)
and excluded it from the default `make api-test`/`make verify` (now `pytest -m "not slow"`); a new
`make api-test-slow` target runs it on demand. With that excluded, a clean run completes in ~28s:
**597 passed, 1 skipped, 3 failed, 1 deselected.** The 3 failures
(`tests/test_outbox_scheduler.py`) are **not a code bug**: `docker ps` shows the full
`fdr-portal-*` compose stack (including `fdr-portal-worker-1`, running `app.outbox.run_worker`)
has been up for 19 hours — that live process holds the Postgres session-scoped advisory lock
(`pg_try_advisory_lock`) the scheduler-lease tests also try to acquire against the same dev
database (`tests/conftest.py`'s `TEST_DATABASE_URL` points at `localhost:5434`, the same DB the
live stack uses — there is no separate test database). This is a **test-isolation gap** (tests
should run against an isolated database, not the live dev stack) to fix in R4/R8, not a defect in
the scheduler itself. `docs/FINAL_AUDIT.md`'s "588 passed, 1 skipped" figure is now superseded by
this freshly-verified number; still treat any future count as unverified until re-run.

## 7. Design system state
- `design/DESIGN_SPEC.md`, `design/tokens.ts`, `design/tokens.css`, `design/check_tokens.py` are
  still the **v1 dark "Apple HIG + Liquid Glass + Material 3" spec** (`#050505` base, violet
  `#3b0a6b`, cyan `#00eeff`) — matches CLAUDE.md's current "Design rules" section.
- The user supplied, and this session materialized into the repo, the **v2.1 "Lavender Ledger"**
  light design system (`docs/MASTER_PROMPT_V2.md`'s design parts, `docs/AUTH_ROLES_MATRIX.md`,
  `docs/DESIGN_RESEARCH.md`, `docs/EXPO_GO_VS_DEV_BUILD.md`, `docs/PHASED_PROMPTS_V2.md`,
  `design/preview.html`, `design/build_preview.py`, `design/reference/reference-sheet.png`,
  `design/preview-screenshots/*`) from `aicte-fdr-v2-fix-and-complete.zip` at the repo root. The
  old v1 tokens/spec were **copied** (not moved) to `design/archive-v1-dark/` for reference; the
  live `design/DESIGN_SPEC.md`/`tokens.*` were left untouched this session because switching them
  is R5 work (needs the design-contract tests written first, per R5.0) and Prompt A is plan-only.
  See `docs/DECISIONS.md` ADR-002 for the v1→v2 supersession call.

## 8. Diffs between the zip's docs and the repo's existing docs (not reconciled this session)
`CLAUDE.md`, `docs/MASTER_PROMPT.md`, `docs/OPEN_DECISIONS.md`, `docs/VERIFY_AT_BUILD.md`,
`docs/TRACEABILITY.md`, `docs/PHASED_PROMPTS.md` all differ slightly (a few lines each) between
the repo's checked-in versions and the zip's versions. Not overwritten this session — CLAUDE.md
in particular is project-owned config and a content decision beyond plan-only scope. Flagged here
so a future session reconciles deliberately instead of silently diverging.

## 9. R0 status: A-01 fixed and proven (see `docs/phase-reports/R0.md`)
`apps/mobile/package.json` `main` → `expo-router/entry`; added `expo-router`, `react-native-web`,
`react-dom`, `@expo/metro-runtime`, `expo-constants`, `expo-linking`, `expo-font`,
`react-native-safe-area-context`, `react-native-screens` via `npx expo install`; `app.json` got
`scheme`, `web.bundler: "metro"`, `web.output: "single"`, the `expo-router`/`expo-font` plugins,
removed the leftover `RECORD_AUDIO` permission, and dropped the now-invalid top-level `splash` key
(SDK 58 schema). Aligned `expo`/`typescript` to the versions `expo-doctor` expects (20/20 checks
now pass, was 17/20). A minimal `app/_layout.tsx` + `app/index.tsx` boot shim was added so
`expo-router/entry` has somewhere to route to — it currently re-exports the existing (still-mock)
`App.tsx` content; R1 replaces the mock, R6 replaces the shell with the real floating-tab-bar
screens. `npx expo export` for web/android/ios all exit 0, `npx tsc --noEmit` is clean, and a live
`expo start --web --port 8082` was fetched directly (no Playwright Chromium available in this
sandbox — `npx playwright install` needs `sudo` this environment doesn't have) and returned the
real Metro-bundled JS (7000+ modules, HTTP 200) instead of the original
`UnableToResolveError: react-native-web/dist/exports/AppRegistry` 503.
