# CLAUDE.md — AICTE Security Deposit / FDR Management Portal (SIH PS 26265)

Authoritative scope: `docs/spec/SPEC_v3.md` (the v3 production specification) and `docs/MASTER_PROMPT.md` (build instructions with stable section IDs). Problem statement: `docs/spec/PS26265_problem_statement.txt`. If these disagree with anything you remember, they win. If they disagree with each other, stop and ask.

## What this is
One backend + one database (system of record) and two clients: a web app and a native mobile app (Android + iOS). Same features on both. The only mobile-specific advantage is instant push notification and device-native conveniences; business rules live ONLY in the backend.

## Non-negotiables (violating any of these is a bug, not a trade-off)
1. **Nothing simulated in production.** No demo seeds, fake bank, mock provider success, simulated clock, voice/AI calling, or hard-coded sample records in prod images. Startup must refuse `DEMO_MODE`, `MOCK_BANK_PROVIDER`, `SIMULATED_CLOCK`, `FAKE_PUSH_SUCCESS` or equivalents. Fixtures live in `packages/fixtures`, are excluded from prod builds, and CI fails if they leak.
2. **Facts come from the database, never from a model.** Amounts, dates, statuses, clause references come from authorised records. LLM/OCR output is a *candidate* with provenance, reviewed by a human.
3. **No "verified" from OCR, AI, a file being present, or institution declaration.** Evidence is separate attributes: Institution-declared, Document-extracted, Bank-confirmed, Ledger-reconciled, Rejected/Inconclusive. Never collapse them into one score or one green badge.
4. **Maturity is a deadline, not permission to release.** Release needs checklist + independent recommendation + competent-authority decision (step-up MFA) + trusted execution evidence.
5. **Separate state machines** (instrument, evidence, observation, renewal link, release request). Allow-listed transitions only, inside a DB transaction that also writes `state_transitions`, `audit_events` and the outbox row.
6. **Default deny.** Every endpoint: authenticate → action permission → scope (institution/region/assignment) → resource state → delegation/SoD → field-level visibility. Postgres RLS as defence in depth. Cross-tenant ids return 404, never 403.
7. **Unsettled policy stays DRAFT/BLOCKED.** Penalty percentages/dates, exemptions, release authority: modelled as versioned config, never guessed, never auto-applied.
8. **Push is best-effort.** Persist the in-app inbox item first. Track CREATED → QUEUED → PROVIDER_ACCEPTED/FAILED → DEVICE_RECEIVED → OPENED → ACKNOWLEDGED → ACTIONED → EXPIRED/DEAD-LETTER separately. A notification never changes financial state.
9. **Unavailable means unavailable.** Show "not configured", "temporarily unavailable", "pending source response", "provider accepted", "evidence received", "human verified" distinctly. Never display success you did not observe.
10. **Money is `NUMERIC`/`Decimal`, never float.** Dates are `DATE`; events are UTC `timestamptz`; business timezone Asia/Kolkata; the server clock is the only clock (injectable `Clock` so tests can time-travel; prod rejects the test clock).

## Working rules
- Plan before coding; keep a living `docs/PLAN.md` and tick it off. Work in the phase order in `docs/PHASED_PROMPTS.md`; do not start phase N+1 until phase N's exit gate is green.
- **Verify, don't recall.** Library/API details (Expo SDK, `@expo/ui`, `expo-glass-effect`, FCM, APNs, Keycloak, Presidio, provider limits) change. Read the official docs for the pinned version before using an API. Record pinned versions + doc URLs in `docs/STACK_LOCK.md`. Items listed in `docs/VERIFY_AT_BUILD.md` need an explicit check and a note.
- Never claim a task is done without running it: tests, typecheck, lint, migration up/down, and for UI a real screenshot at mobile + desktop widths in light, dark and reduce-transparency. Paste the command output summary in the PR/commit notes.
- When a requirement can't be met for real (no bank API, no credentials), build the real *workflow* (statement import, bank-verifier portal, evidence recording) and show the connector as "not configured". Do not stub success.
- Don't invent AICTE facts. Open decisions D-01…D-14 are config toggles/flags in `docs/OPEN_DECISIONS.md`, each with the safe default the spec requires.
- Small commits, conventional commit messages, one concern each. Never commit secrets; `.env*` are denied to tools. Run `gitleaks` before pushing.
- Clause text from policy documents stays in English as the authoritative version; translations are labelled convenience copies.
- Keep this file short. Put long material in `docs/`.

## Commands (fill in as the repo is scaffolded — keep exact)
- Backend: `make api-dev`, `make api-test`, `make api-lint`, `make migrate`, `make openapi`
- Web: `pnpm --filter web dev|test|e2e|build|typecheck|lint`
- Mobile: `pnpm --filter mobile start|test|typecheck|lint`, `eas build` profiles in `apps/mobile/eas.json`
- Everything: `make verify` (lint + typecheck + unit + authz-negative + migration + contract + build + prod-guard)

## Definition of done (every task)
Code + tests (including negative/authorisation tests) + audit/outbox events + OpenAPI updated + generated client regenerated + i18n keys + a11y checked + docs updated + `make verify` green + traceability row updated in `docs/TRACEABILITY.md`.

## Design rules (short; full spec in MASTER_PROMPT §13)
- Brand: base `#050505`, surface tint violet `#3b0a6b`, accent cyan `#00eeff`. Violet is **never** text or icon colour on the base (1.40:1). Cyan fills take dark text (`#00363b`).
- Web + iOS: Apple HIG feel, Liquid Glass only on the navigation/control layer, never on content cards or tables; honour Reduce Transparency/Increased Contrast.
- Android: Material 3 (Expressive where verified), Material Symbols only for every icon. No other icon set in the Android build.
- Professional, restrained, dense-where-needed. No emoji as UI, no stock gradients-on-everything, no lorem ipsum, no placeholder avatars.
