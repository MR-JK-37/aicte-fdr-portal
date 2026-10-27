# MASTER IMPLEMENTATION PROMPT — AICTE KOSH (SIH PS 26265)

> Paste this into OpenCode (or your coding agent) from the root of the existing project repository. Use the relevant Agency Agents specialists if installed. This is an implementation brief, not permission to invent real bank/AICTE integration behaviour or to destroy existing working code.

## ROLE AND OBJECTIVE

Act as the technical lead for taking an existing, partially built AICTE KOSH web + mobile project from a mock-data prototype to a genuinely working, persistent, secure application. The project currently has some UI implemented, uses mock data in at least some flows, and has not yet been connected to its production database. The required result is one shared backend, one authoritative PostgreSQL data model, authenticated web and mobile clients, real persistence, real application workflows, tests and reproducible setup documentation.

You must first inspect the repository and trace its actual code paths. Do not pretend to have inspected files that you did not open. Do not blindly rewrite the UI, replace the stack, or add new architecture before understanding the existing implementation. After producing the audit, continue with the implementation in small, testable vertical slices during this work session; do not stop after writing a plan unless an external credential, policy decision or missing deployment resource genuinely blocks the next step.

## AVAILABLE SPECIALIST AGENTS

If the Agency Agents specialists are installed/invocable, use them selectively—not all 200+ agents. Suggested order:

1. `Codebase Onboarding Engineer` — read-only repository map and trace UI→service→API→database flows.
2. `Software Architect` + `Backend Architect` — recommend the smallest reliable backend architecture and API contracts.
3. `Database Optimizer` / `Database Reliability Engineer` — relational model, migration safety, indexes, backups and data integrity.
4. `Identity & Access Engineer` — authentication, RBAC + ABAC, institution isolation, MFA/step-up and sessions.
5. `Mobile App Builder` — connect the existing mobile app to the shared API with secure session storage and consistent state.
6. `AI Engineer` — bounded OCR/LLM gateway, schema validation, evaluation and privacy controls.
7. `DevOps Automator` / `SRE` — environment configuration, CI, observability, deployment and recovery notes.
8. `Code Reviewer` / security specialist — hostile-case testing and final review.

If these agents are unavailable, perform those roles sequentially yourself. Do not assume subagents are actually running unless the tool confirms it. The agency-agents README notes OpenCode can silently drop excess agents in some versions; use a small relevant subset rather than installing the entire roster.

## NON-NEGOTIABLE RULES

1. **Audit first; preserve working code.** Record current tech stack, routes, screens, app entry points, services, mock fixtures, auth and build/test commands before edits.
2. **One backend and one source of truth.** Web and mobile must use the same API and the same authoritative database. Never maintain independent web/mobile databases or divergent workflow logic.
3. **PostgreSQL as system of record.** If the repository already has a sound relational database, use it. Otherwise use PostgreSQL. If Supabase is suitable for this repo, it may provide managed PostgreSQL/Auth/private Storage for prototype/UAT; document Free-tier constraints. Do not automatically use a free personal tier for actual government/financial production data.
4. **Respect existing stack.** Keep working frontend and framework. Choose NestJS/TypeScript or FastAPI/Python only if no existing backend is appropriate; document the trade-off in an ADR. Do not introduce a second backend language without a clear need.
5. **No fake production data.** Remove normal-runtime mock arrays, hardcoded “successful” provider results and demo-only values from production paths. Keep fixtures behind explicit development/test-only commands and environment checks. Production startup must fail safely if fake provider mode is accidentally enabled.
6. **No fake external integration.** Do not claim a bank, RTGS, NeSL, AICTE source, email, push provider or identity provider is connected unless valid credentials and an actual test prove it. Unprovisioned integrations must show `NOT_CONFIGURED`, `AWAITING_EVIDENCE` or equivalent truthful status—never success.
7. **No automatic financial decisions.** AI/OCR must never declare an FDR genuine, approve a release, determine final legal eligibility, calculate an unverified penalty, or bypass required clearances. Maturity is not release authority.
8. **No AI voice/calling subsystem.** Do not add WebRTC/PSTN, AI calling, STT/TTS, call PINs, call recordings or call transcripts.
9. **Server enforces every security decision.** Hiding buttons is insufficient. Never trust `institution_id`, `region`, `role`, `verified`, `approved`, `bank_confirmed`, `delegation_limit` or similar protected fields supplied by a client.
10. **Never leak secrets.** Do not print, expose, hardcode or commit API keys, service-role secrets, signing keys, production credentials or database passwords. Create `.env.example` with placeholders and safe validation. Do not put server secrets in mobile builds or web bundles.
11. **No uncontrolled retries or costs.** Every external request has timeout, capped retry/backoff, rate limits, circuit breaker and observable error handling.
12. **No “done” without proof.** Run the appropriate tests/build/lint/type checks; tell me exactly what passed, failed, was skipped, and why. Never claim production readiness or compliance certification without evidence.
13. Do not ask me for credentials in chat. Wire configuration safely and document which values I must set locally. If a key is missing, implement the truthful disabled/unavailable path and continue other work.
14. If an AICTE statutory/policy/authority decision is unclear, model it as configurable and label it `AICTE_DECISION_REQUIRED`. Do not invent the official answer. Continue all implementation not blocked by that decision.

