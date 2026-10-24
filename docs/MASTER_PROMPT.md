# MASTER PROMPT — AICTE Security Deposit / FDR Management Portal
**Smart India Hackathon PS 26265 · AICTE Regulation Bureau · Theme: Smart Automation**
**Target builder: Claude Code · Version 1.0 · Written 24 Oct 2026 · Derived from `docs/spec/SPEC_v3.md` (23 Oct 2026) and the PS 26265 problem statement**

> Paste this whole file as the first message to Claude Code (in Plan Mode), after placing the files from this package in the repository root as described in `README.md`. Then drive the build with `docs/PHASED_PROMPTS.md`. Section IDs (§x.y) are stable; refer to them in commits and in `docs/TRACEABILITY.md`.

---

## §0. How you (Claude Code) must operate

You are the lead engineer building a production-grade, government-facing financial-compliance system. Treat the following as binding:

1. **Read first.** Before writing code, read in full: `CLAUDE.md`, this file, `docs/spec/SPEC_v3.md`, `docs/spec/PS26265_problem_statement.txt`, `docs/VERIFY_AT_BUILD.md`, `design/DESIGN_SPEC.md`. Summarise your understanding in `docs/PLAN.md` (≤2 pages): scope, phases, risks, and any contradiction you found. If two sources contradict, **stop and ask**; do not pick silently.
2. **Plan Mode → approval → build.** Present the plan, wait for approval, then execute phase by phase (`docs/PHASED_PROMPTS.md`). Each phase ends with an exit gate (§20). Do not begin the next phase until the gate passes with evidence.
3. **Verify, don't recall.** For every external library, SDK, cloud API or platform capability, read the official documentation for the *exact version you pin* before coding against it. Write the pinned version and doc URL in `docs/STACK_LOCK.md`. Anything in `docs/VERIFY_AT_BUILD.md` needs a recorded check. If a documented capability is missing in the pinned version, use the stated fallback — do not fabricate an API.
4. **Never fake it.** If something cannot be real in this environment (no bank credentials, no Apple account, no FCM project), build the real workflow around it, surface the state honestly in the UI ("not configured"), and add it to `docs/PREFLIGHT.md`. Do not return success from a stub in any non-test code path.
5. **Prove it.** "Done" means: tests written and passing, `make verify` green, migrations apply and roll back, OpenAPI regenerated, UI screenshotted at phone + tablet + desktop in light/dark/reduce-transparency, accessibility checks run, and the traceability matrix updated. Report failures plainly.
6. **Use subagents** from `.claude/agents/` — `reviewer` (reads diffs cold), `security-auditor` (authz/BOLA/RLS/secrets), `design-reviewer` (visual + a11y + platform conformance), `spec-auditor` (checks work against SPEC_v3 and this file). Run `reviewer` + `security-auditor` before closing every phase, and `spec-auditor` at the end of every phase.
7. **Ask only when blocked on a genuine decision** (an AICTE business rule, a credential you cannot obtain, or a contradiction). Otherwise choose the safe default the spec prescribes and record it in `docs/OPEN_DECISIONS.md`.
8. **No mistakes policy.** You cannot guarantee zero defects; you *can* make them detectable. Therefore every business rule has an automated test; every authz rule has a negative test; every state machine has an exhaustive transition test; every migration has an up/down test; every provider path has a failure test.

---

## §1. Mission, users, scope

### §1.1 Mission
Replace fragmented spreadsheets, e-mail and manual tracking of institutions' security deposits and FDRs with a **secure, centralised case-management and system-of-record platform** for the AICTE Regulation Bureau and authorised stakeholders. It tracks each obligation and the *evidence* supporting it across its lifecycle: submission → intake → scrutiny → evidence verification → active tracking → maturity/validity → renewal/replacement → release/refund request → decision → execution evidence → closure. Everything is auditable, role-scoped, and real.

### §1.2 The ten capabilities required by PS 26265 (each must be demonstrably complete)
| # | PS capability | Primary modules |
|---|---|---|
| 1 | Centralised Security Deposit/FDR repository (institution-wise, instrument-wise) | F-02, F-03, F-17 |
| 2 | Digital document management (secure upload/store/retrieve/review) | F-04, F-05, F-20 |
| 3 | Verification and discrepancy detection (authorised sources; flag missing/inconsistent) | F-06, F-07, F-08, F-09 |
| 4 | Automated validity and maturity tracking, advance reminders | F-10 |
| 5 | Renewal and replacement monitoring with complete history | F-11 |
| 6 | Release and refund workflow per regulation and authorised procedure | F-12, F-13 |
| 7 | Automated alerts and escalation (pending verification, deadlines, overdue, unresolved) | F-10, F-14, F-24 |
| 8 | Dashboard and management reports (active, expiring, matured, renewed, released, pending) | F-16 |
| 9 | Audit trail and access control | F-01, F-18 |
| 10 | System integration and data security (authorised integration; protect confidential data) | F-19, §15, §12 connectors |

### §1.3 Users (13 roles; see §8.2)
Institution Organisation Administrator · Institution Submitter/Compliance Officer · Institution Viewer · Intake/Registry Officer · Scrutiny Officer · Finance/Verification Officer · Regional Supervisor/Bureau Reviewer · Competent Authority/Release Approver · Audit/Compliance Reviewer · Identity/Access Administrator · Platform/Security Operator · Integration service identity · Participating Bank Verifier (conditional, disabled until onboarding is approved).

### §1.4 Explicitly excluded (do not build, do not stub, do not mention in UI)
AI voice agent / AI calling / telephony / WebRTC / speech-to-text or text-to-speech / call PINs / recordings / transcripts. Demo or simulated clock in production. Mock data seeding in production. AI-generated release decisions, "genuine FDR" declarations or unreviewed policy inference. Premature microservices, multi-agent orchestration, unconstrained text-to-SQL, black-box risk scores. SMS/WhatsApp adapters (feature-flag registry entries only, status `disabled`, until D-10 provisioning exists). BG/SFMS/NeSL/e-BG integration (registry entry `disabled`, until D-07). DigiLocker/eSign/API Setu/Parichay (registry entries `disabled`; no fake signed certificates).

### §1.5 What "real, working, real-time" means here
- **Real** = every user-visible state is derived from persisted data or an observed external result. No placeholder numbers, no canned responses, no fake delivery receipts.
- **Real-time** = changes made by one user appear on other users' open screens within seconds via Server-Sent Events (§10.8), and mobile users additionally receive push notifications (§10). The persistent inbox is the source of truth for anything missed.
- **No universal public FDR-verification API exists** (SPEC §1.4, §12). "Real verification" therefore means these real mechanisms: (a) authorised **statement import** (MT940/CAMT.053/CSV/XLSX) with deterministic reconciliation; (b) **bank-verifier portal role** where a participating bank's authenticated verifier responds to a confirmation request with signed/attached evidence; (c) **evidence recording** of bank-issued confirmations by a Finance/Verification Officer with independent review; (d) connector **plug-in points** that appear "not configured" until a named owner, route and credentials exist.
- **Staging/UAT and hackathon demo** run with synthetic, clearly labelled data (a persistent "STAGING — SYNTHETIC DATA" banner) in a separate environment (SPEC §13.1). They are the same code with `APP_ENV=staging`; the *clock is still real* (create instruments whose maturity is N days from today to exercise the six PS test scenarios). Time-travel exists only in automated tests.

---

## §2. Principles (P1–P20; each is testable)
P1 One authoritative backend and DB; clients never hold business rules. · P2 Every financial/policy fact has provenance (who, source, version reviewed, decision, when). · P3 Evidence is a set of attributes, never one score. · P4 No "verified" from OCR/AI/declaration/file presence. · P5 Maturity ≠ release permission. · P6 Separate linked state machines. · P7 RBAC + ABAC + RLS, default deny. · P8 Maker-checker and step-up MFA for consequential actions. · P9 Transactional outbox for all side effects. · P10 Idempotency keys on every state-changing endpoint and import. · P11 Append-only history; submitted versions are never overwritten. · P12 Policy is versioned config with citations; decisions pin the version. · P13 AI is a bounded assistant; fail closed to manual. · P14 Honest states for unavailable integrations. · P15 Privacy by design: minimal payloads, masked identifiers, no sensitive data in logs/push/telemetry. · P16 Accessibility (WCAG 2.1 AA minimum, 2.2 target) on web and mobile. · P17 Web and mobile share contract, schemas, i18n, permissions, error model, tokens. · P18 Server clock is the only clock; timezone Asia/Kolkata for business dates. · P19 Everything observable: request IDs, metrics, structured logs, health. · P20 Production hardening is part of the feature, not a later phase.

---

## §3. Reality matrix — connector and feature states

Implement a **feature/connector registry** (table + admin UI + API) with states `disabled | sandbox-only | production-enabled | degraded`. Only a user holding `configure_integrations` plus an independent approver (maker-checker) can set `production-enabled`, and only after an `acceptance_evidence` attachment exists. UI badges read from this registry. Initial entries and their honest default state:

| Connector / feature | Default | Real behaviour when enabled | Behaviour while not enabled |
|---|---|---|---|
| In-app inbox + SSE | production-enabled | DB-backed | n/a |
| Android push (FCM HTTP v1) | disabled until `FCM_*` configured | Direct send, token lifecycle | Banner "Push not configured"; inbox works |
| iOS push (APNs token auth, HTTP/2) | disabled until `.p8` + team/key/bundle configured | Direct send | Same |
| Web push (VAPID) | disabled until keys configured | Service worker + subscription | Same |
| E-mail | disabled until verified sender + SPF/DKIM/DMARC | SMTP/API with bounce handling | "E-mail not configured" |
| SMS / WhatsApp | disabled (no adapter) | — | Hidden from preferences |
| Statement import (MT940/CAMT.053/CSV/XLSX) | production-enabled | Parse, validate, reconcile | n/a |
| Bank-verifier portal | disabled until a bank is onboarded | Signed responses, scoped access | "Awaiting bank onboarding" |
| AICTE institution registry API | disabled | Sync by official ID | Authorised CSV import with provenance |
| Financial execution system | disabled | Record trusted execution reference | Release stays `EXECUTION_PENDING` |
| OCR (local engine) | production-enabled after accuracy baseline | Candidates only | Manual entry; label "Extraction unavailable" |
| LLM gateway — Tier P (public policy text) | sandbox-only by default | Cited answers | Feature hidden/"unavailable" |
| LLM gateway — Tier S (real case data) | **disabled** until D-12 | Local model only unless AICTE approves a provider | Feature hidden |
| BG/e-BG/SFMS/NeSL, DigiLocker, eSign, Parichay | disabled | not built | Hidden |

---

## §4. Architecture and stack

### §4.1 Shape
Modular monolith (one deployable FastAPI backend with strict internal domain packages), PostgreSQL, S3-compatible encrypted object store, durable outbox + worker/scheduler, OIDC identity provider. Two clients on one OpenAPI contract. No microservices.

```
Web (React) ─┐                       ┌─ Postgres (RLS, pgvector, FTS, outbox)
             ├─ HTTPS/OpenAPI ─ API ─┼─ Object store (MinIO/S3, SSE-encrypted, quarantine + vault)
Mobile (RN) ─┘   + SSE stream    │   ├─ Worker (outbox, scheduler, OCR, scanner, reconciliation)
                                 │   └─ Providers: FCM · APNs · Web Push · SMTP · LLM gateway
                         Keycloak (OIDC, PKCE, MFA, passkeys)
```

