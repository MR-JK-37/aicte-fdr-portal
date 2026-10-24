# AICTE FDR Portal — docs/PLAN.md (Phase 0 kick-off plan)

## Context
This repo already has a 10-"phase" build (commits `bd98148`…`21715d3`) against an older
`Blueprint.txt` spec. The user just dropped a new, authoritative spec package
(`docs/MASTER_PROMPT.md` §0–§23, `docs/spec/SPEC_v3.md`, `docs/spec/PS26265_problem_statement.txt`,
`design/DESIGN_SPEC.md`, `docs/VERIFY_AT_BUILD.md`, `docs/PREFLIGHT.md`, `docs/OPEN_DECISIONS.md`,
`CLAUDE.md`) which **supersedes** the old spec and is now extracted into the repo. The new spec
directly bans features the old build already shipped. User has confirmed:
1. Treat the new spec as authoritative; rebuild/remove conflicting old work (not "layer on top").
2. Full MASTER_PROMPT scope (all 10 phases, §20), executed phase-by-phase across many sessions,
   not a hackathon-trimmed subset.

## What gets removed (explicitly banned by SPEC_v3 §1.4 / CLAUDE.md #1)
- `services/voice/`, `services/api/app/voice/*` (1,502 LOC), the `voice_router` mount in
  `app/main.py`, the `CallSession` model/table + its 2 migrations, and the `"voice_call"` step in
  `app/reminders/ladder.py` — AI voice calling/WebRTC/PINs are a hard exclusion, not a stub.
- `app/sim_clock.py` + the `sim_clock` table/migration + every caller (`reminders/ladder.py`,
  `reminders/scheduler.py`, `voice/*`, `celery_app.py`) — replaced by an injectable `Clock`
  (real clock in prod, test-only override that prod startup refuses) per CLAUDE.md #10.
- `app/verification/mock_bank_api.py`, `mock_sfms_feed.py` — replaced by the real workflow: F-06
  (bank-confirmation requests + bank-verifier portal role) and F-07 (MT940/CAMT.053/CSV/XLSX
  statement import + deterministic reconciliation).

## What gets salvaged
- `infra/docker-compose` skeleton (Postgres, Keycloak 26.8.1 already `start-dev`/OIDC-ready,
  Garage as S3-compatible store, ClamAV, Caddy, Mailpit) — matches the new stack shape; extend,
  don't replace.
- The Postgres RLS pattern (`ENABLE ROW LEVEL SECURITY` + `tenant_isolation` policy,
  `SET LOCAL` GUCs) — correct technique, needs extending from 8 roles to the new 13-role model
  and from `app.role`/`app.institution_id` to the fuller `app.user_id`/`app.role_scope`/
  `app.assurance` context MASTER_PROMPT §8.5 specifies.
- Monorepo tooling (pnpm workspaces, turbo.json, `uv` for Python), `packages/shared` scaffold.
- Recent mobile styling work (Expo SDK 58, Tailwind, `#050505/#3b0a6b/#00eeff`) — already matches
  `design/DESIGN_SPEC.md`'s brand tokens exactly; reuse as the starting visual baseline.

## What gets rewritten (architecture-level, not additive)
- 8-role `AppRole` enum + all authz checks → new 13-role model, data-driven `role_permissions`
  table, single `authorise()` function (MASTER_PROMPT §8.2–§8.4), allow-list response serialisers.
- Celery + Valkey worker/beat → Postgres transactional outbox + `FOR UPDATE SKIP LOCKED` worker +
  DB-leased scheduler singleton (MASTER_PROMPT §4.2, §10.2) — the new spec explicitly prefers this
  over a queue broker ("Celery/Valkey optional later; do not add unless needed").
- `lifecycle.py` single state machine → 5 separate explicit state machines (instrument, evidence,
  observation, renewal link, release request) per §7, each with an exhaustive generated transition
  test.

## Phase order (one phase per session, per `docs/PHASED_PROMPTS.md`; exit gate before next phase)
0. Foundations & spikes S-01…S-07, stack lock, prod-guard test, CI skeleton.
1. Platform: OIDC/MFA/step-up, 13-role model, `authorise()`, RLS rewrite, pool-isolation test,
   audit hash-chain, outbox+worker skeleton, design-system primitives (web+mobile).
2. Core workflow: institutions, instruments+versions+receipts, upload pipeline (quarantine→
   ClamAV→sanitise→hash→vault), observations, assignment queues.
3. Evidence & verification: OCR review UI, bank-verifier portal, statement import+reconciliation,
   discrepancy engine — the real replacements for the removed mocks.
4. Lifecycle & release: policy registry (draft-only), scheduler+reminders+escalation, renewal
   lineage, release checklist/clearances/decision/execution with maker-checker + step-up MFA.
5. Notifications & realtime: outbox consumer, FCM/APNs/Web Push/e-mail adapters (honest
   "not configured" where credentials are absent — see PREFLIGHT gaps below), SSE.
6. Web app completion: all §11 screens, dashboards/reports/exports, i18n (en/hi/ta), a11y.
7. Mobile app completion: native iOS (SwiftUI/Liquid Glass)/Android (Material 3) parity matrix.
8. AI/OCR gateway: multi-provider LLM gateway with verified free-tier terms, Tier S local-only.
9. Hardening & compliance: full security checklist, load/restore/chaos tests, runbooks, final audit.

## Top risks
- **Scale**: this is genuinely a multi-week enterprise build (28 functional modules, 2 native
  client UIs, push infra, LLM gateway, i18n×3, full a11y/security hardening). Expect ~1 phase per
  session; do not compress phases to look faster — exit gates exist specifically to prevent that.
- **PREFLIGHT gaps are real and intentional, not blockers**: no FCM/APNs credentials, no Apple
  dev account, no real bank statements, no AICTE institution list, no policy sign-off (D-01…D-14
  all "Open"). Per CLAUDE.md, the correct behaviour is to build the real workflow and show
  "not configured" — never to fake success. This affects Phases 5, 3, 4, 8 visibly.
- **Role-model rewrite is foundational**: every later module depends on Phase 1's `authorise()` +
  RLS landing correctly; a mistake here propagates everywhere, so Phase 1's negative-test matrix
  is the highest-leverage test suite in the whole build.
- **Worker architecture change** (Celery/Valkey → Postgres outbox) touches every background job
  (reminders, OCR, reconciliation) — done once in Phase 1, not incrementally.
- **Mobile native UI coverage is unknown** until spike S-02 (`@expo/ui` Jetpack Compose/SwiftUI
  coverage) runs in Phase 0; a hand-built Material 3 / HIG fallback is the documented contingency.

## Immediate next step after approval
Execute Phase 0 exactly as `docs/PHASED_PROMPTS.md` PROMPT 1: remove the banned modules (voice,
sim_clock, mock verification) with their migrations reverted cleanly, confirm/extend the
docker-compose skeleton, run spikes S-01…S-07 and write `docs/spikes/S-0x.md`, fill
`docs/STACK_LOCK.md`, write the production-guard test (§17.4) and prove it rejects a forbidden
env flag, and write this plan to `docs/PLAN.md` as the first commit of the phase.
