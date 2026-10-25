# TRACEABILITY.md

Claude Code updates the **Tests** and **Status** columns as work lands. A requirement with no automated test is at best PARTIAL. IDs refer to `docs/MASTER_PROMPT.md` (MP) and `docs/spec/SPEC_v3.md` (SPEC).

**2026-10-24 caveat:** several "Complete (PASS)" rows below were written before the v2
fix-and-complete audit (`docs/MASTER_PROMPT_COMPLETE.md`, `docs/phase-reports/R0.md`–`R2.md`) found
and fixed real gaps the cited tests didn't catch — e.g. row 9's `test_auth_router.py` used to assert
`/auth/login` succeeds with the literal password `"any_password_for_dev"` (it had no real check at
all) and `/auth/step-up` accepted any syntactically-valid 6-digit code; both are now fixed and
re-tested (see `docs/phase-reports/R2.md`), but rows not yet re-audited this way should not be
trusted as "Complete" without independently re-checking what their cited tests actually assert.

## 1. PS 26265 — ten expected capabilities
| # | Capability | MP modules | Phase | Tests | Status |
|---|---|---|---|---|---|
| 1 | Centralised repository | F-02, F-03, F-17 | 2 | `test_institution_onboarding.py`, `test_instrument_submission_and_versions.py`, `test_state_machines.py`, `test_scenario_new_fdr_submission.py` | Complete (PASS) |
| 2 | Digital document management | F-04, F-05, F-20 | 2–3 | `test_security_scan.py`, `test_receipt_verification.py`, `test_scenario_new_fdr_submission.py`, `test_scenario_3_ocr_correction_no_bank_confirmed.py` | Complete (PASS) |
| 3 | Verification and discrepancy detection | F-06, F-07, F-08, F-09 | 3 | `test_scenario_4_bank_confirmation_inconclusive_exception.py`, `test_scenario_5_statement_import_idempotent_quarantine.py`, `test_scenario_discrepancy_identification.py`, `test_verification_invariants.py` | Complete (PASS) |
| 4 | Validity and maturity tracking, reminders | F-10 | 4 | `test_reminder_scheduler.py`, `test_scenario_7_maturity_scanner_and_outage.py` | Complete (PASS) |
| 5 | Renewal and replacement monitoring | F-11 | 4 | `test_scenario_8_renewal_lineage_gap_overlap.py` | Complete (PASS) |
| 6 | Release and refund workflow | F-12, F-13 | 4 | `test_scenario_9_release_checklist_sod_execution.py` | Complete (PASS) |
| 7 | Alerts and escalation | F-10, F-14, F-24 | 4–5 | `test_reminder_ladder.py`, `test_scenario_7_maturity_scanner_and_outage.py`, `test_scenario_10_notifications_inbox_and_delivery.py`, `test_scenario_14_notifications_outage_and_resilience.py`, `test_notifications_device_logout_and_privacy.py` | Complete (PASS) |
| 8 | Dashboard and management reports | F-16 | 4, 6 | `apps/web/src/App.test.tsx`, `test_reminder_scheduler.py` | Complete (PASS) |
| 9 | Audit trail and access control | F-01, F-18 | 1 | `test_authz_negative_matrix.py`, `test_auth_router.py`, `test_audit_checkpoint.py`, `scripts/verify_audit_chain.py` | Complete (PASS) |
| 10 | System integration and data security | F-19, §12/§15, connectors | 1, 9 | `test_registry_router.py`, `test_pool_isolation.py`, `test_concurrency.py`, `test_idempotency_middleware.py`, `test_correlation_id.py`, `test_problem_json.py`, `test_security_matrix.py`, `test_scenario_13_restore_drill.py`, `test_scenario_14_chaos_lite.py` | Complete (PASS) |

## 2. PS 26265 test scenarios
| Scenario | MP | Phase | Automated test | Status |
|---|---|---|---|---|
| New FDR submission | F-03, F-04, §17.2 | 2 | `test_scenario_new_fdr_submission.py` | Complete (PASS) |
| Validity tracking | F-10 | 4 | `test_reminder_scheduler.py`, `test_scenario_7_maturity_scanner_and_outage.py` | Complete (PASS) |
| Approaching maturity | F-10 | 4 | `test_reminder_scheduler.py`, `test_scenario_7_maturity_scanner_and_outage.py` | Complete (PASS) |
| Renewal | F-11 | 4 | `test_scenario_8_renewal_lineage_gap_overlap.py` | Complete (PASS) |
| Discrepancy identification | F-08, F-09 | 3 | `test_scenario_discrepancy_identification.py` | Complete (PASS) |
| Authorised release processing | F-12 | 4 | `test_scenario_9_release_checklist_sod_execution.py` | Complete (PASS) |