### §4.2 Stack (versions: resolve latest *stable* at build time, pin, and record in `docs/STACK_LOCK.md`)
| Layer | Choice | Notes |
|---|---|---|
| Monorepo | pnpm workspaces + `uv` (Python) + Makefile | `apps/web`, `apps/mobile`, `backend`, `packages/{api-client,schemas,i18n,design-tokens,fixtures}`, `infra`, `docs` |
| Backend | Python (supported stable), FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, `structlog`, `opentelemetry` | Modular packages per domain (§5) |
| DB | PostgreSQL (supported major), `pgcrypto`, `pg_trgm`, `pgvector`, RLS | App role is NOT superuser; migration role separate |
| Queue/worker | Postgres outbox with `FOR UPDATE SKIP LOCKED` + worker process; scheduler as a DB-leased singleton | Celery/Valkey optional later; do not add unless needed |
| Object store | MinIO (S3 API) locally/self-host; any S3-compatible in prod | Buckets: `quarantine`, `vault`, `exports`, `receipts`; SSE; versioning; no public access |
| Identity | Keycloak (OIDC code + PKCE; TOTP + WebAuthn/passkeys; step-up via `acr`/`max_age`) | Business logic must not depend on Keycloak-specific claims (§8.1) |
| Web | React 19 + TypeScript + Vite, Tailwind CSS v4, Radix primitives (shadcn pattern), TanStack Query + Router, react-hook-form + zod, `eventsource-parser` for SSE | PWA (installable) for web push |
| Mobile | Expo (SDK current stable at build time; Node requirement per Expo docs), React Native new architecture, Expo Router (native tabs), `expo-notifications`, `expo-secure-store`, `expo-local-authentication`, `expo-document-picker`, `expo-image-picker`/camera, `expo-file-system`, `expo-sqlite` (+SQLCipher or encrypted wrapper — verify), `expo-linking`, `expo-calendar`, `expo-haptics`, `expo-screen-capture`, `expo-widgets` (verify) | Development builds / EAS, not Expo Go |
| Mobile UI | iOS: `@expo/ui/swift-ui` + `expo-glass-effect` (iOS 26+) + `expo-symbols` (SF Symbols). Android: `@expo/ui/jetpack-compose` (Material 3) + `@expo/material-symbols` (verify package) | See §13.3; spike S-02 decides coverage |
| Shared | OpenAPI → `openapi-typescript`/`orval` client; zod schemas; ICU message catalogue; design tokens package | CI fails if generated client is stale |
| OCR | Local engine(s): PaddleOCR or docTR, Tesseract fallback (Indic language packs) | Page/region/confidence provenance |
| Malware | ClamAV daemon | Plus PDF sanitiser (e.g. `pikepdf`/qpdf rewrite, or `dangerzone`-style rasterise) |
| PII redaction | Microsoft Presidio (+ custom Indian recognisers: PAN, Aadhaar-like, IFSC, account no., FDR no.) | Before any Tier-P external call |
| Signing | `pyHanko` (PDF), Ed25519 for QR payload | Never claim eSign/DSC |
| Observability | OpenTelemetry → Prometheus/Grafana/Loki (self-host) or approved SaaS; Sentry-compatible error tracking w/ scrubbing | No raw documents/tokens to telemetry |
| CI/CD | GitHub Actions (or equivalent), SBOM (syft), Trivy, Semgrep, bandit, pip-audit, `pnpm audit`, gitleaks, OWASP ZAP baseline, Playwright, Maestro (mobile E2E; verify) | See §17–§18 |

**Spike gate (Phase 0).** Before committing to the stack above, run time-boxed spikes and write results to `docs/spikes/`:
- **S-01** Expo SDK/Node/RN version matrix builds on Android + iOS dev builds.
- **S-02** `@expo/ui` Jetpack Compose + SwiftUI coverage for the components in §13 (lists, forms, sheets, date picker, segmented control, search bar, tabs, large title, dialogs). Record what is missing. **Fallback**: hand-built RN components that follow Material 3 / HIG metrics (never a generic cross-platform look).
- **S-03** `expo-glass-effect` + `expo-symbols` behaviour, pre-iOS-26 fallback (blur-material), Reduce Transparency handling.
- **S-04** Push round-trip: FCM HTTP v1 to a real Android device; APNs token-auth to a real iPhone; web push in installed PWA. If no Apple Developer account exists, mark iOS push `blocked: account` in PREFLIGHT and continue.
- **S-05** RLS + connection pool context isolation test (§8.5).
- **S-06** OCR engine accuracy baseline on synthetic FDR-like documents.
- **S-07** Material Symbols packaging on Android (variable font axes, tree-shaking, licence file).

---

## §5. Repository layout (create exactly; extend as needed)

```
/ CLAUDE.md
/ README.md
/ Makefile
/ .claude/{settings.json,agents/,skills/,hooks/}
/ docs/{MASTER_PROMPT.md,PHASED_PROMPTS.md,PLAN.md,STACK_LOCK.md,OPEN_DECISIONS.md,TRACEABILITY.md,PREFLIGHT.md,VERIFY_AT_BUILD.md,spec/,adr/,runbooks/,security/,privacy/,spikes/}
/ backend/app/{core,auth,institutions,instruments,documents,evidence,verification,reconciliation,observations,lifecycle,renewal,release,policy,notifications,realtime,reports,audit,admin,integrations,ai,search,receipts,retention,migration}
/ backend/{alembic/,tests/{unit,integration,authz,e2e,security,contract},pyproject.toml}
/ apps/web/…   / apps/mobile/{app/,src/{ios,android,shared},eas.json,app.config.ts}
/ packages/{api-client,schemas,i18n,design-tokens,fixtures}
/ infra/{docker-compose.yml,docker-compose.staging.yml,keycloak/,minio/,caddy/,prometheus/,grafana/,scripts/}
/ config/{LLM_PROVIDERS.yaml,policy-drafts/,connectors.example.yaml}
/ design/{DESIGN_SPEC.md,tokens.css,tokens.ts}
```
`packages/fixtures` is never imported by `backend/app` or by any production entry point; a CI test greps built artifacts and the Docker image for fixture markers and fails if found.

---

## §6. Domain model

Implement all tables from SPEC §7.1 with Alembic migrations. Additional requirements:

- Every table: `id UUID` (UUIDv7 preferred), `created_at`, `updated_at`, `row_version int` (optimistic concurrency), soft-delete only where retention requires (otherwise none; history is append-only).
- Tenant columns: `institution_id` and (where relevant) `region_id`, with RLS policies and composite indexes.
- Amounts `NUMERIC(18,2)` + `currency CHAR(3)`; dates `DATE`; instants `timestamptz` UTC.
- Identifier columns (FDR number, account number, UTR) stored encrypted at rest (app-level envelope encryption with key id) **plus** a keyed HMAC "blind index" column for exact-match lookup and duplicate detection; display masked (`XXXX1234`) unless the viewer has `view_unmasked_identifiers` in scope and the action is logged.
- `state_transitions` is append-only (revoke UPDATE/DELETE from the app role; trigger as defence in depth).
- `audit_events` hash-chained per partition with periodic signed checkpoints (§F-18).
- `policy_versions` immutable once `approved`; supersession creates a new row.

Additional tables beyond SPEC §7.1 (needed by modules below): `institution_onboarding_requests`, `case_assignments`, `case_comments` (internal vs institution-visible), `clearances` (release clearances from PGRC/Vigilance/other cells), `release_execution_evidence`, `receipt_documents`, `saved_views`, `support_requests`, `rights_requests` (DPDP), `access_recertifications`, `break_glass_sessions`, `feature_registry`, `connector_health_checks`, `notification_preferences`, `notification_templates`, `sse_events` (short-lived replay buffer), `llm_requests` (redacted metadata, no raw text), `translation_catalog_status`, `scheduler_runs`, `idempotency_keys`.

---

## §7. State machines (SPEC §6.1) — implement as explicit enums + transition tables

Each machine has: `states`, `allowed_transitions[(from, to, required_permission, guard_fn, side_effects)]`, and a **generated exhaustive test** that attempts every (from,to) pair and asserts only allow-listed pairs succeed.

1. **Instrument** `DRAFT → SUBMITTED → INTAKE_REVIEW → SCRUTINY → ACTIVE_TRACKING → {SUPERSEDED | CANCELLED | ARCHIVED}`; plus `INTAKE_REVIEW → RETURNED_FOR_CORRECTION → SUBMITTED`. `ACTIVE_TRACKING` requires the evidence checks the *policy version* demands for that instrument type (guard).
2. **Evidence item** `DECLARED → EXTRACTED(optional) → REVIEWED → BANK_CONFIRMED | LEDGER_RECONCILED`; any → `INCONCLUSIVE | REJECTED` (reason + reviewer mandatory). Evidence dimensions are not ranked.
3. **Observation** `OPEN → AWAITING_INSTITUTION → RESPONSE_RECEIVED → UNDER_REVIEW → RESOLVED → CLOSED`; `RESOLVED/CLOSED → OPEN` re-open only with reason + audit. Never deleted.
4. **Renewal link** immutable relation old→new with type (`RENEWAL | REPLACEMENT | CONVERSION`), gap/overlap days, review result, approver. Cycle and orphan constraints.
5. **Release request** `DRAFT → SUBMITTED → COMPLETENESS_REVIEW → REQUIRED_CLEARANCES → SCRUTINY_RECOMMENDATION → COMPETENT_AUTHORITY_DECISION → EXECUTION_PENDING → RELEASED_DISCHARGED`; side exits `RETURNED | DEFERRED | REJECTED | CANCELLED`. `RELEASED_DISCHARGED` only via trusted execution evidence (§F-12).
6. **Verification request** `CREATED → SENT → AWAITING_RESPONSE → RESPONSE_RECEIVED → ACCEPTED | REJECTED | INCONCLUSIVE`; timeout → `OVERDUE` (escalation only).
7. **Document** `UPLOAD_INTENT → QUARANTINED → SCANNING → ACCEPTED | REJECTED`.
8. **Reconciliation exception** `OPEN → UNDER_REVIEW → RESOLVED(match|no-match|adjustment) `, dual review when policy says.
9. **Notification** per SPEC §11.3.

Invariants (SPEC §6.2): every transition row stores from/to/actor/timestamp/reason-code/free-text/policy-version/evidence/request-id; allow-listed only; atomic with audit+outbox; submitted versions immutable; renewal links preserve history; `ACTIVE` needs approved checks; `RELEASED` needs approved decision + execution evidence; inconclusive ≠ fraud; policy version pinned to decisions.

---

## §8. Identity, roles, authorisation

