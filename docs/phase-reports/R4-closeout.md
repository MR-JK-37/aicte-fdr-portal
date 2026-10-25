# Stream R4 Close-Out — Missing Backend Modules & Security Invariants (2026-10-24)

Concludes Stream R4 ("Missing backend modules") per `docs/MASTER_PROMPT_V2.md` §7.

---

## 1. Scope & Delivered Backend Modules

### 1. Dashboard API (`services/api/app/dashboard/router.py`)
- **Endpoints:**
  - `GET /v1/dashboard/summary`: Scope-filtered counts for all operational categories (`active`, `expiring_30d`, `expiring_60d`, `expiring_90d`, `matured`, `renewed`, `released`, `pending_verification`, `open_observations`, `awaiting_institution`, `reconciliation_exceptions`, `release_by_stage`, `overdue_and_ageing`, `evidence_distribution`).
  - `GET /v1/dashboard/my-work`: Role- and scope-filtered action items requiring user attention with deep links and priorities.
  - `GET /v1/dashboard/due-soon`: Instruments nearing maturity within specified horizon (<= 30 days).
  - `GET /v1/dashboard/activity`: Recent auditable events strictly within user's institutional/regional scope.
- **Invariants Enforced (Exit Gate G-14):**
  - No synthetic composite scores (no arbitrary "98.5% Compliance Index").
  - Counts equal list totals (`data["active"]["count"] == len(client.get("/v1/instruments").json())`).
  - Every count is paired with an actionable drilldown filter object.

### 2. Reports & Exports Engine (`services/api/app/reports/router.py`)
- **Endpoints:**
  - `GET /v1/reports/catalogue`: Published report catalogue with definitions and formats.
  - `POST /v1/reports/{key}/runs`: Asynchronous/synchronous report execution with mandatory business reason.
  - `GET /v1/export-jobs`: Paginated list of export runs.
  - `GET /v1/export-jobs/{id}`: Detailed export job metadata, SHA-256 hash, and row count.
  - `GET /v1/export-jobs/{id}/download`: Download export artifact with `X-Content-SHA256` integrity header.
  - `GET/POST /v1/report-schedules`: Scheduled report runs CRUD.
- **Invariants Enforced (Exit Gate G-14):**
  - Cross-tenant isolation: Tenant B cannot access or download Tenant A's export job (403/404).
  - Identifier masking: FDR numbers masked (`XXXX...`) unless user holds `view_unmasked_identifiers`.
  - CSV Formula Injection Neutralization: `sanitize_csv_cell` neutralizes formula injection triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) by prepending a single quote (`'`).

### 3. Universal Search & Saved Views (`services/api/app/search/router.py`)
- **Endpoints:**
  - `GET /v1/search?q={query}`: Universal cross-entity scoped search (instruments, institutions, observations, release requests) with blind-index match for FDR identifiers.
  - `GET/POST/PATCH/DELETE /v1/saved-views`: CRUD for user saved search filters and views.
- **Invariants Enforced (Exit Gate G-15):**
  - Search never leaks out-of-scope rows: searching for universal queries (e.g. `99999`) never returns instruments belonging to other institutions.

### 4. Reminder Scheduler & Calendar Feed (`services/api/app/reminders/router.py`)
- **Endpoints:**
  - `GET /v1/reminder-schedules`: Schedule configurations and version history.
  - `POST /v1/reminder-schedules/versions`: Maker draft schedule creation.
  - `POST /v1/reminder-schedules/approve`: Checker schedule approval (Maker != Checker SoD).
  - `GET /v1/scheduler/status`: Distributed database-leased scheduler status with alert when schedule is unapproved.
  - `GET /v1/calendar/maturities`: JSON calendar feed of upcoming maturities.
  - `POST /v1/calendar/feed-token`: Token generation for external calendar integration.
  - `GET /v1/calendar/feed.ics`: RFC 5545 iCalendar feed for desktop and mobile calendar subscription.
- **Invariants Enforced (Exit Gate G-16):**
  - Maker-checker separation: schedule creator cannot approve their own schedule version (403).
  - Unapproved schedule alert: status endpoint explicitly alerts if no approved schedule version is active.

### 5. Audit Chain Verification Job (`services/api/app/audit/router.py`)
- **Endpoints:**
  - `GET /v1/audit/events`: Paginated audit log retrieval with JSON before/after state diffs.
  - `GET /v1/audit/access-logs`: Filtered access logs for identity administrators.
  - `GET /v1/audit/chain/status`: Current hash-chain status, total entries, and signed checkpoint metadata.
  - `POST /v1/audit/chain/verify`: On-demand SHA-256 hash-chain verification job walking the entire ledger.
  - `POST /v1/audit/exports`: Cryptographically sealed audit log export.
