---
name: add-state-transition
description: Procedure for adding a state or transition to any FDR portal state machine (instrument, evidence, observation, renewal, release, verification, document, exception).
---
1. Update the transition table (from, to, permission, guard, side effects) — never use a generic status PATCH.
2. Guards must read pinned policy-version rules; if the rule is not `approved`, the guard fails closed with an explanatory reason code.
3. Required data on every transition: actor, reason code (+ free text when required), related evidence, policy version, request id.
4. SoD: confirm maker≠checker constraints at service layer AND with a DB constraint/trigger where the action is consequential.
5. Regenerate the exhaustive transition test (all (from,to) pairs) and add notification events for the new transition (use add-notification-event).
6. Update the UI state badges (web + iOS + Android), i18n keys, and the state diagram in `docs/ARCHITECTURE.md`.
