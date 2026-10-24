# TRACEABILITY.md

Claude Code updates the **Tests** and **Status** columns as work lands. A requirement with no automated test is at best PARTIAL. IDs refer to `docs/MASTER_PROMPT.md` (MP) and `docs/spec/SPEC_v3.md` (SPEC).

## 1. PS 26265 — ten expected capabilities
| # | Capability | MP modules | Phase | Tests | Status |
|---|---|---|---|---|---|
| 1 | Centralised repository | F-02, F-03, F-17 | 2 | `test_institution_onboarding.py`, `test_instrument_submission_and_versions.py`, `test_state_machines.py`, `test_scenario_new_fdr_submission.py` | Complete (PASS) |
| 2 | Digital document management | F-04, F-05, F-20 | 2–3 | `test_security_scan.py`, `test_receipt_verification.py`, `test_scenario_new_fdr_submission.py` | Phase 2 Complete (PASS) |
| 3 | Verification and discrepancy detection | F-06, F-07, F-08, F-09 | 3 | — | Not started |
| 4 | Validity and maturity tracking, reminders | F-10 | 4 | — | Not started |
| 5 | Renewal and replacement monitoring | F-11 | 4 | — | Not started |
| 6 | Release and refund workflow | F-12, F-13 | 4 | — | Not started |
| 7 | Alerts and escalation | F-10, F-14, F-24 | 4–5 | — | Not started |
| 8 | Dashboard and management reports | F-16 | 4, 6 | — | Not started |
| 9 | Audit trail and access control | F-01, F-18 | 1 | `test_authz_negative_matrix.py`, `test_auth_router.py`, `test_audit_checkpoint.py`, `scripts/verify_audit_chain.py` | Complete (PASS) |
| 10 | System integration and data security | F-19, §12/§15, connectors | 1, 9 | `test_registry_router.py`, `test_pool_isolation.py`, `test_concurrency.py`, `test_idempotency_middleware.py`, `test_correlation_id.py`, `test_problem_json.py` | Phase 1 Complete (PASS) |

## 2. PS 26265 test scenarios
| Scenario | MP | Phase | Automated test | Status |
|---|---|---|---|---|
| New FDR submission | F-03, F-04, §17.2 | 2 | `test_scenario_new_fdr_submission.py` | Complete (PASS) |
| Validity tracking | F-10 | 4 | — | Not started |
| Approaching maturity | F-10 | 4 | — | Not started |
| Renewal | F-11 | 4 | — | Not started |
| Discrepancy identification | F-08, F-09 | 3 | — | Not started |
| Authorised release processing | F-12 | 4 | — | Not started |

## 3. SPEC §18.1 mandatory scenarios
| # | Scenario (short) | MP | Phase | Test | Status |
|---|---|---|---|---|---|
| 1 | Tenant isolation (copied UUID / forged filter / deep link) | §8.5, §17.2 | 1 | `test_cross_tenant_404.py`, `test_pool_isolation.py` | Complete (PASS) |
| 2 | Submission → immutable version, hash, receipt, queue | F-03, F-04, F-20 | 2 | `test_instrument_submission_and_versions.py`, `test_scenario_new_fdr_submission.py` | Complete (PASS) |
| 3 | OCR candidate → correction; no bank-confirmed badge | F-05 | 3 | — | Not started |
| 4 | Bank confirmation pending; inconclusive → exception | F-06 | 3 | — | Not started |
| 5 | Statement import idempotent; malformed quarantined; ambiguity not auto-confirmed | F-07 | 3 | — | Not started |
| 6 | Observation lifecycle with full timeline | F-09 | 2 | `test_observation_casework.py`, `test_scenario_new_fdr_submission.py` | Complete (PASS) |
| 7 | Maturity scanner twice → one reminder per key; outage detectable | F-10 | 4 | — | Not started |
| 8 | Renewal lineage; gap/overlap policy | F-11 | 4 | — | Not started |
| 9 | Release checklist blocks; SoD; delegation; MFA; execution evidence | F-12 | 4 | — | Not started |
| 10 | Inbox persists if push fails; invalid token cleaned; no fabricated "delivered" | §10 | 5 | — | Not started |
| 11 | Prod config refuses demo/fake/sim/test creds | §17.4 | 0 | `test_prod_guard.py` | Complete (PASS) |
| 12 | Audit tamper denied; checkpoint verification detects change | F-18 | 1 | `test_audit_checkpoint.py`, `scripts/verify_audit_chain.py` | Complete (PASS) |
| 13 | Backup restore reconciles hashes/counts/keys | §18 | 9 | — | Not started |
| 14 | Outage/bounce/timeout/restart/failover → controlled states + alerts | §10, §18 | 5, 9 | — | Not started |


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
| Request | MP |
|---|---|
| Remove AI calling/voice and all simulations; keep everything real-time and real | §1.4, §1.5, §3, §17.4, F-15, §10.8, M-21 |
| Web and mobile identical except instant push (mobile advantage) | §9A parity rule, §10, docs/PARITY_MATRIX.md (CI) |
| Mobile "even more portable": extra functionality | §9A M-01…M-21 |
| Apple-style design on web (and iOS); Material 3 on Android | §13, design/DESIGN_SPEC.md, tokens |
| System icons: Material Symbols only on Android | §13.3, `.claude/hooks/forbidden-patterns.sh`, DESIGN_SPEC §8 |
| Free multi-provider AI with complete fallback (bounded by SPEC §17 / D-12) | §14, config/LLM_PROVIDERS.yaml |
| Brand colours #050505 / #3b0a6b / #00eeff | §13.1, tokens (contrast-verified) |