### §8.1 Authentication
- OIDC authorization-code + PKCE for web (BFF-style secure HttpOnly SameSite=Strict cookie session issued by the API, CSRF double-submit/Origin check) and native OIDC code + PKCE for mobile (system browser via `expo-auth-session`/AppAuth; never embedded webview). Tokens in OS secure storage only.
- MFA mandatory for every AICTE-side role and for institution administrators; TOTP and WebAuthn passkeys supported. Step-up (`max_age`/`acr`) required immediately before: approve/reject/defer release, record execution, forfeit, change policy, grant/revoke roles, change connector state, un-mask identifiers in bulk, break-glass.
- Account lifecycle: single-use short-lived invitations bound to one institution; institution representative onboarding is a **workflow** (§F-02): the applicant submits an authorisation letter + official ID reference; an AICTE Intake/Registry Officer verifies the authority through the AICTE-approved process (D-04) before the account is activated. E-mail verification alone never confers authority.
- Session/device list, remote revoke, refresh-token rotation with reuse detection, lockout + rate limits, suspicious-login notification, immediate revoke on assignment end, privileged recovery with dual control. Biometric unlock on mobile is a *local* convenience only after a server-authenticated session; never proof of role.

### §8.2 Roles → permissions (verbs, SPEC §4.1)
Verbs: `view`, `create_draft`, `edit_draft`, `submit`, `upload_evidence`, `download_evidence`, `raise_observation`, `respond_observation`, `assign_case`, `recommend`, `verify_bank_evidence`, `reconcile_statement`, `resolve_exception`, `request_release`, `approve_release`, `execute_release_record`, `export_report`, `manage_institution_users`, `manage_roles`, `manage_policy`, `configure_integrations`, `view_audit`, `administer_platform` (+ `view_unmasked_identifiers`, `manage_templates`, `break_glass`).
Implement the SPEC §5 matrix as data (`role_permissions` + scope rules), not `if role ==` code, and generate the **role × action × scope negative test matrix** from it.

### §8.3 Separation of duties (SPEC §4.3)
Database constraint + service guard: for any (case, action-class) the maker cannot be the checker: the submitter ≠ intake ≠ recommender ≠ verifier-reviewer ≠ approver on the same release; same user cannot recommend and approve; same user cannot approve own exception; delegations carry limits (amount, region, programme) enforced server-side. Break-glass: separate workflow, time-boxed, reason, enhanced logging, mandatory retrospective review task.

### §8.4 Authorisation algorithm (SPEC §4.2) — implement as one function used by every route
`authorise(principal, action, resource, context)`: (1) identity active/session valid; (2) required assurance (MFA/step-up); (3) action granted by approved role assignment; (4) scope attributes (institution/region/assignment/programme); (5) resource state permits action; (6) delegation limits + SoD + policy version; (7) deny on missing/ambiguous attributes or engine failure; (8) consequential writes record actor/reason/correlation ID/audit; (9) response serialiser returns only fields the role may see (allow-list serialisers, no `**model.dict()`).

### §8.5 Row-level security
Per request: open a transaction, `SET LOCAL app.user_id`, `app.role_scope` (JSON of institution_ids / region_ids / assignment ids), `app.assurance` via parameter-safe `set_config(..., true)`. Policies reference these. Provide a **pool-isolation test** that runs interleaved requests of two tenants on a size-1 pool and proves no leakage, plus a test that a missing context yields zero rows. Workers use a distinct DB role with narrowly scoped policies.

---

## §9. Functional modules — complete specification with acceptance criteria

Legend: **WEB** and **MOB** both implement every module unless marked. "AC" = acceptance criteria (each becomes at least one automated test, referenced in `docs/TRACEABILITY.md`).

### F-01 Identity, sessions, access governance
Behaviour: login (OIDC), MFA enrolment (TOTP, passkey), step-up prompts, device/session list with remote revoke, suspicious-login alerts, lockout, invitation acceptance, privileged recovery workflow, access recertification campaign (quarterly or policy-defined), role assignment requests (maker-checker), break-glass.
AC:
- Role change or revocation takes effect on the **next** authorisation check; an open session cannot keep stale access (test with a live session).
- Refresh-token reuse revokes the family. Invitation single-use + expiry enforced.
- Client-sent `institution_id`, `role`, `region`, `approval_limit` are ignored/rejected and the attempt is audit-logged.
- Step-up is demanded server-side for the listed actions even if the client skips the prompt.
- Mobile: logout/revocation clears tokens, cache, scheduled local notifications, and de-registers the push token server-side.

### F-02 Institution registry and onboarding
Behaviour: authoritative institution/legal-entity records with AICTE identifier, programmes/levels, region, status, effective-dated attributes; imported by **authorised CSV/XLSX batch with provenance** (file hash, importer, source owner, mapping version) — never fuzzy auto-merge; institution-representative onboarding workflow (apply → document upload → Intake review → approve/reject with reason → account activation); Organisation Admin manages own users (invite, deactivate, role among institution roles only); regulator-owned attributes are read-only for institution users.
AC: duplicate official IDs rejected; fuzzy-name candidates go to a merge-review queue (human decides); onboarding cannot self-approve; deactivated user loses access at once; every attribute change versioned with source.

### F-03 Instrument register
Behaviour: instruments per institution and programme; types `ONLINE_DEPOSIT`, `LEGACY_FDR` (+ others only if D-07 enabled via registry). Draft → submit; every submit freezes an immutable `instrument_version` (normalised snapshot + content hash + submitter + reason); amendments create a new version and show a field-level diff; fields: reference/FDR number (encrypted + blind index), issuing bank + branch + IFSC (validated against the offline IFSC dataset, flagged not blocked if unknown), amount, currency, issue date, maturity/validity date, lien/pledge declaration, holder name, programme(s) covered, linked policy version, owner, related documents. Each field has provenance (declared/extracted/confirmed/reconciled) and a "why this value" panel.
AC: float amounts impossible (schema + DB); maturity ≤ issue date rejected with explanation; submitting twice with the same idempotency key yields one version; concurrent edit returns `409 STALE_VERSION` with latest state; deletion impossible, only `CANCELLED/ARCHIVED` through allowed transitions; receipt (F-20) issued at submit.

### F-04 Document vault and upload pipeline (SPEC §8.1 exactly)
Pipeline: authorised upload intent → short-lived presigned PUT to `quarantine` for **one object key with size cap** → finalise → magic-byte/MIME/extension/page-count/archive-bomb checks → reject encrypted/unsupported → ClamAV scan → PDF sanitise (strip JS/launch/embedded files; rasterise-and-rebuild if policy says) → SHA-256 (+ optional perceptual hash for duplicate flags) → move to `vault` only on pass → record `documents` row with every step status → OCR on rasterised copy (F-05) → authorised download only via API-minted short-lived signed URL; every download is logged in `document_access_events`; watermark/redact per policy.
Categories (configurable): FDR copy, deposit payment proof/UTR, Affidavit 6, request letter, latest LoA/EoA, clearance letters, NOC/sanction order, bank confirmation, authorisation letter, other.
AC: EICAR test file quarantined; wrong-magic file rejected; zip-bomb rejected; a client cannot choose a trusted destination; no vault object is reachable without a signed URL; hash recorded and re-verified on download; version history for corrected re-uploads (old versions retained).

### F-05 OCR/extraction assist and review (bounded AI — §14)
Behaviour: extraction proposes candidate fields (bank, FDR number, amount, dates, holder) with page/region/confidence/engine+version; side-by-side review UI (image with highlighted region ↔ editable field); reviewer confirms/corrects with reason; original extraction kept; **no evidence level changes**. Deterministic post-checks (tenor/date consistency, amount vs policy expectation, duplicate number/hash) create *flags*, not verdicts.
AC: scenario SPEC §18.1-3 passes; with OCR disabled, everything still works manually and UI says "Extraction unavailable" (not "failed verification"); prompt-injection text in a document never alters tool behaviour (OCR/LLM has no tools or write access).

### F-06 Verification of legacy FDR and online deposits (SPEC §2.4, §12)
Behaviour:
- **Bank confirmation requests**: Finance/Verification Officer issues a request (approved template/version, fields to confirm, destination bank/branch/channel, tracking number) → status machine (§7, item 6). Response paths: (a) **Bank-verifier portal** (role 13, scoped to its bank and assigned requests only; responds with confirmed fields + signed PDF/attachment; MFA mandatory); (b) officer records a bank-issued letter/e-mail response as an attachment with received-time and channel; (c) none yet → stays `AWAITING_RESPONSE` and escalates on due date.
- **Evidence decision**: independent reviewer (≠ requester) accepts / rejects / marks inconclusive with reason → sets `BANK_CONFIRMED` on the specific fields confirmed. Inconclusive opens a reconciliation/verification exception, not a fraud label.
- Verification summary on instrument: per-field attribute chips (Declared · Extracted · Bank-confirmed · Ledger-reconciled · Rejected/Inconclusive) with source and date. Hover/tap → provenance drawer.
AC: scenario §18.1-4; response without a verifiable sender identity is rejected; bank verifier cannot see other banks' or AICTE-wide data (negative tests); request overdue → escalation notification only (no status change to rejected).

### F-07 Statement import and reconciliation (SPEC §8.3, §12.2)
Behaviour: Finance officer uploads authorised bank-origin statements (MT940 via `mt-940`, CAMT.053 via `pycamt`, CSV/XLSX with an admin-defined column mapping version). Validate schema, account/source identity (masked account), period, opening/closing balances/totals, duplicate batch (checksum + source ID), row sequence gaps, currency. Immutable `statement_lines`. Import report: received / parsed / rejected (quarantined with reason) / duplicate / matched / unmatched / ambiguous. Deterministic matching on exact UTR/reference, amount, currency, date window (policy-controlled), remitter, destination account; every candidate stores matched attributes and ruleset version; fuzzy narrative matches go to the exceptions queue. Reversals/returns/amended statements/late lines are handled by compensating events; raw rows never rewritten. Result: `LEDGER_RECONCILED` evidence on the **online deposit** only.
AC: scenario §18.1-5; re-import of same file is a no-op with report; out-of-order import converges to the same matches; ambiguous match never auto-confirms; reconciliation of an FDR scan can never produce `LEDGER_RECONCILED`.

### F-08 Discrepancy and completeness engine (deterministic)
Rules (versioned, in the policy registry, each with id, severity, explanation template): missing mandatory field/document per policy; date inconsistencies; amount ≠ policy expected amount (only when the policy rule for that programme/level is `approved`; otherwise "policy rule not approved — cannot assess"); duplicate FDR number/hash across institutions or instruments; declared vs extracted vs confirmed mismatch; bank/IFSC mismatch; maturity before required validity; missing renewal before maturity; unresolved observations past due; statement credit without matching declaration; declared deposit without matching credit after the policy window.
Output: an `observation` draft (needs officer confirmation to issue) or an automatic **flag** visible only to staff until an officer issues an observation. Never auto-reject.
AC: each rule has fixture-based positive/negative tests; disputed policy → rule status `BLOCKED` and surfaced as "cannot assess".

### F-09 Observations / casework (SPEC §6.3)
Behaviour: first-class records with type, severity, affected fields, compared source IDs, explanation, owner, due date, status machine, institution response (text + documents), resolution code, reviewer, policy ref; threads of comments (internal vs institution-visible, with clear visual distinction); reassignment; reopen with reason; SLA ageing; bulk assignment for supervisors.
AC: scenario §18.1-6; deletion impossible; institution cannot see internal notes (negative test); every status change notifies the right parties (F-14).

