# Stream R7 Closeout Report — Realtime, Push, and Notifications

**Status:** PASS  
**Branch:** `v2/fix-and-complete`  
**Milestone:** Stream R7 (Realtime, Push, and Notifications per `docs/MASTER_PROMPT_V2.md` §10)  
**Date:** 2026-10-24  

---

## 1. Executive Summary

Stream R7 delivers the complete **Realtime, Push, and Notification System** across the backend (`services/api`), web client (`apps/web`), and mobile companion (`apps/mobile`), strictly obeying the requirements of **MASTER_PROMPT_V2 §10** and satisfying **Exit Gates G-20, G-21, and G-22**.

The notification system adheres to an **Inbox-First Source of Truth** architecture:
1. Every domain event creates a persistent user inbox record before attempting external push dispatch.
2. Push state progression tracks the full state ladder: `CREATED` $\rightarrow$ `PROVIDER_ACCEPTED` / `PROVIDER_FAILED` $\rightarrow$ `OPENED` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `ACTIONED`.
3. When external push provider credentials (FCM / APNs / WebPush) are unconfigured, the system reports `NOT_CONFIGURED` gracefully without crashing, leaving inbox and realtime SSE fully operational.
4. All lock-screen push payloads undergo strict data sanitization and canary testing in English, Hindi, and Tamil: FDR numbers, rupee amounts, bank names, and institution names are strictly prohibited on lock-screens.
5. Server-Sent Events (`/v1/stream`) support `Last-Event-ID` resumption with replay from Postgres `sse_events`, enforcing per-event re-authorization so principals only receive events within their current institution/role scope.

---

## 2. Deliverables & Technical Architecture

### 2.1 R7.1 Server-Sent Events (SSE) Stream (`/v1/stream`)
- **Location:** `services/api/app/realtime/router.py`
- **Capabilities:**
  - Standard Server-Sent Events endpoint with 15-second heartbeat keep-alives (`: keep-alive\n\n`).
  - `Last-Event-ID` header and query parameter catch-up phase: queries `sse_events` for sequence IDs greater than the client's last observed sequence number.
  - Per-event re-authorization (`is_event_authorized_for_principal`): evaluates each event against the connecting principal's user identity, role, and institution scope before emission.
  - Row-Level Security (RLS) integration: session context (`app.role`, `app.user_id`, `app.institution_id`) is properly propagated to ensure tenant isolation.

### 2.2 R7.2 Notification Pipeline & Outbox (`app/notifications/`)
- **Inbox-First Persistence:**
  - `process_domain_event` creates `UserNotification` entries in PostgreSQL first.
  - State ladder progression:
    - `/v1/notifications/{id}/read` $\rightarrow$ transitions to `OPENED`.
    - `/v1/notifications/{id}/acknowledge` $\rightarrow$ transitions to `ACKNOWLEDGED`.
    - `/v1/notifications/{id}/action` $\rightarrow$ transitions to `ACTIONED`.
- **Statutory Protection:**
  - `UNSUPPRESSIBLE_CATEGORIES = {"critical_workflow", "security_account"}` cannot be disabled or muted via `/v1/notifications/preferences`.
  - Attempts to disable statutory alerts return HTTP 400 with `"Statutory and critical compliance notifications cannot be disabled"`.
- **Dead-Letter Queue (DLQ) & Resilience:**
  - Provider exhaustion routes failures to `NotificationDLQ` table.
  - Admin inspection (`GET /v1/notifications/dlq`) and replay endpoint (`POST /v1/notifications/dlq/{id}/replay`) restricted to `PLATFORM_OPERATOR` and `IDENTITY_ADMIN`.
  - Funnel metrics (`GET /v1/notifications/funnel`) track count breakdowns at each pipeline stage.

### 2.3 R7.3 Lock-Screen Privacy & Canary String Testing
- **Template Sanitization:** `services/api/app/notifications/templates.py` renders versioned templates for `en`, `hi`, and `ta`.
- **Canary Invariant:**
  - Lock-screen title and body use generic templates (e.g., *"Deposit submission received"*, *"Action required on compliance item"*).
  - Canary test verifies that `SECRET-FDR-998877`, `99,99,999.00`, `Secret Custodial Bank`, and `Confidential National Institute` never appear on lock-screen payloads across any language.

### 2.4 R7.4 Device Lifecycle & Push Token Revocation
- **Registration (`POST /v1/devices/register`):**
  - Registers device installations with platform (`android`, `ios`, `web`) and provider (`fcm`, `apns`, `webpush`).
- **Revocation (`POST /v1/devices/revoke`):**
  - Marks installation `is_active=False` and timestamps `revoked_at`.
  - On user logout, device tokens are revoked to prevent any stale notification delivery.

---

## 3. Verification & Exit Gates

| Gate | Requirement | Status | Evidence |
|---|---|---|---|
| **G-20** | Reconnect with `Last-Event-ID` replays missed events and re-authorises each | **PASS** | `test_g20_sse_per_event_reauthorization_and_replay` & `test_g20_sse_generator_catchup_replay` in `tests/test_stream_r7_notifications_and_sse.py`. |
| **G-21** | Inbox is source of truth; state ladder `CREATED` $\rightarrow$ `ACTIONED`; honest `NOT_CONFIGURED` when push credentials absent | **PASS** | `test_g21_inbox_first_and_state_ladder` & `test_scenario_10_notifications_inbox_and_delivery.py`. |
| **G-22** | Lock-screen payloads contain no sensitive values (canary test); logout revokes device tokens | **PASS** | `test_g22_lock_screen_canary_sanitization` & `test_g22_device_registration_and_logout_revocation` in `tests/test_stream_r7_notifications_and_sse.py`. |
| **RLS** | Shared DB dependency across auth and handlers | **PASS** | Fixed session dependency caching in `app/auth/deps.py` so RLS context (`app.user_id`, `app.role`) cleanly applies across all notification endpoints. |
| **CI** | Full platform verification (`make verify`) | **PASS** | 632 backend unit/integration tests PASS, 29 web vitest tests PASS, mobile icon hygiene PASS, forbidden-strings PASS, 17 prod-guard tests PASS. |

---

## 4. Next Stream

**Stream R8:** Hardening, performance, security audit, and documentation handover.
- Security scan (gitleaks, dependency audits, security headers, EICAR/zip-bomb protection).
- Final end-to-end integration verification and production readiness checklist.
