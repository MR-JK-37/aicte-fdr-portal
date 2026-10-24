---
name: add-endpoint
description: Checklist for adding or changing an API endpoint in the FDR portal backend (authz, schemas, idempotency, audit, outbox, tests, OpenAPI, client regeneration). Use whenever a route is added or its behaviour changes.
---
1. Name the **action verb** (docs/MASTER_PROMPT.md §8.2) the route needs; add it to `role_permissions` data if new.
2. Route calls `authorise(principal, action, resource, context)`; resource is loaded under RLS; missing/foreign resource → 404 (anti-enumeration).
3. Request model: Pydantic `extra="forbid"`; no client-trusted server-owned fields. Response: allow-list serialiser only.
4. State change → go through the state-machine service; in ONE transaction write `state_transitions`, `audit_events`, and the outbox row. Add `Idempotency-Key` and `If-Match`/`row_version` handling.
5. Money = `Decimal`; dates = `date`; instants = UTC; business tz Asia/Kolkata.
6. Tests: happy path; each role×scope negative; wrong state; stale version (409); duplicate idempotency key; protected-property injection; rate limit if applicable.
7. Regenerate OpenAPI + client (`make openapi`), update web AND mobile call sites, update `docs/PARITY_MATRIX.md` and `docs/TRACEABILITY.md`.
8. Run `make verify`.