### F-10 Lifecycle, deadline and escalation engine (SPEC §9)
Behaviour: server-authoritative scheduler (DB-leased singleton, `scheduler_runs` heartbeat) scans due obligations: validity/maturity, renewal due, verification overdue, observation overdue, release pending, unacknowledged critical notices. **Reminder windows, grace, holidays, weekend rules and escalation periods are policy config** (admin UI with maker-checker + effective dates). Each reminder has idempotency key `instrument+event+target_date+schedule_version+recipient`. Overdue escalation reassigns/exposes to supervisors only; it never rejects, forfeits or releases.
**No approved schedule ⇒ no invented one.** In production, if no approved reminder schedule exists, the dashboard shows an admin alert "Reminder schedule not approved" and the scanner records `skipped: no approved schedule`. In staging the *example* schedule (T-90/60/30/7/0) from `config/policy-drafts/reminders.example.json` can be activated and is labelled `UNAPPROVED EXAMPLE`.
AC: scenarios §18.1-7; scanner twice → one reminder per key; scheduler outage detected by heartbeat alert and recovered by catch-up on restart; date-boundary and Asia/Kolkata tests (DST-free but test month ends, leap day, holiday shift); client clocks irrelevant.

### F-11 Renewal and replacement
Behaviour: institution (or officer) creates a renewal/replacement instrument linked to the old one; system computes gap/overlap days; policy handles gap/overlap (observation if gap > allowed); both records remain queryable; lineage graph visual on web and mobile; old instrument transitions `SUPERSEDED` only when the new one reaches `ACTIVE_TRACKING` under the approved checks.
AC: scenario §18.1-8; cycles and orphans rejected at DB level; history never lost.

### F-12 Release / refund workflow (SPEC §2.3, §6.1)
Behaviour:
1. Institution creates request (may begin before maturity if policy permits): reason, instrument(s), upload request letter, Affidavit 6, FDR/payment proof, latest LoA/EoA.
2. System builds the **checklist from the approved policy version** (APH 6.46 elements as rule drafts): each row is `SATISFIED | NOT SATISFIED | PENDING SOURCE | NOT APPLICABLE` with deciding user, evidence link, rule version, reason. Rows: request letter; Affidavit 6; FDR/payment copy; latest LoA/EoA; clearances from PGRC, Vigilance Cell and other Cells/Bureaus (each a separate `clearances` record with source, cell, received date, outcome — an empty queue or integration outage is never "clear"); FDR/RPGF NOC from Approval Bureau **or** RTGS sanction order (distinct paths per instrument type); embezzlement-hold NOC when the case owner records such a hold.
3. Completeness review → required clearances → scrutiny recommendation (≠ requester) → competent-authority decision (approve/reject/return/defer; delegation limit + step-up MFA + reason) → `EXECUTION_PENDING` → `RELEASED_DISCHARGED` only after an authorised finance user records trusted execution evidence (transaction reference + attachment, second-person review) — or a connector confirms it once that connector is `production-enabled`.
4. Portal never generates a substitute NOC/sanction order and never calculates or imposes penalties unless the exact rule is `approved` in the policy registry.
AC: scenario §18.1-9; same-person maker/checker denied (API + DB); out-of-delegation denied; approval without step-up denied; maturity alone cannot create approval; checklist rows cannot be bulk-ticked; closing requires execution evidence.

### F-13 Policy and rules registry (SPEC §2.1–2.3, §21)
Behaviour: `policy_versions` with source URL/ID, document hash, clause, scope, effective_start/end, config payload, status `draft → review → approved → retired`, approver ≠ author, changelog; admin UI for diff and effective-date scheduling; decisions pin the version; supersession never rewrites history.
Ship **drafts only** (never `approved`) in `config/policy-drafts/`: APH 2024-27 Table 1.4 amounts (₹ lakh) incl. the "double for private leased building/land" note; Clause 6.46 release checklist; example reminder schedule. Penalty rules: not shipped — registry entries exist with status `BLOCKED: awaiting AICTE written confirmation (D-01)`.
Table 1.4 (draft source data; Engineering & Technology: Diploma ₹15 L / UG ₹35 L / PG ₹15 L; Planning, Applied Arts & Crafts, Design, Hotel Mgmt & Catering: ₹15 L in each column; Computer Applications and Management: Diploma —, UG ₹5 L, PG ₹15 L) — encoded only as a draft, with the accuracy guardrail from SPEC §2.1.
AC: unapproved rules can't drive a "compliant/non-compliant" result; approving requires a different user plus step-up; rollback of a published version is a runbook-tested operation.

### F-14 Notifications (full spec in §10)
### F-15 Realtime (SSE) (full spec in §10.8)

### F-16 Dashboard, reports, exports
Dashboard cards (scope-filtered): **active, expiring (configurable horizons), matured, renewed, released, pending verification, open observations, awaiting institution, reconciliation exceptions, release requests by stage, overdue**, plus ageing buckets and evidence-attribute distribution (never one score). Drill-down from every number to the filtered list; counts always equal list totals (tested).
Reports (each also scheduled, exportable): pending verifications; upcoming maturities by horizon/region; missing documents; cases requiring intervention; observation ageing; reconciliation exceptions; release pipeline; reminder coverage; notification delivery funnel (created→accepted→received→opened→acknowledged); officer workload; institution compliance summary; audit/access report (auditor only).
Exports: async `export_jobs` (scope, reason, row count, format CSV/XLSX/PDF, file hash, expiry); permission **revalidated at download**; size/row caps; neutralise CSV injection (`=`,`+`,`-`,`@` prefix); audit every export.
Product/ops metrics per SPEC §20 exposed on an Ops dashboard (Platform role only for system metrics).
AC: dashboard numbers reconcile to DB queries in tests; export respects RLS and masked identifiers; institution cannot export other institutions.

### F-17 Search, filters, saved views
Postgres FTS + `pg_trgm` over scoped fields only (never across tenants); filters (institution, region, programme, instrument type, state, evidence attributes, dates, bank, owner, aging); saved views per user; bounded pagination (cursor), server-side sort; query timeout. Identifier search uses the blind index (exact) — no wildcard search over identifiers.
AC: search results never include out-of-scope rows (property test); p95 target recorded after load test (no invented SLA — D-13).

### F-18 Audit and access logging (SPEC §14.7)
Behaviour: every consequential action and every sensitive read (document download, un-masking, export, audit view) → `audit_events` (actor, action, resource, safe diff, reason, correlation ID, source IP/device summary per privacy policy, prev/current hash); hash chain + periodic **signed checkpoint** (Ed25519 key outside the DB) forwarded to a restricted log store; verification job + UI for the Auditor ("chain verified through checkpoint N; gap/mismatch alert"); app roles have INSERT-only; state-transition and audit tables protected by triggers.
Auditor workspace: read-only timeline per case/user/document, policy-version viewer, decision trace, access-audit reports, control-evidence export.
AC: scenario §18.1-12; tamper attempt denied; modified/deleted row detected by verification; logs scrubbed of tokens/identifiers (tested with canary values).
State the assurance accurately in UI/docs: "tamper-evident", not "immutable".

### F-19 Administration and operations
Users & roles (assignment workflow with approver, scope, validity, ticket reference); access recertification; policy admin (F-13); connector/feature registry with health checks, credential-expiry warnings and acceptance-evidence attachments; notification template versioning (key, version, locale, review status); retention classes; system health; scheduler/worker status; dead-letter queue viewer with safe replay; maintenance banner; platform operator cannot read case documents by default (break-glass only).
AC: no user can grant themselves a role; platform role cannot approve business actions; connector cannot be set `production-enabled` without evidence + second approver.

### F-20 Receipts and verifiable QR
Behaviour: at submission/decision milestones issue a **receipt PDF** (institution, instrument ref masked, version hash, timestamps, policy version) signed with pyHanko using an AICTE-controlled key; QR encodes a short verification URL + Ed25519-signed payload; public verification page shows only minimal non-sensitive confirmation (receipt exists, issued-at, version-hash prefix). Never labelled eSign/DSC/official certificate; footer states what it is.
AC: tampered PDF fails verification; verification page leaks nothing beyond the minimum; rate-limited.

### F-21 Help, support and grievance
In-app help centre (searchable, versioned content in en + localised), support request form with correlation ID auto-attached, status tracking, FAQ per role. Rights/grievance requests (DPDP) workflow (F-22). Contact details and support hours come from admin config, never hard-coded.
AC: support request cannot attach out-of-scope records; PII scrubbed from diagnostics.

### F-22 Retention, legal hold, deletion, rights requests
Retention classes per record type (D-11 config; none invented): schedule disposal jobs, legal hold overrides, deletion proof, exceptions; rights/correction/grievance request workflow with due dates and authority approval; unconditional deletion is never promised for financial records.
AC: held records are never disposed; disposal logged with proof; correction creates a new version, not an overwrite.

### F-23 Migration and bulk import (SPEC §13.3–13.4)
Tools: legacy-batch importer (immutable batch, source file hash, mapping version, importer), dry-run report (counts by source/type/status, amount totals, duplicates, missing critical fields), staging-first migration, signed reconciliation report, two-person cutover sign-off, post-cutover marking "migrated—unverified" until evidence attached. Never corrects amounts/dates/IDs without an approved correction record.
AC: dry-run and real run totals match; re-run idempotent; imported legacy rows never show `Bank-confirmed`.

### F-24 Assignment, queues and workload
Queues per role/region; auto-assignment rules (round-robin / by programme / by region) as policy config; manual assign/reassign with reason; supervisor workload board; SLA timers per stage (targets from D-13 once approved; ageing shown without invented targets before that); escalation views.

### F-25 Comments, mentions, attachments
Case comments with `internal` / `institution_visible` flag, @mentions limited to in-scope users, attachments through F-04 pipeline, edit history preserved.

### F-26 Policy Q&A and case summary (bounded AI — §14.4)
RAG over **approved** policy documents/clauses only, answers must cite document version + clause + quote; no citation ⇒ "I couldn't find this in the approved policy documents." Case summary generated only from authorised fields of that case, labelled "AI-generated assistance — verify against the record", off by default for Tier-S (real case data) until D-12 approves a provider or a local model is accepted.
AC: hallucinated clause numbers impossible (post-check: every citation must resolve to a stored clause); injection tests pass.

### F-27 Internationalisation
Languages: English (authoritative) plus Hindi and Tamil at launch, plus pluggable additional Indian languages. ICU message format, plural/number/date formatting by locale (`Intl`), Indian digit grouping (₹ 1,00,000), `lang` attributes, font fallbacks for Devanagari/Tamil scripts, and layout tested with 30–40% text expansion. A `translation_catalog_status` table marks each key `machine-draft | reviewed`; **production shows only `reviewed` strings in that locale and falls back to English otherwise**; notification templates are versioned per locale with the same rule. Legal/clause text is displayed in English as authoritative with a clearly labelled convenience translation only if reviewed.