## PROJECT CONTEXT

**Project:** AICTE KOSH — Security Deposit / FDR Management Portal, SIH 2026 Problem Statement 26265, “Streamline of security deposit/FDR portal.”

**Product goal:** one secure lifecycle for institution deposits, FDR/RTGS evidence, independent verification, document observations, maturity and renewal, release requests, required clearances, authorised decisions, execution evidence and audit history, available from both web and mobile clients.

**Domain requirements to model:** AICTE APH 2024–2027 Clause 6.46 text identifies a release request letter, Affidavit 6, FDR copy or applicable RPGF/DD copies or online payment proof, latest LoA/EoA, relevant PGRC/Vigilance/other-cell clearances, and distinct FDR/RPGF NOC vs RTGS sanction-order paths. Verify the current complete handbook/corrigenda and obtain policy-owner approval before hardcoding rules. A financial-embezzlement hold may need an NOC from the relevant government body/bank. Do not hardcode unsettled penalty percentages, exemptions, dates or delegated authorities.

**Verification boundary:** online payment/RTGS can be reconciled only against an authorised bank/AICTE ledger/source. Legacy paper FDR requires a separately approved bank-confirmation process. OCR, a PDF hash, AI analysis and institution self-declaration do not prove current genuineness, outstanding balance, lien or encashment. If no approved integration is configured, state the exact limitation and keep an auditable manual evidence workflow.

## PHASE 0 — READ-ONLY CODEBASE AUDIT (DO THIS FIRST)

Before editing, inspect the repository files that actually determine behaviour:

- Root manifests, lockfiles, workspace/package configuration, framework versions and build scripts.
- All web/mobile app entry points, routes, screens, layouts, design components and navigation.
- Existing API clients/services, local state, fixture/mock modules, fake delays, fake auth, localStorage/AsyncStorage use and hardcoded arrays.
- Existing backend routes/controllers, database ORM/schema/migrations, environment variables, auth middleware, queue/worker and file storage code.
- Every `TODO`, `mock`, `fake`, `sample`, `demo`, `placeholder`, `seed`, `setTimeout`-as-success and stubbed integration in the active path.
- Existing tests, lint/typecheck/build/test commands, Docker/CI/deployment files and README.
- The current end-to-end path for one representative screen: UI action → client service → network request → handler → authorization → DB/storage write → response → UI refresh.

Run the existing build and tests before changing code, if the environment permits. Record existing failures separately from new failures.

Create these files before implementation:

- `docs/PROJECT_AUDIT.md` — stack, app entry points, command results, actual findings and inspected/uninspected areas.
- `docs/CURRENT_ARCHITECTURE.md` — confirmed architecture and request/data paths.
- `docs/MOCK_DATA_INVENTORY.md` — each mock/fixture, where it is used, whether dev-only or in a production path, and replacement plan.
- `docs/IMPLEMENTATION_PLAN.md` — dependency-ordered vertical slices, risks and blockers.
- `docs/decisions/ADR-001-database-backend.md` — actual selected backend/database and rationale.

Do not guess the repository stack in these documents. Cite real file paths and line numbers where possible.

