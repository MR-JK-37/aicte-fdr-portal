---
name: add-notification-event
description: Procedure for adding a notification event type (recipients, template, deep link, privacy, tests) to the FDR portal.
---
1. Define category (`critical_workflow|deadline|security_account|operations|digest`), recipient rule (resolved from CURRENT scope/assignment at dispatch time), urgency, dedupe key, and deep link.
2. Template key + version with a minimal payload for lock screen (no FDR number, amount, bank, legal names). Provide en text; hi/ta marked `machine-draft` until reviewed (falls back to en in production).
3. The domain code only writes an outbox row inside its transaction; it never calls a provider.
4. Tests: recipients correct; inbox row created even if all providers fail; canary-string test proves no sensitive value in the push payload; deep link to out-of-scope entity returns the safe 404; dedupe works on re-run.
5. Add to the event catalogue in docs/MASTER_PROMPT.md §10.3 and to the admin template list.