### F-28 Accessibility
WCAG 2.1 AA minimum (2.2 AA target) on web and mobile: keyboard-only operation, visible focus, semantic landmarks, screen-reader names for all controls and chips (attribute chips announce full meaning, not colour), 4.5:1 text and 3:1 non-text contrast, touch targets ≥44pt iOS / ≥48dp Android, dynamic type/font scaling to 200%, Reduce Motion / Reduce Transparency / Increased Contrast, captions-free (no audio/video), error summaries, no time limits without extension (idle-timeout warning with extend). axe-core in CI plus manual TalkBack/VoiceOver scripts (`docs/a11y-test-script.md`).

---

## §9A. Mobile-only and mobile-enhanced features (the app must be *more portable*, never a different rulebook)

All business actions go through the same API; the server may deny a mobile action by policy (e.g. a decision class that must be done on desktop) with a clear explanation. Mobile differs in the following ways only:

| ID | Feature | Detail and constraints |
|---|---|---|
| M-01 | **Instant push for every event class in §10.3** | FCM (Android) / APNs (iOS); channels per category on Android; interruption levels on iOS; badge = unread inbox count from server; tapping opens the authorised record after normal auth. |
| M-02 | Notification centre sync | Inbox is server-backed; pull-to-refresh; background refresh best-effort; missed pushes recovered when app opens (SSE catch-up with `Last-Event-ID`, then `/inbox?since=`). |
| M-03 | Biometric app lock | Local unlock (Face ID/Touch ID/Android Biometric Prompt) after server auth; configurable auto-lock timeout; hides content in app switcher; never replaces step-up MFA for decisions. |
| M-04 | Secure screens | `FLAG_SECURE`/`expo-screen-capture` prevention on documents, identifiers and decision screens (policy configurable); lock-screen notifications minimal. |
| M-05 | **Document capture** | Camera scan with edge detection/perspective crop/multi-page → PDF; document picker; share-sheet "Send to AICTE FDR" import; resumable chunked upload with progress, retry and background continuation; local pre-checks (size, type, blur warning) that never replace server checks. |
| M-06 | Quick actions | App icon long-press shortcuts (Android shortcuts / iOS quick actions): Inbox, Due soon, Upload document, Scan QR. |
| M-07 | Home-screen widgets | "Due soon" and "Open tasks" counts (iOS WidgetKit via `expo-widgets` if verified; Android Glance/AppWidget via config plugin if verified). Data limited to non-sensitive counts; empty when locked. |
| M-08 | Deep links / universal links / App Links | `aicte-fdr://` plus verified HTTPS links; link IDs untrusted; auth + authorisation always re-checked. |
| M-09 | QR scanner | Verify receipt QR (F-20) inside the app; offline signature check of payload plus online confirmation. |
| M-10 | Add to device calendar | User-initiated: add maturity/renewal/response-due to the device calendar (title without sensitive values; deep link in notes). Server reminders remain authoritative. |
| M-11 | Reminder "remind me again" | A **local** re-surface of a notification after 1h/4h/tomorrow. It never cancels the server-side obligation, escalation or acknowledgement requirement. |
| M-12 | Offline read cache | Optional, encrypted (SQLCipher/OS keystore key), expiring, scoped to the user's last-viewed lists and open items; **no offline writes of approvals, reconciliations, financial transitions**; allowed offline draft of an observation *response text* is queued only as an unsent draft, submitted when online and re-validated. Cache purged on logout/revocation/role downgrade. |
| M-13 | Network resilience | Request queue with idempotency keys for safe writes (uploads, acknowledgements), exponential backoff, visible sync state; conflict UI for `409`. |
| M-14 | Adaptive layouts | Phone, large phone, foldable, tablet: Android window-size classes with list-detail panes; iPad split-view/sidebar adaptable tabs; landscape support; keyboard & pointer support on tablets. |
| M-15 | Share (outbound) | Share a deep link or an exported report file through the OS share sheet only if the user has `export_report`; no raw sensitive documents shared by default. |
| M-16 | Device management | Profile → Notification & device status (permission state, token registered time, last push received, channel states), "Send test notification to this device" (real send through the real pipeline, labelled TEST), re-register, sign out everywhere. |
| M-17 | Haptics & motion | Subtle confirmations; honour Reduce Motion. |
| M-18 | App update gating | `min_supported_version` from server; soft/hard update prompts; store links. |
| M-19 | Privacy controls | Hide amounts in notifications/widgets toggle (default hidden); clipboard never auto-filled with identifiers; copy actions show brief masked confirmation. |
| M-20 | Diagnostics | "Report a problem" attaches app version, OS, correlation IDs; no tokens/PII. |
| M-21 | Dictation | Use the OS keyboard's own dictation only; the app contains **no** speech/voice feature. |

Parity rule: for every screen in §11 there is a mobile equivalent with the same data and permissions (denser tables become card lists with the same columns reachable via "details"). A parity checklist (`docs/PARITY_MATRIX.md`) is generated in CI from route/screen manifests and fails if a web capability lacks a mobile counterpart or a documented, policy-based exception.

---

## §10. Notifications and real-time (F-14, F-15) — the one place mobile is *better*

### §10.1 Contract
"Instant" is an engineering target: the notification event is committed with the business transaction and dispatch is enqueued without a human; the OS may still delay or suppress display. Never promise or display "delivered" beyond what the platform reports. Metrics measure each stage separately (SPEC §11.1, §20).

### §10.1a Notification state model (SPEC §11.3) — stages are never merged
`CREATED` (event committed + inbox item persisted) → `QUEUED` (dispatch ready) → `PROVIDER_ACCEPTED` | `PROVIDER_FAILED` (accepted/rejected by FCM/APNs/Web Push/e-mail — **not** proof of display) → `DEVICE_RECEIVED` (only where the platform exposes a signal; otherwise "not observable") → `OPENED` (deep link/inbox opened) → `ACKNOWLEDGED` (explicit user acknowledgement recorded server-side) → `ACTIONED` (an authorised state-changing API call succeeded) ; terminal `EXPIRED` / `DEAD-LETTER`. `status` holds the furthest stage reached; each stage also keeps its own timestamp/attempt record (`provider_accepted_at`, `device_received_at`, `read/opened_at`, `acknowledged_at`, `actioned_at`) so measurements stay separate. The UI may claim only what the evidence proves (SPEC §11.3 "What can safely be claimed").

### §10.2 Pipeline (SPEC §11.2) — implement exactly
1. Business transaction commits domain change **and** an `outbox` row (same transaction).
2. Worker claims outbox rows (`FOR UPDATE SKIP LOCKED`), dedupes by `dedupe_key`, resolves recipients from *current* role/scope/assignment (never from a cached list).
3. For each recipient persist `user_notifications` (inbox item) first, status `CREATED`; apply preferences and policy (§10.4).
4. Render localised, versioned template with a **minimal** payload; server-owned amounts/dates substituted from authorised data (no model text).
5. Channel adapters send via real providers; persist provider message id, attempt number, result, error category.
6. Transient errors: exponential backoff + jitter, bounded attempts; permanent errors retire the device/subscription or raise an ops alert; exhaustion → dead-letter queue (visible in admin, safe replay).
7. Opening a notification → deep link → normal auth + authorisation → server records `OPENED`; explicit user action records `ACKNOWLEDGED`; a successful state-changing API call records `ACTIONED`.
8. Metrics: enqueue latency, dispatch latency, accepted/failed, invalid tokens, backlog age, dead letters, received/opened/acknowledged — all separate series.

### §10.3 Event catalogue (SPEC §9.2 + more) — each has category, recipients rule, template key, deep link, urgency
Categories: `critical_workflow`, `deadline`, `security_account`, `operations`, `digest`.
- Submission received (submitter + intake queue) · Returned for correction · Observation raised / response submitted / resolved / reopened / overdue · Document accepted / rejected (scan fail) · OCR ready for review · Verification request sent / response received / accepted / rejected / inconclusive / overdue · Statement imported / reconciliation exception created / resolved · Maturity horizon reached (per approved schedule) / renewal due / renewal received / replacement accepted · Release request submitted / clearance requested / clearance received / recommendation made / decision (approved, rejected, returned, deferred) / execution recorded / closed · Case assigned / reassigned / escalated · Unacknowledged critical notice escalated to supervisor · Role/device/session change, new-device login, MFA change, access recertification due · Policy approved/superseded · Connector failure / credential expiring / scheduler missed run / dead-letter spike (ops only) · Export ready · Support request update · Rights request due.
Each event has a unit test proving recipients, template, deep link, and that no sensitive value appears in the lock-screen payload.

### §10.4 Channels, preferences, escalation
- Channel mapping per category is **configuration signed off by the process owner (D-10)**; the build ships a conservative default: inbox (always) + push (if device registered) for all; e-mail only if configured; SMS/WhatsApp hidden.
- Preferences: language, optional categories (digest, operations), quiet hours — **quiet hours and opt-outs never suppress** `critical_workflow`, `deadline` or `security_account` items; user preference cannot silently cancel an obligation.
- Critical items unacknowledged beyond a configured window escalate to the supervisor queue (the case status is independent of delivery). Window values come from config; none are invented in code.
- Provide Profile → "Notification status": per channel configured/not, device registered, permission state (as reported by the app), last registration, last push accepted/received, last test result.
- Lock-screen content default: generic title + short phrase ("FDR Portal — Action needed"); no FDR number, amount, bank, institution legal detail. A per-user *opt-in* may show richer text if policy allows (default off, admin can force off).

### §10.5 Android push (FCM HTTP v1)
- Server uses a Google service-account credential (short-lived OAuth2 access token); message type: notification + data with `inbox_id`, `type`, `deep_link` (no sensitive values), `android.notification.channel_id` ∈ {`critical_workflow`,`deadline`,`security_account`,`operations`,`digest`} with importance set at channel creation (HIGH, HIGH, HIGH, DEFAULT, LOW), `android.priority` high for time-sensitive categories (must be user-visible notifications — high-priority data-only messages can be deprioritised), `ttl`, `collapse_key = type:entity` for reminders (≤100 pending per device), `priorityLowered` outcomes recorded.
- App: request `POST_NOTIFICATIONS` on Android 13+ **only after** channels exist and at a meaningful moment (explain value first); if denied, inbox stays fully usable and Profile explains how to enable; token refresh handler re-registers; token registered on login, refreshed periodically (stale if untouched ~1 month), revoked on logout.
- Error handling: `UNREGISTERED` → revoke installation; `INVALID_ARGUMENT` → inspect payload vs token (never loop); `QUOTA_EXCEEDED`/`UNAVAILABLE` → backoff honouring retry-after; `SENDER_ID_MISMATCH`/`THIRD_PARTY_AUTH_ERROR` → ops alert.
### §10.6 iOS push (APNs, token-based auth)
- Backend sends HTTP/2 to APNs with a `.p8` key (`aioapns` or equivalent; verify): `apns-push-type: alert`, `apns-priority` 10 for critical/deadline, 5 for others, `apns-topic` = bundle id, `apns-collapse-id`, `thread-id` per case, `interruption-level` `time-sensitive` for deadline/critical **only if the entitlement is approved** (verify), `category` for notification actions; token from `expo-notifications` `getDevicePushTokenAsync` (APNs device token); production vs sandbox endpoints by build profile; handle `BadDeviceToken`, `Unregistered`, `TooManyRequests`, `ExpiredProviderToken` (refresh the JWT before 60 minutes).
- Requires paid Apple Developer account, real device; mark blocked in PREFLIGHT if absent. Use FCM-to-APNs routing only as a documented alternative if the team prefers a Firebase iOS SDK — not both.
- Notification action buttons only open the app (foreground, authenticated); no background API calls from notification actions.
### §10.7 Web push and e-mail
- Web push: VAPID keys, `pywebpush`, service worker (`push`, `notificationclick`), subscription stored encrypted, expired subscription (410/404) retired; iOS web push needs the installed PWA + user gesture; UI explains this.
- E-mail: provider adapter (SMTP/API), verified domain (SPF/DKIM/DMARC), bounce/complaint webhooks → suppression list, template with no sensitive details; disabled until configured.
### §10.8 Real-time stream (SSE)
- `GET /v1/stream` (auth required; cookie on web, bearer on mobile) emits `id`, `event`, `data` (IDs + minimal change info; clients refetch through normal authorised APIs). Events: `inbox.created`, `inbox.count`, `case.changed`, `queue.changed`, `dashboard.counters`, `session.revoked` (client logs out immediately), `config.changed`, `maintenance`.
- Fan-out between API workers via Postgres `LISTEN/NOTIFY` (payload = event id only) + `sse_events` replay buffer (retention minutes–hours, configurable) for `Last-Event-ID` resume. Heartbeat comment every ~15 s. **Re-authorise before emitting each event** (scope may have changed). Bounded connections per user, backpressure, graceful shutdown, automatic reconnect with jitter on clients, fallback to 30-s polling if streaming is blocked.
- Mobile: foreground SSE; background relies on push; on resume run catch-up.
AC: scenario §18.1-10 and -14; killing FCM credentials yields `PROVIDER_FAILED` + visible "push not configured/unavailable", inbox item still present and SSE updates still arrive; after logout the previous user's device token receives nothing (test); forged deep link to another tenant's case returns the safe 404 screen.

