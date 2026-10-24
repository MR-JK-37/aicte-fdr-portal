# PHASED_PROMPTS.md — paste these one at a time into Claude Code

How to use: start every phase in a **fresh session** (or after `/clear`) so context stays clean; `CLAUDE.md` loads automatically. Each prompt tells Claude to re-read the relevant parts of `docs/MASTER_PROMPT.md` instead of relying on memory. Do not skip the exit gate. If a phase is large, split it by module ID (F-xx) and keep `docs/PLAN.md` updated.

Common footer for every phase prompt (already included below as "Close-out"): run `make verify`; run the `reviewer` and `security-auditor` subagents on the phase diff; run `spec-auditor` against the sections listed; write `docs/phase-reports/N.md` in the §20 final-report format; update `docs/TRACEABILITY.md`; commit in small conventional commits.

---

## PROMPT 0 — Kick-off (Plan Mode)
```
Read CLAUDE.md, docs/MASTER_PROMPT.md, docs/spec/SPEC_v3.md, docs/spec/PS26265_problem_statement.txt, docs/VERIFY_AT_BUILD.md, docs/PREFLIGHT.md and design/DESIGN_SPEC.md completely.
Then, in plan mode only (no code): 
1. Write docs/PLAN.md (≤2 pages): scope, phase order, top risks, anything contradictory or missing.
2. List every input from docs/PREFLIGHT.md that is still missing and what it blocks.
3. Propose the spike plan S-01…S-07 with pass/fail criteria.
Ask me only about genuine blockers. Do not write production code yet.
```

## PROMPT 1 — Phase 0: Foundations and spikes
```
Execute Phase 0 of docs/MASTER_PROMPT.md §20.
- Scaffold the monorepo exactly as §5 (pnpm workspaces, uv/pyproject, Makefile, docker-compose for postgres+pgvector, minio, keycloak, clamav, mailpit).
- Run spikes S-01…S-07; write results to docs/spikes/S-0x.md with the exact versions, doc URLs, what worked, what did not, and the chosen fallback. Fill docs/STACK_LOCK.md.
- Create the CI skeleton and the production-guard test (§17.4) even if the app is empty.
- Create docs/OPEN_DECISIONS.md with D-01…D-14 and the safe default (§21).
Exit gate: plan approved, spikes documented, `make verify` runs green, prod-guard test fails if a forbidden flag/fixture is present (prove it by temporarily adding one).
Close-out as per docs/PHASED_PROMPTS.md.
```

## PROMPT 2 — Phase 1: Platform
```
Execute Phase 1 (§20) using MASTER_PROMPT §2, §6, §8, §9 F-01, F-18, F-19 (registry only), F-27, F-28 and §13.
Build: Keycloak realm config + OIDC (web cookie session via API BFF; mobile PKCE), MFA (TOTP + passkeys), step-up, role/permission tables generated from the SPEC §5 matrix, the single authorise() function and allow-list serialisers, RLS with set_config per transaction, the pool-isolation test, audit hash chain + checkpoint job + verification script, transactional outbox + worker skeleton, idempotency middleware, optimistic concurrency, problem+json errors, correlation IDs, feature/connector registry, packages/{schemas,api-client,i18n,design-tokens} and the design-system primitives for web (React) and mobile (iOS SwiftUI/Android Compose or fallback) per spike S-02.
Tests first for: the role×action×scope negative matrix, cross-tenant 404s, protected-property injection, step-up enforcement, stale role after downgrade, RLS leakage.
Exit gate: all of the above green; no secrets in repo (gitleaks); primitives screenshot-approved by design-reviewer in light/dark/reduce-transparency.
Close-out.
```