## PHASE 1 — DATABASE, MIGRATIONS AND A REAL VERTICAL SLICE

Choose and implement the smallest architecture that fits the existing repository. The target design is:

`Web Client + Mobile Client → Shared HTTPS API → Domain Services → PostgreSQL + Private Object Storage + Durable Job/Outbox Worker`.

- Add a tested PostgreSQL connection using the existing ORM/query layer if suitable.
- Create version-controlled, reproducible database migrations. Do not depend on manual-only SQL editor changes.
- Create separate environments for local/dev, CI, staging/UAT and production. Include `.env.example` without real secrets and strict startup validation.
- Add seed/fixture commands that only run for development/tests. Production must not seed fake institutions or fake bank responses.
- Implement an initial vertical slice: authenticate → load `/v1/me` and permissions → create institution-scoped draft instrument → save in PostgreSQL → list/detail/timeline from web and mobile → update a valid state → prove it survives refresh and process restart.
- Make web and mobile call the same API. If the project uses direct Supabase client reads for safe read-only data, enforce tested RLS and keep high-risk state transitions in trusted backend functions.
- Add migrations, API validation, transaction boundaries, standard errors, pagination, request IDs and integration tests.

## CORE DATA MODEL

Adapt this to the current project; avoid duplicate tables that mean the same thing. At minimum model:

- `institutions`, `institution_programmes` / approvals (effective-dated source attributes).
- `users` or identity profiles, `institution_memberships`, `role_assignments`, approved scope/delegation records.
- `instruments`, `instrument_versions`, `instrument_relationships` (renewal/replacement lineage).
- `documents`, `document_versions`, OCR jobs/extractions and authorised document-access events.
- `evidence_items`, `verification_requests`, `verification_responses`, reconciliation batches/matches.
- `observations`, institution responses and resolution events.
- `release_requests`, `release_checklist_items`, `clearance_requests`, `approvals`, `execution_evidence`.
- `policy_rules`, `policy_rule_versions`, `policy_sources` and policy test scenarios.
- `notifications`, `notification_outbox`, `job_runs`, `integration_attempts`.
- `audit_events`, `access_events`, `security_events`, bounded export jobs.
- Optional `ai_jobs`, `model_registry`, `prompt_versions`, and evaluation records only when needed.

Use foreign keys, uniqueness constraints, decimal types for money, timezone-aware timestamps, indexes for scope filters, optimistic concurrency (`version`/ETag) and idempotency keys. Preserve provenance: declared, extracted, reviewed, bank-confirmed and ledger-reconciled values must not overwrite each other.

## PHASE 2 — AUTHENTICATION, ROLES AND AUTHORIZATION

Implement one identity system with role-driven workspaces, not separate hardcoded credentials or a role selector that grants privilege. Use an approved OIDC/SSO provider when supplied; otherwise use the current auth provider for the prototype and document the production identity decision.

Proposed functional roles (all must be configurable and mapped to actual approved posts before production):

1. **Institution Organisation Admin** — one institution; invite/manage institution users and contacts only.
2. **Institution Submitter / Compliance Officer** — own institution; create/edit drafts, submit records, upload evidence, respond to observations and request renewals/releases.
3. **Institution Viewer** — own institution, read-only.
4. **Intake / Registry Officer** — assigned queue/region; completeness check and routing.
5. **Scrutiny Officer** — assigned cases; evidence review, observations and recommendation.
6. **Finance / Verification Officer** — approved source/account scope; review bank evidence and reconciliation exceptions.
7. **Regional Supervisor / Bureau Reviewer** — explicit assigned region/bureau; queue and escalation review.
8. **Competent Authority / Release Approver** — only approved delegated scopes/limits; independent release decision.
9. **Audit / Compliance Reviewer** — scoped read-only access to records, history and logs.
10. **Identity / Access Administrator** — identity lifecycle and approved role grants; no automatic business case access.
11. **Platform / Security Operator** — infrastructure/operations scope; not a business approver and no default routine access to plaintext FDR documents.
12. **Integration Service Identity** — named connector/job with minimal scoped permissions; non-interactive.
13. **Participating Bank Verifier** — optional and disabled unless formally onboarded; limited to assigned confirmation requests.