---

## §11. Web application — screens and behaviour (React, PWA)

Layout: left glass sidebar (collapsible) + top toolbar (global search / command palette ⌘K, notifications bell with live count, language, theme, user menu). Content area on **solid** surfaces. Breakpoints: ≥1280 desktop (3-pane where useful), 768–1279 tablet, <768 phone layout (so the web is usable on a phone browser and as an installed PWA).
Screens (role-filtered; everything fetched through the generated client; every list virtualised; every empty/loading/error/forbidden/offline state designed):
1. Sign-in (OIDC), MFA, step-up modal, invitation acceptance, institution onboarding application.
2. **Home dashboard** (F-16 cards, due-soon timeline, my queue, activity feed live via SSE).
3. **Institutions** list/detail (programmes, users for org admins, instruments, open items).
4. **Instruments** list (filters, saved views, bulk assign) and **Instrument detail** with tabs: Overview (provenance chips) · Versions & diff · Documents · Evidence & verification · Reconciliation · Observations · Renewal lineage graph · Release · Timeline · Notifications.
5. **Submission wizard** (instrument type → details → documents → review → submit → receipt).
6. **Document review** (viewer with zoom/rotate/page nav ↔ extracted fields ↔ confirm/correct; hash, scan status, versions).
7. **Verification workbench** (requests, awaiting, responses, decisions) and **Bank-verifier portal** (isolated minimal UI for role 13).
8. **Reconciliation workspace** (statement batches, import report, candidate matches with matched-attribute explanation, exceptions, approve/resolve).
9. **Observations** inbox/detail with threaded responses; institution view shows only institution-visible content.
10. **Queues & workload** (intake, scrutiny, verification, supervisor board).
11. **Release request** detail: checklist table, clearances, recommendation, decision pane with step-up, execution evidence, closure.
12. **Renewals** pipeline; **Maturity calendar** (month/agenda); **Reminder schedule** viewer.
13. **Reports & exports** (catalogue, parameters, schedule, history, download with revalidation).
14. **Notifications** inbox (filters, mark read/ack) + **Preferences** (channels, languages, quiet hours for optional categories, device status).
15. **Profile & security** (sessions/devices, passkeys/TOTP, language, accessibility settings including "Reduce transparency", "Increase contrast", text size).
16. **Admin**: users & roles, access recertification, policy registry (diff, approve, effective dates), reminder schedules, connector registry & health, templates, retention classes, institution import, migration tools, dead-letter viewer, system health, feature registry.
17. **Audit workspace** (auditor): timeline, access logs, chain verification status, exports.
18. **Help & support**, **Rights/grievance requests**.
19. **Public receipt verification** page (no login; minimal output; rate-limited).
20. Error pages: 401/403/404/409/422/429/503/500 with correlation ID and safe guidance (SPEC §16.3).
Global: command palette, keyboard shortcuts (documented), unsaved-changes guard, optimistic UI only for reversible actions, toast + persistent banner for degraded integrations, session-timeout warning, print-friendly case summary (scoped).

---

## §12. Mobile application — navigation and screens

Same feature set as §11 (parity matrix, §9A). Platform-appropriate navigation:
- **iOS**: native tab bar (Expo Router native tabs; iOS 26 Liquid Glass tab bar with minimise-on-scroll, plus a Search tab role) — Home · Cases · Inbox · Tasks · More; large titles; swipe-back; sheets with detents; context menus; pull-to-refresh; swipe actions on list rows (acknowledge, assign) where permitted.
- **Android**: Material 3 navigation bar (compact), navigation rail (medium/expanded), top app bar (small/medium/large collapsing), FAB or extended FAB only for the primary create action, predictive back, bottom sheets, snackbars, search bar with suggestions, list-detail canonical layout on large screens.
- Both: identical routes (`/cases/:id/...`), same deep links, same permissions from `/v1/me/permissions`, same error model, same i18n catalogue, same formatting.
Mobile-specific screens: Biometric lock, Notification & device status, Document scanner, Share-import, QR scanner, Widgets config, Update-required, Offline/sync status.

---

## §13. Design system — "Apple-style on web + iOS, Material 3 on Android"

Full specification and token files live in `design/DESIGN_SPEC.md`, `design/tokens.css`, `design/tokens.ts`. Obey them; the points below are the part you must never lose.

### §13.1 Brand and colour
- Base `#050505` (true-dark canvas), violet `#3b0a6b` (container/tint), cyan `#00eeff` (accent). **Computed contrast on `#050505`: cyan 14.24:1 (text/icon OK); violet 1.40:1 (never text/icon; fills, tint, glow, selected-row wash only).** Text on cyan fills is `#00363b`. Text tiers on base: `#f0f0f0 / #b9b9b9 / #919191`; `#646464` is decoration/disabled only.
- Light theme exists (follows system, user-overridable): surface `#fef7fc`, primary `#006971`, onSurface `#1d1b1e` (contrast: text 16.2:1, primary 6.1:1). Dark is the hero theme.
- Status colours (never alone — always icon + text): ok `#3ddc97`, warn `#ffb020`, info `#7aa7ff`, error `#ff5c7a`, pending `#b69cff`, neutral `#9aa0ad` (all ≥4.8:1 on elevated dark surfaces). Light-theme counterparts in tokens.
- **Evidence attribute chips** (distinct shapes + icons + labels, not just colour): Declared (outlined), Extracted (dashed), Bank-confirmed (filled with check), Ledger-reconciled (filled with link), Inconclusive/Rejected (warning/stop). Tooltip/sheet gives source, date, reviewer.

### §13.2 Web + iOS (Apple HIG / Liquid Glass)
- Type: system stack `-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", Inter, "Noto Sans", "Noto Sans Devanagari", "Noto Sans Tamil", system-ui, sans-serif` (SF fonts are not self-hosted on the web; self-host Inter, OFL, as the non-Apple fallback). Tabular numerals for money/dates; monospace for identifiers. HIG-like scale (Large Title 34 / Title 28–22 / Headline 17 semibold / Body 17 / Subhead 15 / Footnote 13 / Caption 12) — web rem equivalents.
- Shape/spacing: 4-pt grid; continuous-corner radii 12 / 16 / 22 / 28; hairline separators; generous but information-dense in tables (44-px minimum row height on touch, 36 px on desktop pointer).
- **Liquid Glass usage rule (HIG):** glass is for the **navigation/control layer** only — sidebar, toolbar, tab bar, floating action cluster, popovers, sheets' grab area, segmented controls. **Never** apply glass to content (tables, cards, forms, documents), never stack glass on glass, keep it sparing. Content sits on solid dark surfaces (`#0f0d11…#2c292d` tonal steps); glass floats above with a subtle violet-tinted refraction of what's behind.
- Web recipe (progressive enhancement, tokens in `tokens.css`): `backdrop-filter: blur(24px) saturate(180%)` with the `-webkit-` prefix, translucent `color-mix` tint, 1-px inner highlight border + soft shadow; optional specular edge via gradient border; SVG `feDisplacementMap` refraction **only** as an optional enhancement in Chromium (feature-detect; never required); on iOS 26 Safari optionally use `-apple-visual-effect` behind `@supports` (verify); fallbacks: `@supports not (backdrop-filter…)` → solid elevated surface; `prefers-reduced-transparency` / in-app "Reduce transparency" / `prefers-contrast: more` → opaque surfaces with a clear border. Limit to ≤3 simultaneous glass surfaces per viewport; test scroll performance on a mid-range phone.
- Motion: spring-like easing, 180–320 ms, no gratuitous parallax; honour `prefers-reduced-motion`.
- iOS native: SwiftUI components via `@expo/ui/swift-ui`, `expo-glass-effect` for custom glass surfaces on iOS 26+, pre-26 fallback to system materials (blur) via the same tokens, SF Symbols via `expo-symbols`, haptics, native sheets/menus/date pickers, large titles.
- Icons on web: one open icon family chosen in the spike (Lucide or Phosphor "regular"), wrapped in a single `<Icon name>` component with a closed enum; SF Symbols may not be used on the web (licence restricts to Apple platforms).

### §13.3 Android (Material 3)
- Material Design 3 components through `@expo/ui/jetpack-compose` where S-02 confirms coverage; otherwise faithful RN implementations (state layers, ripples, elevation tonal overlays, M3 shapes 4/8/12/16/28/full, type scale Display/Headline/Title/Body/Label with Roboto/Roboto Flex). Use Material 3 **Expressive** (springy motion, shape morphing, larger type contrast, emphasised nav) only where the pinned API supports it (verify).
- **Colour scheme from the brand, not the wallpaper** (government app identity). Roles (dark): primary `#00eeff`, onPrimary `#00363b`, primaryContainer `#004f55`, onPrimaryContainer `#84f3ff`, secondary `#dab9ff`, onSecondary `#411a6c`, secondaryContainer `#3b0a6b`, onSecondaryContainer `#eedbff`, surface/background `#050505`, onSurface `#e7e1e5`, onSurfaceVariant `#ccc4cf`, outline `#958e98`, outlineVariant `#4a454e`, surface containers `#0f0d11 / #151316 / #1d1b1e / #211f22 / #2c292d`, tertiary `#ffb2be`, error `#ffb4ab`. Light scheme in tokens. Optionally expose "Use device colours" (dynamic color) as an **off-by-default** user setting.
- **Icons: Material Symbols only — every icon on Android, including navigation, chips, status, empty states and notification small icons** (monochrome, Material Symbols exported as a drawable for the notification small icon). Style Outlined, weight 400, grade 0, optical size 24; FILL 1 for selected nav items. A lint/CI rule fails the build if any non-Material icon package or raster/vector icon outside the Material Symbols pipeline is imported in Android code paths. Include the Apache-2.0 licence notice.
- Touch targets ≥48 dp; edge-to-edge with correct insets; predictive back; adaptive navigation (bar → rail → drawer); haptic and motion per M3.
### §13.4 Quality bar (reject if any is true)
Looks like a template or "AI-generated" (centered hero with gradient blob, equal-weight card grids, emoji icons, random illustrations, generic stock avatars, Lorem ipsum) · inconsistent spacing/type · glass on content · low contrast · colour-only status · missing empty/error states · layout shift on load · text clipping in Hindi/Tamil · tables unusable on phone.
Visual QA: Playwright screenshots (web: 390, 768, 1280, 1920 px × light/dark/reduced-transparency × en/hi/ta) and device screenshots (iPhone, iPad, Pixel, tablet) attached to each phase report; the `design-reviewer` subagent must sign off.