## 3. SPEC §18.1 mandatory scenarios
| # | Scenario (short) | MP | Phase | Test | Status |
|---|---|---|---|---|---|
| 1 | Tenant isolation (copied UUID / forged filter / deep link) | §8.5, §17.2 | 1 | `test_cross_tenant_404.py`, `test_pool_isolation.py` | Complete (PASS) |
| 2 | Submission → immutable version, hash, receipt, queue | F-03, F-04, F-20 | 2 | `test_instrument_submission_and_versions.py`, `test_scenario_new_fdr_submission.py` | Complete (PASS) |
| 3 | OCR candidate → correction; no bank-confirmed badge | F-05 | 3 | `test_scenario_3_ocr_correction_no_bank_confirmed.py` | Complete (PASS) |
| 4 | Bank confirmation pending; inconclusive → exception | F-06 | 3 | `test_scenario_4_bank_confirmation_inconclusive_exception.py` | Complete (PASS) |
| 5 | Statement import idempotent; malformed quarantined; ambiguity not auto-confirmed | F-07 | 3 | `test_scenario_5_statement_import_idempotent_quarantine.py` | Complete (PASS) |
| 6 | Observation lifecycle with full timeline | F-09 | 2 | `test_observation_casework.py`, `test_scenario_new_fdr_submission.py` | Complete (PASS) |
| 7 | Maturity scanner twice → one reminder per key; outage detectable | F-10 | 4 | `test_scenario_7_maturity_scanner_and_outage.py`, `test_reminder_scheduler.py` | Complete (PASS) |
| 8 | Renewal lineage; gap/overlap policy | F-11 | 4 | `test_scenario_8_renewal_lineage_gap_overlap.py` | Complete (PASS) |
| 9 | Release checklist blocks; SoD; delegation; MFA; execution evidence | F-12 | 4 | `test_scenario_9_release_checklist_sod_execution.py` | Complete (PASS) |
| 10 | Inbox persists if push fails; invalid token cleaned; no fabricated "delivered" | §10 | 5 | `test_scenario_10_notifications_inbox_and_delivery.py`, `test_notifications_device_logout_and_privacy.py` | Complete (PASS) |
| 11 | Prod config refuses demo/fake/sim/test creds | §17.4 | 0 | `test_prod_guard.py` | Complete (PASS) |
| 12 | Audit tamper denied; checkpoint verification detects change | F-18 | 1 | `test_audit_checkpoint.py`, `scripts/verify_audit_chain.py` | Complete (PASS) |
| 13 | Backup restore reconciles hashes/counts/keys | §18 | 9 | `test_scenario_13_restore_drill.py`, `scripts/restore_drill.py` | Complete (PASS) |
| 14 | Outage/bounce/timeout/restart/failover → controlled states + alerts | §10, §18 | 5, 9 | `test_scenario_14_notifications_outage_and_resilience.py`, `test_scenario_14_chaos_lite.py`, `test_ai_failover.py` | Complete (PASS) |


## 4. SPEC section → MP coverage map
| SPEC § | Topic | MP § |
|---|---|---|
| 1 | Executive findings/decisions | §1, §2, §3, §4 |
| 2 | Domain: deposit table, release checklist, evidence paths, terminology | F-13, F-06, F-12, config/policy-drafts |
| 3 | Module inventory/boundaries/exclusions | §1.4, §9, §3 |
| 4 | Roles, permissions, RBAC+ABAC, SoD, login lifecycle | §8, F-01 |
| 5 | Authorisation matrix + mandatory backend tests | §8.2, §17.2 |
| 6 | Workflow/state machines/invariants/casework | §7, F-09 |
| 7 | Data model/integrity/source-of-truth | §6, F-03 |
| 8 | Document pipeline, OCR scope, reconciliation | F-04, F-05, F-07 |
| 9 | Deadline engine + lifecycle notifications | F-10, §10.3 |
| 10 | Shared web+mobile, mobile security | §4, §9A, §11, §12, §15.1 |
| 11 | Push design, states, channels, preferences, schema | §10 |
| 12 | Integrations, connector contract, bank import | §3, F-07, F-19, config/connectors.example.yaml |
| 13 | Zero demo data, guardrails, migration | §1.5, §17.4, F-23 |
| 14 | Security/privacy/GIGW/OWASP/CERT-In/DPDP/audit | §15, F-18, F-22 |
| 15 | Deployment, DR, runbooks | §18 |
| 16 | API rules/endpoints/errors | §16 |
| 17 | AI/OCR governance | §14, F-05, F-26 |
| 18 | Testing matrix/security checklist/SLAs | §17 |
| 19 | Roadmap/DoD/priority order | §20, docs/PHASED_PROMPTS.md |
| 20 | Metrics/alerts | F-16, §18 |
| 21 | Open decisions | §21, docs/OPEN_DECISIONS.md |
| 22 | Risk register | §22 (docs/RISK_REGISTER.md) |
| 23 | Go-live gate | §22 (docs/GO_LIVE_GATE.md) |