Implement RBAC + ABAC. Each authorization must check: active identity/session; permission; institution/region/case/programme scope; current resource state; delegation; policy version; separation of duties; MFA level if required. Deny if attributes are missing/ambiguous. Record reason/correlation ID for high-impact writes.

Mandatory safety tests:

- User of Institution A cannot access Institution B's record/document by changing path ID, query, export, search filter, deep link or client state.
- Client cannot set `role=admin`, `verified=true`, `approved=true`, `bank_confirmed=true`, `institution_id` or `region` to obtain privilege.
- Correct role with expired assignment/revoked session is denied.
- Submitter/recommender cannot approve the same case when maker-checker is required.
- Two concurrent approvals/imports cannot create duplicate decisions or side effects.
- If Supabase is used, test table grants + RLS for every exposed table, and keep secret/service-role keys server-side only.

Require MFA for privileged/approval roles and step-up re-authentication for release decisions, policy publication, role elevation and other high-risk actions. Verify institutional authority via an approved workflow; email verification by itself is insufficient.

## PHASE 3 — BUSINESS WORKFLOWS (REAL PERSISTENT STATE)

### Instrument lifecycle

`DRAFT → SUBMITTED → INTAKE_REVIEW → SCRUTINY → ACTIVE_TRACKING`, with explicitly authorised cancellation, supersession or archival paths.

### Evidence lifecycle

`DECLARED → EXTRACTED (optional) → REVIEWED → BANK_CONFIRMED or LEDGER_RECONCILED where the evidence type permits`; alternative states `INCONCLUSIVE` and `REJECTED` require reason and provenance.

### Observation lifecycle

`OPEN → AWAITING_INSTITUTION → RESPONSE_RECEIVED → UNDER_REVIEW → RESOLVED/CLOSED`; reopening requires a reason and audit event.

### Release lifecycle

`DRAFT → SUBMITTED → COMPLETENESS_REVIEW → REQUIRED_CLEARANCES → SCRUTINY/RECOMMENDATION → COMPETENT_AUTHORITY_DECISION → EXECUTION_PENDING → RELEASED/DISCHARGED` only with trusted execution evidence. Explicit alternative paths include `RETURNED`, `DEFERRED`, `REJECTED` and `CANCELLED` with authorised transition/reason.

Do not compress these workflows into one overloaded status field. Use transactional, allow-listed state transitions. Keep the instrument lifecycle separate from its evidence and release request lifecycles.

### Institution flows

- Dashboard of own institutions/deposits, outstanding actions, upcoming maturities and submitted cases.
- Register new instrument/payment evidence, save draft, upload docs, submit, review observations and resubmit corrected versions without erasing old submitted snapshots.
- Request renewal/replacement and create explicit old→new instrument links.
- Request release with a dynamic versioned checklist; show why an item is required or pending.
- See status timeline, permitted notifications and read-only history.

### Internal staff flows

- Intake queue, region/assignment filters, completeness review, reassignment and due-date monitoring.
- Scrutiny screen showing field-level evidence provenance, differences, document versions and notes.
- Verification screen to record authorised source, request/reference, response, outcome and evidence.
- Clearance inbox where each required cell has an explicit pending/received/cleared/not-cleared state and evidence/reason.
- Approval screen with delegation, step-up auth, complete checklist, prior independent decision, hold/exception information and reasoned outcome.
- Audit/reporting screen with least-privilege exports and data masking.

### Workflow invariants

- Maturity date never automatically means released/eligible.
- `RELEASED` requires trusted execution evidence after the authorised process confirms release/settlement.
- A file's presence is not proof of authenticity or an adequate clearance.
- Missing source response must remain pending/unavailable, not green.
- Policy rules and decisions use a pinned policy version and keep history.
- Submitted evidence is versioned; never silently overwrite it.

## PHASE 4 — SECURE FILE UPLOAD AND OCR

Implement secure upload with private bucket, size/page limits, magic-byte/MIME validation, extension allowlist, quarantine, malware scanning where available, archive bomb protection, safe filenames, document metadata/version table and authorised time-limited download links.

OCR should be asynchronous. Record job status, retry attempts and failure reason. Store page/region text and extracted field candidates with confidence and OCR/model version; permit reviewer corrections while keeping extraction history. Label the UI clearly:

- “Extracted by OCR/AI” is not “verified.”
- “Reviewed” is not “bank-confirmed.”
- “Bank-confirmed” requires a named authorised confirmation source/evidence.
- “Ledger-reconciled” applies to the actual online-payment reconciliation path.

First evaluate local OCR such as Tesseract/PaddleOCR on allowed sample documents. Measure exact-match accuracy for instrument IDs, amounts and dates; do not infer production-grade OCR from marketing claims. Keep OCR processing isolated from the API request path.

## PHASE 5 — MATURITY, EMAIL/PUSH AND BACKGROUND JOBS

- Build maturity queries over persisted dates and approved policy configuration.
- Use a durable outbox/job worker with transactional event creation and idempotent dispatch.
- Provide in-app notifications first; add email/FCM/APNs/Web Push only when real provider keys and approved templates are configured.
- Track `QUEUED`, `PROVIDER_ACCEPTED`, `DELIVERY_CONFIRMED` (only when provider supports it), `OPENED` and `ACKNOWLEDGED` separately.
- Never claim that an operating system displayed a push immediately.
- If provider credentials are missing, label the adapter as `NOT_CONFIGURED`; no fake success.
- Use capped retries/backoff, dead-letter/error states, health checks and scheduled-job observability.

## PHASE 6 — GROQ / OPENROUTER / FREE MODEL INTEGRATION

Implement a small **server-only AI provider gateway**, not separate provider code inside every screen. Use capability-level methods such as:

- `classify_document` — propose a document type.
- `extract_document_fields` — structured candidate fields and evidence page references.
- `compare_document_fields` — list conflicts between form/OCR/source evidence.
- `summarise_case` — concise summary of assigned case and outstanding tasks, with IDs/links to source records.
- `answer_policy_question` — retrieve from a versioned, approved policy corpus and cite clause/version.

Provider requirements:

- Groq and OpenRouter are optional configured providers, not required for the core app to work.
- Model IDs, allowed tasks, timeouts, token limits, rate limits, budgets and fallback order are configuration, not assumptions.
- Never expose `GROQ_API_KEY`, `OPENROUTER_API_KEY`, Supabase secret/service key or database URL with credentials to browser/mobile code.
- Use structured JSON Schema/Pydantic/Zod output validation and bounded retries. Never execute model-generated SQL or accept a free-form model response as a state transition.
- Use a provider allowlist; avoid sending unredacted institution, FDR, bank or personal data to free/unapproved services. Groq documents limited retention exceptions and US data location; Google's unpaid Gemini terms allow content use for improvement/human review; OpenRouter free quotas/provider policies vary. Check current terms and procurement/data approval first.
- For demo data use obviously synthetic institutions, accounts, identifiers and documents. Never upload real financial documents to a free model to make the demo look advanced.
- Add request budgets, rate limiting, per-tenant quota, concurrency cap, timeout, retry cap, exponential backoff, circuit breaker and provider health states.
- Log provider/model/prompt version, task, outcome, latency, token counts and error class, but do not log raw sensitive prompts or document contents by default.
- If provider not configured, show `AI_DISABLED`/`AI_UNAVAILABLE` and allow manual processing. Do not block required manual review.
- Do not use an LLM to decide whether a deposit is genuine, apply policy/penalties, issue a clearance or release funds.

### Model evaluation

Build a safe evaluation script/dataset from synthetic or authorised, redacted examples. Track per-field exact match, amount/date normalization errors, document-type precision/recall, false discrepancy rate, reviewer correction rate, latency and provider failure rate. Version the model/prompt and retain aggregate metrics only. A model is not selected because it is free or trending; select by measured quality, latency, privacy terms and operational cost.

## PHASE 7 — AUDIT, REPORTING AND OPS