---

## §14. AI/OCR — bounded assistant and the free multi-provider gateway (SPEC §17)

### §14.1 What AI may and may not do
**Allowed:** (1) candidate field extraction from documents (OCR first; LLM only to structure OCR text, validated against source); (2) duplicate/inconsistency *flags* for humans; (3) cited policy Q&A over approved documents; (4) case summary from authorised fields, labelled as AI. (5) Draft *machine translations* of UI strings for human review (public strings only).
**Never:** bank authenticity, evidence promotion, policy waiver, penalty, forfeiture, release/refund approval, execution; acting as permission checker, database or state machine; generating numbers/dates/clause references not retrieved from records; tools with write access; following instructions found inside documents; sending raw financial documents to a cloud provider without D-12 approval.

### §14.2 Data tiers
- **Tier S (sensitive)**: real case data and documents. Allowed processors: local OCR/local model only, until AICTE approves specific providers (D-12). External providers are `disabled` for Tier S by default and cannot be enabled without the registry approval flow.
- **Tier P (public)**: approved public policy text, synthetic fixtures, public UI strings. May use free external providers (subject to each provider's terms; providers that train on free-tier data are Tier-P only).

### §14.3 Gateway design (`backend/app/ai/gateway`)
Provider registry from `config/LLM_PROVIDERS.yaml` (OpenAI-compatible adapter first; native adapters where needed) · routing by task, tier, language, context size, JSON-mode support · per-provider **token buckets** from configured limits (limits are config; verify at build time, never hard-coded) · **circuit breakers** (open on repeated 429/5xx/timeouts, half-open probe) · jittered retry then **ordered failover** across providers · final fallback: local model (Ollama/llama.cpp, optional) → else "AI unavailable" and the manual workflow (never a failed verification) · request/response validation with JSON Schema/Pydantic, `temperature` low, bounded `max_tokens` · versioned prompts in repo with eval IDs · Presidio redaction (+ Indian recognisers) before any Tier-P call that could contain personal data · metadata-only logging in `llm_requests` (provider, model, latency, tokens, outcome, redaction count) — no raw prompts for Tier S · global kill switch · per-user and per-institution quotas · provider health in admin.
### §14.4 Safety and evaluation
Prompt-injection defence (delimit untrusted text, no tools, schema-constrained outputs, citation resolver that rejects unknown clauses, value-in-source check for extracted fields) · adversarial test pack (hidden text, injected instructions, hallucinated dates/amounts, cross-institution leakage, stale policy retrieval) · field-level precision/recall/correction-rate by document type/scan quality (`docs/ai-evals/`) · feature automatically hidden if the latest eval is below the configured gate or the provider is down.

---

## §15. Security, privacy and compliance (SPEC §14)

### §15.1 Controls to implement (all with tests)
- **Transport/storage:** TLS everywhere, HSTS, secure headers (CSP with nonces, `frame-ancestors 'none'`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`), encryption at rest (DB volume + object SSE + app-level envelope encryption for identifiers), key separation + rotation procedure, private buckets, signed URLs ≤ minutes.
- **Database:** least-privilege roles (app ≠ migration ≠ worker ≠ read-only reporting), no superuser, RLS (§8.5), `statement_timeout`, parameterised queries only, backups encrypted.
- **API:** schemas in/out (Pydantic `extra="forbid"`), allow-list response serialisers (kills mass assignment/property exposure), object-level checks everywhere, idempotency keys, cursor pagination with caps, request size limits, timeouts, CORS allow-list, safe `application/problem+json` errors, correlation ID on every request/log/audit/provider attempt.
- **Rate limits:** login, MFA, upload intents, OCR, search, reconciliation, export, SSE connections, public QR verification; per-user and per-institution quotas.
- **Uploads:** §F-04. **SSRF:** no server-side fetch of user-supplied URLs; connectors use allow-listed hosts; egress policy.
- **Secrets:** none in repo/images/logs; `.env` only locally; deployment secrets via the platform's secret store; `gitleaks` in pre-commit and CI; rotate-on-leak runbook.
- **Mobile (MASVS):** secure storage, no sensitive data in logs/backups (`allowBackup=false`/iOS exclude), certificate validation (consider pinning with rotation plan — document the trade-off), deep-link validation, screenshot/background protections (M-04), clipboard hygiene, minimal local cache, root/jailbreak *threat model documented* (detect-and-warn, not a security boundary), obfuscation/R8 for release.
- **Supply chain:** pinned lockfiles, `pip-audit`, `pnpm audit`, SBOM (syft), signed artifacts (cosign), container scan (Trivy), SAST (Semgrep, bandit), dependency-review, reproducible builds where feasible.
- **Standards traceability:** ASVS 5.0.0 (target level chosen in `docs/security/ASVS_TARGET.md`, default L2 with L3 for the release/decision/audit paths), OWASP API Top 10 2023, MASVS; `docs/security/TRACEABILITY.csv` maps each control to code/test. Do not claim "OWASP compliant" from scanner output.
### §15.2 Privacy (DPDP posture; SPEC §14.5–14.6)
Data inventory (`docs/privacy/DATA_INVENTORY.md`: categories, purpose, roles, retention, residency, sharing), masked identifiers, sensitive values excluded from logs/crash reports/analytics/push, vendor register (push, OCR, e-mail, AI, hosting) with data-handling notes, rights/grievance workflow (F-22), consent/notice surfaces implemented as configurable content with legal sign-off (no invented legal text), and a provision-by-provision DPDP applicability matrix maintained by AICTE counsel (`docs/privacy/DPDP_MATRIX.md` seeded from SPEC §14.5; **do not write "DPDP compliant"**).
### §15.3 CERT-In / logging / time (SPEC §14.4)
Structured logs retained rolling 180 days within Indian jurisdiction (deployment config), NTP/chrony to NIC/NPL-traceable source documented, incident runbook with 6-hour reporting step and POC placeholder (config), security events surfaced to ops.
### §15.4 GIGW / accessibility / certification honesty
Build to GIGW 3.0 expectations and WCAG 2.1 AA; ship `docs/compliance/GIGW_CHECKLIST.md`. **Never state "STQC certified"**; certification is a separate formal process (D-14).
### §15.5 Audit tamper evidence
F-18. State exactly what is guaranteed. Provide `scripts/verify_audit_chain.py` runnable by the auditor.

---

## §16. API contract (SPEC §16)

- Versioned REST under `/v1`, OpenAPI 3.1 generated from code, committed to `packages/api-client/openapi.json`; web and mobile use the same generated client; CI fails if stale. Problem+JSON errors with `code`, `title`, `detail`, `correlation_id`, `retry_after` where relevant. Error families exactly as SPEC §16.3 (401, 403, 404 anti-enumeration, 409 conflict/stale, 422, 429, 503 integration unavailable, 500).
- Groups (design names; implement as needed by §9): Identity (`/me`, `/me/permissions`, `/me/devices`, `/me/sessions`) · Institutions · Instruments (+ `/submit`, `/versions`, `/timeline`) · Documents (upload intent/finalise, download intent, extraction, reviewer confirmation) · Observations · Verification (requests, responses, decisions) · Reconciliation (batches, runs, matches, exceptions) · Renewal/Release (`/renewals`, `/release-requests`, `/checklist`, `/clearances`, `/recommendations`, `/decisions`, `/execution`) · Notifications (`/inbox`, `/inbox/{id}/read|ack`, `/preferences`, `/devices`, `/devices/test`) · Stream (`/stream`) · Reports/Exports · Audit · Admin/Config (roles, policy, connectors, templates, retention, feature registry) · Public (`/public/receipts/verify`).
- High-consequence operations are explicit verbs (`/decisions`, `/execution`) — never a generic `PATCH status`.
- All state-changing endpoints: `Idempotency-Key`, `If-Match`/`ETag` or `row_version`, audit + outbox atomically.
- Webhooks inbound (bank-verifier, e-mail bounces, provider callbacks): signature verification, replay protection (timestamp + nonce), idempotency, SSRF-safe, rate-limited.
- Pagination: cursor; filters bounded; sort allow-list; export size limits.
- Health: `/healthz` (liveness), `/readyz` (DB, object store, outbox lag, scheduler heartbeat), `/metrics` (internal only).

---

## §17. Testing and verification

### §17.1 Pyramid and gates
Unit (domain rules, state machines, money/date maths, policy evaluation) · Integration against real Postgres/MinIO/Keycloak containers (no mocked repositories for authz or RLS) · Contract tests from OpenAPI (Schemathesis) · Authorisation matrix tests generated from `role_permissions` (every role × action × scope × state) · Property tests (search scope, reconciliation idempotence, deadline arithmetic) · E2E web (Playwright) · E2E mobile (Maestro or Detox — choose in spike; real-device smoke for push) · Security tests (§17.3) · Accessibility (axe-core CI + manual scripts) · Load test (k6; record numbers, don't invent SLAs — D-13) · Restore drill · Chaos-lite (kill worker, drop DB connection, revoke FCM credential).

### §17.2 Mandatory scenarios — each must exist as an automated test and be listed in `docs/TRACEABILITY.md`
**PS 26265 scenarios (6):** new FDR submission · validity tracking · approaching maturity · renewal · discrepancy identification · authorised release processing (full chain, each with assertions on DB, audit, notifications and UI).
**SPEC §18.1 (14):** (1) tenant isolation incl. copied UUID/forged filter/deep link · (2) submission → immutable version/hash/receipt/queue · (3) OCR candidate → correction, original kept, no bank-confirmed badge · (4) bank confirmation pending until evidence; inconclusive opens exception · (5) statement import idempotent/quarantine/ambiguity not auto-confirmed · (6) observation lifecycle with timeline preserved · (7) maturity scanner twice → one reminder per key; outage detectable/recoverable · (8) renewal lineage, gap/overlap handling · (9) release checklist blocks, SoD denied, delegation + MFA, execution evidence required · (10) inbox persists when push fails, invalid token cleaned, no fabricated delivered status · (11) prod config refuses demo/fake/sim/test creds · (12) audit tamper denied + detected · (13) backup restore reconciles hashes/counts/keys · (14) provider outage/bounce/bank timeout/worker restart/db failover → controlled states + alerts.
**Mandatory backend authz tests (SPEC §5):** ID swap in path/query/export/document/notification link → denied without existence leak · protected property injection (`status=verified`, `role=admin`, `region=all`, `evidence_level=bank_confirmed`, `approved=true`) rejected/ignored + logged · stale scope denied · pool-reuse RLS leakage test · concurrent approvals/imports create one effect.

### §17.3 Security test checklist (SPEC §18.2) — implement every row
BOLA · function-level authz (including role downgrade mid-session) · mass assignment · auth/session (expired/revoked refresh, fixation, MFA brute force, invitation reuse, recovery abuse) · file abuse (magic bytes, oversize, malformed PDF, scripts, archive bomb, EICAR, OCR hidden text) · financial logic (precision, date/timezone boundary, duplicates, stale update, concurrent approver, out-of-order import, reversal) · notification privacy (lock-screen, forged deep link, push to previous user after logout, token rotation, denied permission, provider outage) · integration safety (SSRF, expired creds, checksum mismatch, timeout, duplicate callback, replay) · audit integrity · mobile (storage, backup leakage, clipboard, screenshots, deep links, TLS validation, cache after logout) · operational resilience · accessibility/usability.

### §17.4 Production guard test (scenario 11)
Forbidden configuration names — the API **refuses to start** with `APP_ENV=production` if any of `DEMO_MODE`, `MOCK_BANK_PROVIDER`, `SIMULATED_CLOCK`, `FAKE_PUSH_SUCCESS` is set truthy, or any variable matching `^(DEMO|MOCK|FAKE|SIMULAT)\w*` (equivalents), or a provider adapter whose class is registered as test-only. The guard lives in `backend/app/core/prod_guard.py` and is covered by a test per flag.
CI builds the production image and: (a) asserts `packages/fixtures` absent; (b) starts the API with each forbidden flag and asserts a refusal exit with a clear message; (c) asserts the clock provider is the real NTP-synced one; (d) asserts no seeded users/institutions exist after migrations; (e) greps bundles for known fixture markers.

---

## §18. CI/CD, deployment and operations (SPEC §15)

- **Environments:** local (docker compose, synthetic fixtures), CI (ephemeral), staging/UAT (synthetic or anonymised data, separate Keycloak realm/DB/buckets/keys/app IDs/FCM project/push endpoints, internal recipients, banner), production (real). Disaster-recovery environment access-restricted. Staging credentials cannot touch production.
- **Pipeline:** PR → lint/typecheck/unit → migration up/down tests → authz tests → SAST/dependency/secrets/container scans → integration + E2E → SBOM → sign artifacts → deploy staging → smoke + migration verification + security checks → release approval → staged production rollout → post-deploy smoke/metrics → rollback or fix-forward with audit record.
- **Deployment artefacts:** Dockerfiles (non-root, read-only FS, minimal base), `docker-compose` for local/self-host, Caddy/Nginx reverse proxy with TLS, Kubernetes manifests/Helm optional (only if hosting requires), `infra/scripts` for backup/restore/rotate keys. **Free-tier note:** free hosting is acceptable for development/staging/hackathon demo; production hosting is an AICTE IT/security/procurement decision (D-09) — document this limitation in `README` and `docs/runbooks/HOSTING.md`; ship portable containers so migration is trivial.
- **Mobile release:** EAS Build profiles (development, preview/internal, production), signing credentials owned by AICTE/team accounts (PREFLIGHT), OTA updates (EAS Update) allowed for JS fixes only after review and never for changes that alter permissions or native modules; Play Internal Testing / TestFlight distribution.
- **Backups/DR:** encrypted DB (PITR) + object backups, restore drill script, RPO/RTO values placeholders awaiting AICTE approval; key-recovery procedure.
- **Observability:** metrics from SPEC §20 (API availability/latency, DB connections, queue backlog/oldest age, scheduler last success, provider accept/fail, invalid tokens, dead letters, backup age, storage growth, quarantine counts, OCR queue, MFA enrolment, denied-access spikes), dashboards, alerts (owner + severity + runbook + escalation), no noisy per-event alerts.
- **Runbooks (write all before go-live; SPEC §15.5):** identity outage/compromise · statement import invalid/duplicate/backlog · push outage / APNs-FCM credential expiry / invalid-token spike · scheduler missed run / clock desync · malware upload / storage exposure · DB restore/failover / object recovery · unauthorised release attempt / SoD collision · data exposure + CERT-In/privacy incident · policy misconfiguration + rollback · key rotation · hosting migration.

---

## §19. Documentation deliverables (build them as you go)
`README.md` (setup in ≤10 commands) · `docs/ARCHITECTURE.md` with diagrams · ADRs in `docs/adr/` · `docs/STACK_LOCK.md` · `docs/OPEN_DECISIONS.md` (D-01…D-14 table with safe default currently implemented) · `docs/PREFLIGHT.md` · `docs/TRACEABILITY.md` (PS capability → module → tests; SPEC section → code/test) · `docs/PARITY_MATRIX.md` · `docs/security/*` · `docs/privacy/*` · `docs/compliance/GIGW_CHECKLIST.md` · `docs/runbooks/*` · `docs/API.md` (generated) · `docs/USER_GUIDES/{institution,officer,verifier,approver,auditor,admin}.md` (+ Hindi/Tamil after review) · `docs/DEMO_SCRIPT.md` (staging walkthrough for the six PS scenarios with measurable-improvement metrics definition — baseline-first, no invented gains) · `docs/KNOWN_LIMITATIONS.md`.

---

## §20. Phases, exit gates, and final report

| Phase | Scope | Exit gate (evidence required in `docs/phase-reports/N.md`) |
|---|---|---|
| 0 Foundations | Read/plan; spikes S-01…S-07; repo scaffold; CI skeleton; STACK_LOCK; PREFLIGHT; OPEN_DECISIONS | Plan approved; spikes documented; `make verify` runs (even if mostly empty); prod-guard test exists |
| 1 Platform | Auth/OIDC/MFA, role model, authorise(), RLS, audit chain, migrations, feature registry, i18n/tokens packages, design-system primitives (web + mobile) | Role×action×scope negative tests green; pool-isolation test green; no secrets in repo; design primitives screenshot-approved |
| 2 Core workflow | Institutions + onboarding, instruments + versions, documents pipeline, intake/scrutiny, observations, comments, assignment queues, receipts | Scenarios 1, 2, 6 + PS "new FDR submission" green on staging with audit/outbox |
| 3 Evidence | OCR assist + review UI, verification requests + bank-verifier portal, statement import + reconciliation, discrepancy engine | Scenarios 3, 4, 5 + PS "discrepancy identification" green; no path creates verified status without evidence |
| 4 Lifecycle & release | Policy registry (drafts), deadline engine, reminders/escalation, renewal lineage, release checklist/clearances/decision/execution | Scenarios 7, 8, 9 + PS "validity tracking / approaching maturity / renewal / authorised release" green; SoD/delegation/step-up tests green |
| 5 Notifications + realtime | Inbox, SSE, FCM/APNs/Web Push/e-mail adapters, prefs, token lifecycle, telemetry, DLQ | Scenarios 10, 14; real-device push round trips recorded (or `blocked` with reason); funnel metrics visible |
| 6 Web app completion | All §11 screens, dashboards/reports/exports, search, help | Playwright suite + a11y + visual QA matrix green |
| 7 Mobile app completion | All §12/§9A features, parity matrix | Maestro/Detox suite; device screenshots; parity matrix has no unexplained gaps |
| 8 AI/OCR gateway | Gateway, providers, evals, policy Q&A, summaries (gated) | Eval report; adversarial pack green; kill-switch + failover tests green |
| 9 Hardening | Security test checklist full run, load test, restore drill, chaos-lite, docs, runbooks, GIGW checklist, ASVS/MASVS traceability | Scenarios 11, 12, 13; no release-blocking findings; `docs/KNOWN_LIMITATIONS.md` honest |

### Final report (end of every phase and at the end)
1. What was built (modules/IDs). 2. Evidence (commands + results, test counts, screenshots list). 3. Spec/PS traceability delta. 4. Deviations and why. 5. Things that are *not* real yet and why (PREFLIGHT items). 6. Open decisions touched. 7. Risks. 8. Next phase entry checklist. No celebratory language; no claims without evidence.

---

## §21. Open decisions (SPEC §21) → what the build does until answered
D-01 policy versions → rules stay `draft`; checks that depend on them display "policy rule not approved". D-02 role/post mapping → roles are functional; delegation limits empty ⇒ approve action denied. D-03 replace vs integrate → system of record for tracked instruments, with import tools; no sync claims. D-04 registry ID/authorisation → CSV import + onboarding review workflow. D-05 bank feed → statement-file import path. D-06 legacy FDR proof → bank-confirmation workflow with attachment; no auto-proof. D-07 BG/e-BG → disabled. D-08 identity provider/Parichay → Keycloak OIDC isolated behind an adapter. D-09 hosting → portable containers + honest limitations. D-10 channels/official notices → conservative default mapping; no claim push is a legal notice. D-11 retention → no invented periods; classes unset ⇒ no disposal. D-12 AI providers → Tier S local-only; external only Tier P. D-13 workload/SLA → measure, don't promise. D-14 GIGW/STQC/VAPT → checklists only.

---

## §22. Production go-live gate (SPEC §23) — you prepare the evidence pack; AICTE decides
Go-live is a formal decision by AICTE business, IT/security, legal/privacy, finance and operations — never a developer checkbox. Maintain `docs/GO_LIVE_GATE.md` with one row per item, evidence link, status and named approver (leave approver blank — do not invent names):
1 Policy register signed off; no unresolved penalty/amount/exemption/tenure/release ambiguity affecting real decisions · 2 Official role mapping + delegation limits; maker-checker where required · 3 Institution verification + account recovery approved; MFA/session revocation exercised · 4 All APIs/documents enforce institution/region/case scope; negative tests + independent security review passed · 5 Upload pipeline operational; private object access + retention tested · 6 Every integration shown as production-enabled has owner, contract, credentials, provenance, monitoring, acceptance evidence · 7 Historical migration reconciled + signed off · 8 Scheduler, reminder idempotency, failure recovery, escalation tested; inbox works if push/e-mail fail · 9 Release/forfeiture flow end-to-end tested (step-up, citations, execution evidence, audit) · 10 Production image has no seeder/demo accounts/fake provider/simulation clock; guard test passes · 11 Backup restore, DR, patching, alerting, incident response, access recertification operational · 12 GIGW/accessibility, DPDP analysis, CERT-In obligations, and any STQC/VAPT/certification complete and documented · 13 Help/support, training, runbooks, monitoring ownership, rollback, vendor contacts ready.
Also maintain `docs/RISK_REGISTER.md` seeded from SPEC §22 (12 risks with required controls) and update it each phase.

---

## §23. Final instructions
Begin now in Plan Mode: (1) read all listed files, (2) write `docs/PLAN.md`, (3) list any contradictions or missing inputs (see PREFLIGHT) as questions, (4) wait for approval, then execute Phase 0. Do not write production code before the plan is approved. When uncertain about a platform API, read the docs; when uncertain about an AICTE rule, mark it open and fail safe.