## PROMPT 3 — Phase 2: Core workflow
```
Execute Phase 2 (§20) using MASTER_PROMPT F-02, F-03, F-04, F-09, F-20, F-24, F-25 and §7 machines 1, 3, 7.
Build institution registry import + onboarding workflow, instrument drafts/versions/submit with receipts, the full upload pipeline (quarantine → checks → ClamAV → sanitise → hash → vault) with EICAR/zip-bomb/magic-byte tests, intake/scrutiny queues and assignment, observations with institution-visible vs internal comments, receipts with signed QR (pyHanko + Ed25519; never call it eSign), and the web screens + mobile screens for these flows.
Every state change writes state_transitions + audit + outbox in one transaction. Generated exhaustive transition tests for each machine.
Exit gate: SPEC §18.1 scenarios 1, 2, 6 and the PS scenario "new FDR submission" pass end-to-end on staging config (synthetic data, banner visible); no silent overwrite possible (prove with tests).
Close-out.
```

## PROMPT 4 — Phase 3: Evidence and verification
```
Execute Phase 3 (§20) using MASTER_PROMPT F-05, F-06, F-07, F-08 and §14.1 (OCR part only; no LLM required yet).
Build local OCR with page/region/confidence provenance and the side-by-side review UI; verification requests + bank-verifier portal role (isolated, signed responses, MFA) + independent evidence decision; statement import for MT940 (mt-940), CAMT.053 (pycamt), CSV/XLSX with mapping versions; deterministic reconciliation with ruleset versions, exceptions queue and compensating events; the discrepancy engine with versioned rules that create flags/draft observations, never rejections.
Honest-state UI everywhere: not configured / unavailable / pending source / evidence received / human verified.
Exit gate: SPEC §18.1 scenarios 3, 4, 5 and PS scenario "discrepancy identification" pass; prove that no code path sets Bank-confirmed or Ledger-reconciled without the required evidence/reviewer (property test + review).
Close-out.
```

## PROMPT 5 — Phase 4: Lifecycle and release
```
Execute Phase 4 (§20) using MASTER_PROMPT F-10, F-11, F-12, F-13, F-16 (the lifecycle and release cards) and §7 machines 4, 5.
Build the policy registry with draft-only imports from config/policy-drafts (APH Table 1.4, Clause 6.46 checklist, example reminder schedule) and BLOCKED penalty entries; the DB-leased scheduler with heartbeat and idempotent reminders; escalation (never state-changing); renewal lineage with gap/overlap handling; release requests with the policy-built checklist (SATISFIED / NOT SATISFIED / PENDING SOURCE / NOT APPLICABLE), clearances as separate records, recommendation ≠ requester, competent-authority decision with delegation limits + step-up MFA, EXECUTION_PENDING until trusted execution evidence is recorded and independently reviewed.
Exit gate: SPEC §18.1 scenarios 7, 8, 9 and PS scenarios "validity tracking", "approaching maturity", "renewal", "authorised release" pass; same-person maker/checker denied at API and DB; no approved schedule ⇒ explicit admin alert (not invented reminders).
Close-out.
```

## PROMPT 6 — Phase 5: Notifications and realtime
```
Execute Phase 5 (§20) using MASTER_PROMPT §10 and F-14/F-15, §9A M-01, M-02, M-16.
Build the outbox consumer, recipient resolution from current scope, inbox-first persistence, templates (versioned, localised, reviewed-only), FCM HTTP v1 adapter (Android), APNs token-auth adapter (iOS), Web Push (VAPID), e-mail adapter (disabled until configured), preferences, device lifecycle, test-notification endpoint, DLQ + admin viewer, funnel metrics, SSE with Last-Event-ID replay and per-event re-authorisation, mobile and web clients for all of the above.
Verify on real devices where credentials exist; where they don't, mark `blocked: <reason>` in docs/PREFLIGHT.md and prove the inbox + SSE path and the "not configured" UI.
Exit gate: scenarios 10 and 14; logout ⇒ previous user's token receives nothing; forged deep link ⇒ safe 404; lock-screen payload contains no sensitive values (tested with canary strings).
Close-out.
```

