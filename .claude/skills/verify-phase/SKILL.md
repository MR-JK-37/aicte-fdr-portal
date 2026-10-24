---
name: verify-phase
description: Close-out procedure for a build phase of the FDR portal — runs verification, reviews, and writes the phase report with evidence.
---
1. `make verify`; capture the summary (counts of tests, failures, skipped — skipped tests need a reason).
2. Run web E2E and (when applicable) mobile E2E; capture screenshots (390/768/1280/1920 × light/dark/reduced-transparency × en/hi/ta for web; device matrix for mobile).
3. Invoke subagents: `reviewer`, `security-auditor`, `design-reviewer` (if UI), `spec-auditor` (sections of this phase). Fix BLOCKER/MAJOR items, re-run.
4. Write `docs/phase-reports/N.md` in the MASTER_PROMPT §20 format (built, evidence, traceability delta, deviations, not-yet-real items, open decisions, risks, next-phase checklist).
5. Update `docs/TRACEABILITY.md`, `docs/PREFLIGHT.md`, `docs/KNOWN_LIMITATIONS.md`.
6. Commit in small conventional commits. Do not start the next phase.