- **Invariants Enforced (Exit Gate G-18):**
  - Hash chain cryptographic verification job confirms tamper-evident immutability (`status: "VERIFIED"`, `ok: True`).

### 6. Users & Access Management (`services/api/app/users/router.py`)
- **Endpoints:**
  - `GET/POST /v1/users`: User directory and user provisioning with initial credentials.
  - `GET/PATCH /v1/users/{id}`: User profile lookup and update / deactivation.
  - `POST /v1/users/{id}/unlock`: Account unlock following security lockout.
  - `GET/POST /v1/invitations`: Institution staff invitation lifecycle.
  - `POST /v1/role-assignments/requests`: Maker requests role upgrade/assignment.
  - `POST /v1/role-assignments/{id}/approve`: Checker approves role assignment (with step-up MFA).
  - `POST /v1/role-assignments/{id}/reject`: Checker rejects role assignment.
  - `GET/POST /v1/recertification-campaigns`: Periodic access recertification campaigns.
- **Invariants Enforced (Exit Gate G-12):**
  - Maker-checker SoD: Nobody can request or grant themselves a role (403).
  - Separation of duties: requester cannot approve their own role change request (403).
  - Step-up MFA enforced on role approval: approving without fresh step-up returns 403 `step_up_required`.
  - Immediate session revocation: deactivating a user immediately revokes all active sessions.

### 7. Support, DPDP Rights & Data Retention (`services/api/app/support/router.py`, `app/retention/router.py`)
- **Endpoints:**
  - `GET /v1/help/articles`: FAQ and regulatory help articles catalogue.
  - `POST/GET /v1/support-requests`: Support ticket submission with `X-Correlation-ID` tracking.
  - `POST/GET /v1/rights-requests`: Digital Personal Data Protection (DPDP) Act compliance requests (access, correction, erasure).
  - `GET/POST /v1/retention/classes`: Statutory retention classifications.
  - `GET/POST /v1/retention/legal-holds`: Legal hold creation freezing records from automated disposal.

---

## 2. Database Migration Lifecycle

- Migration script: `services/api/migrations/versions/f6a7b8c9d0e1_stream_r4_backend_modules.py`.
- Tables added:
  - `export_jobs`, `report_schedules`
  - `audit_verification_jobs`
  - `user_invitations`, `role_assignment_requests`, `recertification_campaigns`
  - `saved_views`
  - `reminder_schedules`, `calendar_feed_tokens`
  - `support_requests`, `rights_requests`
  - `retention_classes`, `legal_holds`
- **Reversibility verification:**
  - `alembic upgrade head` $\rightarrow$ PASS
  - `alembic downgrade -1` $\rightarrow$ PASS
  - `alembic upgrade head` $\rightarrow$ PASS

---

## 3. Automated Verification & Exit Gates

- **Dedicated Test Suite (`services/api/tests/test_stream_r4_modules.py`):**
  - `test_dashboard_summary_counts_equal_list_totals`: PASS (Exit Gate G-14)
  - `test_report_export_neutralizes_csv_injection_and_masks_identifiers`: PASS (Exit Gate G-14)
  - `test_search_never_returns_out_of_scope_rows`: PASS (Exit Gate G-15)
  - `test_reminder_scheduler_maker_checker_and_unapproved_alert`: PASS (Exit Gate G-16)
  - `test_audit_verification_job_verifies_integrity`: PASS (Exit Gate G-18)
  - `test_users_access_sod_and_session_revocation`: PASS (Exit Gate G-12)
  - `test_support_rights_and_retention`: PASS (Exit Gate G-14)
- **Full Backend Suite:** 625 passed, 1 skipped, 0 failed in 35.6s
- **Production Guard Tests:** 17/17 passed
- **OpenAPI Schema Sync (`make openapi`):** Synchronized at `packages/api-client/openapi.json`
- **Client Build & Typecheck:** `pnpm --filter @aicte-fdr/api-client run generate && tsc --noEmit && test` PASS
- **Repository Verification Gate (`make verify`):**
  - Backend ruff check: PASS (0 errors)
  - Full pytest suite: 625 passed
  - Frontend workspace build: 7 of 7 packages PASS
  - Web & Mobile test suites: PASS
  - Forbidden strings: PASS
  - No business literals: PASS (0 violations)
  - Audit chain verification: PASS (0 tamper points detected)
  - Output: `ALL GATES GREEN (Phase 1 Platform verification complete)`
- **Live Smoke Test Gate (`make smoke-test`):** PASS (OpenAPI 200, wrong-password rejection 401, mobile CORS headers verified)