## PROMPT 7 — Phase 6: Web app completion
```
Execute Phase 6 (§20): complete every web screen in MASTER_PROMPT §11 with the design system in §13.1–13.2 and design/DESIGN_SPEC.md. Dashboard + reports + exports (F-16), search + saved views (F-17), help/support (F-21), rights/retention (F-22), admin consoles (F-19), auditor workspace (F-18), public receipt verification (F-20), PWA install + web push.
Visual QA matrix: Playwright screenshots at 390/768/1280/1920 px × light/dark/reduced-transparency × en/hi/ta; axe-core clean; keyboard-only walkthrough scripted. design-reviewer must sign off; fix every finding.
Close-out.
```

## PROMPT 8 — Phase 7: Mobile app completion
```
Execute Phase 7 (§20): complete the mobile app so every web capability has a mobile counterpart (generate docs/PARITY_MATRIX.md in CI) and implement every item M-01…M-21 in MASTER_PROMPT §9A.
iOS: native tabs, SwiftUI via @expo/ui, expo-glass-effect on iOS 26+ with graceful fallback, SF Symbols via expo-symbols. Android: Material 3 via @expo/ui Jetpack Compose (or the S-02 fallback), brand colour scheme, Material Symbols for EVERY icon (add the lint rule that fails on any other icon source), adaptive layouts for tablets/foldables.
Run Maestro/Detox flows for the six PS scenarios on emulator/simulator and smoke on real devices where available. Provide screenshots per platform/size/theme.
Close-out.
```

## PROMPT 9 — Phase 8: AI/OCR gateway
```
Execute Phase 8 (§20) using MASTER_PROMPT §14, F-26 and config/LLM_PROVIDERS.yaml.
Build the gateway (registry, token buckets, circuit breakers, ordered failover, local fallback, redaction, schema validation, metadata-only logging, kill switch), policy Q&A with citation resolver, gated case summaries, machine-translation drafts for human review, eval harness and adversarial test pack. Verify every provider's current free-tier terms/limits/model IDs from its official docs before enabling and record them in docs/ai-evals/PROVIDERS_VERIFIED.md; leave unverifiable providers disabled. Tier S stays local-only unless OPEN_DECISIONS D-12 says otherwise.
Exit gate: with all providers disabled the product is fully usable and the AI features show "unavailable"; failover proven by killing providers one by one; injection pack green.
Close-out.
```

## PROMPT 10 — Phase 9: Hardening and compliance
```
Execute Phase 9 (§20): run the full security checklist (§17.3) and fix findings; ASVS/API/MASVS traceability CSV; load test with k6 (record, don't invent SLAs); restore drill with hash/count/key reconciliation; chaos-lite scenarios; write all runbooks (§18); GIGW checklist; DPDP matrix scaffold; KNOWN_LIMITATIONS.md; DEMO_SCRIPT.md for the six PS scenarios with baseline-first metric definitions.
Then run spec-auditor across the whole SPEC_v3 and the ten PS capabilities and produce docs/FINAL_AUDIT.md listing every requirement as Done / Partial / Blocked (with reason) and the evidence link.
Close-out.
```

## PROMPT X — Final independent audit (fresh session)
```
You are an independent auditor. Do not trust previous reports. Using only the repository, run `make verify`, the Playwright and mobile suites, and the production-guard test. Then verify: (1) no demo/mock/simulated path exists in production code or images; (2) every SPEC §18.1 scenario and every PS scenario has a passing automated test; (3) the role×action×scope matrix test is exhaustive; (4) no UI shows "verified/confirmed/reconciled" without the evidence record; (5) icon sources: Android uses only Material Symbols, iOS only SF Symbols, web only the chosen open set; (6) no secrets, no sensitive values in logs or push payloads; (7) docs/KNOWN_LIMITATIONS.md matches reality. Produce a defect list ranked by severity with reproduction steps. Fix nothing; report only.
```