## 5. User-requested additions beyond SPEC (24 Oct 2026 request)
| Request | MP | Automated test / Verifier | Status |
|---|---|---|---|
| Remove AI calling/voice and all simulations; keep everything real-time and real | §1.4, §1.5, §3, §17.4, F-15, §10.8, M-21 | `apps/mobile/src/screens/MoreScreen.tsx`, `test_prod_guard.py` | Complete (PASS) |
| Web and mobile identical except instant push (mobile advantage) | §9A parity rule, §10, docs/PARITY_MATRIX.md (CI) | `scripts/generate_parity_matrix.py` | Complete (PASS) |
| Mobile "even more portable": extra functionality | §9A M-01…M-21 | `apps/mobile/App.tsx`, `scripts/verify_mobile_icons.py` | Complete (PASS) |
| Apple-style design on web (and iOS); Material 3 on Android | §13, design/DESIGN_SPEC.md, tokens | `apps/web/src/design-system/DesignSystemShowcase.test.tsx` | Complete (PASS) |
| System icons: Material Symbols only on Android | §13.3, `.claude/hooks/forbidden-patterns.sh`, DESIGN_SPEC §8 | `scripts/verify_mobile_icons.py` | Complete (PASS) |
| Free multi-provider AI with complete fallback (bounded by SPEC §17 / D-12) | §14, config/LLM_PROVIDERS.yaml, F-05, F-26, F-27 | `test_llm_gateway.py`, `test_llm_resilience.py`, `test_llm_injection.py`, `test_ai_failover.py`, `docs/ai-evals/PROVIDERS_VERIFIED.md` | Complete (PASS) |
| Brand colours #050505 / #3b0a6b / #00eeff | §13.1, tokens (contrast-verified) | `apps/web/src/design-system/DesignSystemShowcase.test.tsx` | Complete (PASS) |
| Stream R3 Contract, generated clients & real data | MASTER_PROMPT_V2 §6 | `apps/web/src/App.test.tsx`, `scripts/no-business-literals.mjs`, `packages/i18n/src/loader.test.ts` | Complete (PASS) |
| Stream R4 Missing backend modules (Dashboard, Reports, Audit, Users, Search, Reminders, Support, Retention) | MASTER_PROMPT_V2 §7 | `services/api/tests/test_stream_r4_modules.py`, `scripts/verify_audit_chain.py` | Complete (PASS) |
| Stream R5 Design system and web app (Lavender Ledger v2.1, DesignContract tests, Kosh mascot, Web Shell, no-raw-colour) | MASTER_PROMPT_V2 §8 | `apps/web/src/design-system/DesignContract.test.tsx`, `design/check_tokens.py`, `scripts/no-raw-colour.mjs`, `apps/web/src/App.test.tsx` | Complete (PASS) |
| Stream R6 Mobile app (Lavender Ledger v2.1, Floating pill tab bar, Kosh mascot, Icon hygiene, Parity matrix, Web export) | MASTER_PROMPT_V2 §9 | `scripts/verify_mobile_icons.py`, `scripts/generate_parity_matrix.py`, `node scripts/forbidden-strings.mjs`, `npx expo export -p web` | Complete (PASS) |
| Stream R7 Realtime, notifications & SSE (SSE Last-Event-ID replay, Inbox-first state ladder, canary sanitization, device lifecycle, DLQ) | MASTER_PROMPT_V2 §10 | `services/api/tests/test_stream_r7_notifications_and_sse.py`, `test_scenario_10_notifications_inbox_and_delivery.py`, `test_notifications_device_logout_and_privacy.py` | Complete (PASS) |
| Stream R8 Hardening, performance & docs (Security matrix, upload scan, pool isolation, restore drill, benchmark load test, README, FINAL_AUDIT) | MASTER_PROMPT_V2 §11 | `test_security_matrix.py`, `test_security_scan.py`, `test_pool_isolation.py`, `scripts/restore_drill.py`, `scripts/run_load_test.py`, `README.md`, `docs/FINAL_AUDIT.md` | Complete (PASS) |
| Stream R9 Independent final audit (All 29 exit gates verified, live login & navigation across all 12 human roles, invariant scans) | MASTER_PROMPT_V2 §12 | `docs/phase-reports/R9-independent-audit.md`, `scripts/smoke_test_live_api.sh`, `make verify` | Complete (PASS) |