- Build a timeline from persisted events, not computed client-side guesses.
- Store actor, action, resource IDs, timestamp, reason, policy version, correlation ID and evidence reference for consequential decisions.
- Restrict audit DB rights; protect logs from normal app operators; add central forwarding/checkpoints if feasible. A simple hash chain is tamper-evident only under additional controls and is not automatically immutable.
- Reports must be query-scoped to the user's role. Bulk export requires explicit permission, bounded filters, audit event and masking rules.
- Add health endpoints, structured logs, request IDs, DB/worker/provider metrics and safe error messages.
- Create backup/export instructions and test a restore. Include object storage as well as database metadata.
- Add environment-specific startup checks: production must reject dev seed mode, mock integrations, wildcard CORS and missing critical secrets.

## REQUIRED TEST MATRIX

Add tests appropriate to the project's framework. At minimum:

1. Unit tests for date/amount normalization, field validation, release checklist conditions and state-transition rules.
2. Database migration tests from an empty database and from the prior schema.
3. Integration tests for auth, instrument CRUD, document metadata, observations, release request and timeline.
4. Positive/negative authorization tests for every role/scope, including cross-institution IDOR and exports.
5. Maker-checker tests including concurrent requests and duplicate idempotency keys.
6. File security tests: wrong MIME/magic bytes, large file, malformed PDF, empty file, duplicate, forbidden extension, unauthorised download.
7. Worker tests for retry, dead-letter, repeated job, scheduler rerun, provider failure and duplicate notification prevention.
8. AI tests for invalid JSON, hallucinated/missing fields, prompt injection within document text, low confidence and provider timeout/rate-limit; verify AI cannot mutate business state.
9. Web E2E for institution submitter and internal reviewer; mobile E2E for sign-in, create/view same record, uploads, notification inbox and logout/session revocation.
10. Production configuration tests ensuring mock providers/seeds and credentials are not present in release build.

Do not use only mocks to prove database integration. At least one CI integration suite must run against a real disposable PostgreSQL instance. Mock external bank/notification/AI providers only in unit/CI tests and mark them test-only; production code must surface unavailable status rather than mocked success.

## REQUIRED IMPLEMENTATION ARTIFACTS

Keep these updated as work proceeds:

- `docs/PROJECT_AUDIT.md`
- `docs/CURRENT_ARCHITECTURE.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/ROLE_PERMISSION_MATRIX.md`
- `docs/WORKFLOW_STATE_MACHINES.md`
- `docs/DATA_MODEL.md` or ER diagram
- `docs/API.md` or generated OpenAPI spec
- `docs/AI_PROVIDER_POLICY.md`
- `docs/SECURITY_CHECKLIST.md`
- `docs/INTEGRATIONS_STATUS.md` listing each integration as `LIVE_TESTED`, `SANDBOX_TESTED`, `NOT_CONFIGURED`, `BLOCKED_POLICY`, or `TEST_ONLY`
- `.env.example`
- database migrations and tests
- reproducible README setup/test/deploy instructions

## WORK EXECUTION STRATEGY

- First produce the read-only repository audit, then immediately start implementing the highest-value vertical slice.
- Make one coherent, verifiable batch at a time: migrations → API → UI/mobile integration → tests.
- After each batch run targeted tests and the relevant app build. Do not proceed while introducing new unresolved failures; if a pre-existing failure blocks a test, record it.
- Make small changes and preserve existing design/components wherever possible. Do not restyle the entire product unless necessary for a working flow.
- Do not claim “complete” if a credential, bank API, AICTE source, identity provider or external service is not available. Implement the integration adapter and truthful blocked state, document the dependency, and complete the rest of the workflow.
- Do not stop at sample JSON, static dashboards, a mocked API or a schema-only change. The goal is real persistence and real end-to-end flows.

## FINAL RESPONSE FORMAT

When finished, report:

1. **What you inspected:** exact key paths and commands.
2. **What was implemented:** actual screens, APIs, tables/migrations, roles and workflows.
3. **What is now real vs still blocked:** DB, auth, storage, OCR, Groq, OpenRouter, email/push, bank/AICTE integrations—each with evidence/state.
4. **Test results:** commands and pass/fail counts, plus known failures.
5. **Security review:** tenant-isolation, role, maker-checker, file-access and secret-handling tests.
6. **How to run locally:** exact commands and required `.env` names, but never expose values.
7. **Manual actions still required from me:** only those requiring external credentials or AICTE approval.
8. **Known limitations and next implementation slice.**

Never state that a feature works unless you can point to implemented code and a test/demo that proves it.
