# PHASED_PROMPTS_V2.md — paste these into Claude Code one at a time

Use a **fresh session** (or `/clear`) for each prompt; `CLAUDE.md` loads automatically. Each prompt re-reads the files it needs. Do not skip an exit gate. Put the repo's current `git status` clean before starting. Every prompt ends with the close-out block (repeated here once, then referenced).

**Close-out block (applies to every prompt):** run `make verify`; run the `reviewer` and `security-auditor` subagents on the diff; run `spec-auditor` on the sections named; run `design-reviewer` on screenshots for any UI change; write `docs/phase-reports/R<n>.md` per MASTER_PROMPT_V2 §14; update `docs/TRACEABILITY.md`; commit in small conventional commits; finish with `STREAM R<n>: PASS` or `STREAM R<n>: BLOCKED — <reason>`.

---

## PROMPT A — Kick-off (plan only, no code)
```
Read CLAUDE.md, docs/MASTER_PROMPT_V2.md, docs/AUDIT_REPORT.md, docs/AUTH_ROLES_MATRIX.md, design/DESIGN_SPEC.md and open design/preview.html in headless Chromium (screenshot it and look at it). Skim docs/MASTER_PROMPT.md (v1) section list and docs/spec/SPEC_v3.md headings.
Then, WITHOUT changing source code: git switch -c v2/fix-and-complete; write docs/PLAN.md (≤2 pages), docs/INVENTORY.md (repo map, versions, how each app starts, current test results, route table with authz/scope/RLS/idempotency/audit/test columns — fill it by reading code and running tests, do not assume), and docs/DECISIONS.md with ADR-001 (identity provider) and any other decision you must make. List every missing credential/input from docs/PREFLIGHT.md and what it blocks. Ask me only about genuine blockers.
```

## PROMPT B — R0: Repair and boot
```
Execute stream R0 of docs/MASTER_PROMPT_V2.md exactly (R0.1–R0.6). Priority: the mobile bundler (A-01). Reproduce the failure first (start Expo, request the web bundle, save the 503 body), then fix it using the official Expo monorepo/Expo Router docs for the pinned SDK, then prove it: `npx expo export` for web/android/ios exit 0, Playwright loads http://localhost:8082 and sees the sign-in screen text, `npx expo-doctor` clean. Then make `make dev`, `make dev-stop`, `make verify` work from a clean clone and print the four URLs (Expo Go LAN URL, mobile web :8082, web :3000, API docs :8000/docs).
Exit gate: G-01, G-02 (exports + web), G-03. Close-out.
```

## PROMPT C — R1: Remove every fake and every removed feature
```
Execute stream R1 of docs/MASTER_PROMPT_V2.md. Delete (not hide) everything in R1.1, replace with the honest components in R1.3, add scripts/forbidden-strings.mjs to make verify (source AND built bundles), add the production-guard test and the prod-image check. Show before/after screenshots of Submit FDR, Bank Verification, Reminder Ladder, Audit Chain, Admin & Connectors and the header. Remove the L0–L3 model from UI and code and migrate data to evidence attributes (F-06) with a reversible migration.
Exit gate: G-04, G-05, G-07. Close-out.
```

## PROMPT D — R2: Authentication and all 13 roles
```
Execute stream R2 of docs/MASTER_PROMPT_V2.md using docs/AUTH_ROLES_MATRIX.md as data. Tests first: the generated role×verb×scope negative matrix, cross-tenant 404s, stale-role-after-downgrade, step-up enforcement without client cooperation, refresh-token reuse revocation, lockout, invitation single-use, SoD at API and DB, no self role-grant.
Then build backend (R2.1–R2.3), web auth UI and mobile auth UI (R2.4–R2.5), `make seed-staging` and `e2e:roles` for web and mobile (R2.6), and CI drift check between the matrix and role_permissions (R2.7). Remove the role dropdown entirely. Produce screenshots per role (landing + nav) in artifacts/roles/.
Exit gate: G-08..G-12, G-29. Close-out.
```

## PROMPT E — R3: Real data everywhere
```
Execute stream R3 of docs/MASTER_PROMPT_V2.md. Generate packages/api-client from /v1/openapi.json in CI (fail on stale). Replace every hard-coded array/number in apps/web and apps/mobile with API-backed queries and designed loading/empty/error/forbidden states (use temporary plain styling if the new design system is not built yet — the next prompt restyles). Add the no-business-literals lint. Wire the SSE client with Last-Event-ID. Start the i18n catalogue with review status.
Prove: Playwright asserts every screen issues /v1/* requests and renders data from them; kill the API and show honest "temporarily unavailable" states.
Exit gate: G-06. Close-out.
```

## PROMPT F — R4: Missing backend modules
```
Execute stream R4 of docs/MASTER_PROMPT_V2.md module by module in this order: dashboard, search+saved views, reminders+scheduler+calendar feed, reports+export jobs, audit+chain verification, users/access/invitations/recertification, help/support/rights, retention, release+policy hardening, notification additions. For each: migration (up/down), authorise() with scope + RLS, audit+outbox in the same transaction, OpenAPI, allow-list serialisers, positive and negative tests, and a short entry in docs/TRACEABILITY.md. Do the work in separate commits per module.
Exit gate: G-14..G-19 (backend part). Close-out.
```

## PROMPT G — R5: Design system and the web app
```
Execute stream R5 of docs/MASTER_PROMPT_V2.md. Look at design/reference/reference-sheet.png and design/preview.html (render both with Playwright and read them) before writing any UI. Step R5.0 FIRST: write the design-contract tests (computed-style and test-id assertions for top bar, role pill, black pill buttons, soft-red pair, 20-px cards, floating tab bar with azure icons and light-blue active capsule, grouped lists, chips/segments, sheets, Kosh empty states, tokens-only colours) and watch them fail. Then: wire design/tokens.* into Tailwind v4, add the no-raw-colour lint, self-host Inter and Plus Jakarta Sans (include licence files), build the component library with a gallery, draw the original Kosh illustrations and the wordmark. Open design/preview.html and make the real components match it. Then build the web shell and every screen in R5.5 role by role, in the order: Institution roles → Intake → Scrutiny → Finance → Supervisor → Authority → Auditor → IAM → Platform → Bank verifier portal → public receipt page.
After each role: run e2e:roles for that role, take screenshots (390/768/1280/1920 × light/dark × en/hi/ta), read them, compare with the preview, fix, then run design-reviewer. Do not move to the next role until PASS.
Exit gate: G-23, G-24 (web), G-25 (web), G-27 (web), the six PS scenarios on web. Close-out.
```

## PROMPT H — R6: Mobile app
```
Execute stream R6 of docs/MASTER_PROMPT_V2.md. Build the floating pill tab bar with expo-router/ui headless tabs (NOT native tabs; read docs/DESIGN_RESEARCH.md for why), one <Icon> wrapper over expo-symbols (name={{ios, android, web}}), the role-specific tabs from /me/navigation, and every screen with the same data/permissions as web. Android: Material 3 behaviour and Material Symbols for EVERY icon (add the lint rule and a test that enumerates icon imports); iOS: SF Symbols. Implement M-01…M-21 (no voice features). Run Maestro for the six PS scenarios and e2e:roles on Android emulator and iOS simulator when available (otherwise record blocked: <reason>). Generate docs/PARITY_MATRIX.md in CI.
Screenshots: small/large phone, tablet, 200% font scale, light/dark. design-reviewer must PASS.
Exit gate: G-02, G-13 (mobile), G-24..G-27 (mobile). Close-out.
```

## PROMPT I — R7: Realtime, push, notifications
```
Execute stream R7 of docs/MASTER_PROMPT_V2.md and MASTER_PROMPT (v1) §10. Prove with a two-browser Playwright test that user A's action appears on user B's screen within seconds; prove Last-Event-ID replay; prove the push state ladder; prove lock-screen payloads contain no sensitive canary strings; prove logout de-registers the device token. If FCM/APNs credentials are absent, prove the Not-configured UI and mark blocked in docs/PREFLIGHT.md — never fake a provider success.
Exit gate: G-20..G-22. Close-out.
```

## PROMPT J — R8: Hardening and handover
```
Execute stream R8 of docs/MASTER_PROMPT_V2.md: security checklist, headers, rate limits, upload tests, gitleaks, dependency audit, restore drill, k6 load test (record numbers, invent no SLAs), runbooks, KNOWN_LIMITATIONS.md, DEMO_SCRIPT.md (six scenarios, staging banner), README quick-start (clone → make dev → open URLs → sign in as each seeded role). Run spec-auditor across SPEC_v3 and the ten PS capabilities; write docs/FINAL_AUDIT.md listing each requirement Done / Partial / Blocked with evidence links.
Exit gate: G-28 and every remaining gate. Close-out.
```

## PROMPT K — R9: Independent final audit (fresh session, fix nothing)
```
You are an independent auditor. Do not trust any previous report. Using only the repository and a clean `make dev`: (1) check every gate G-01…G-29 in docs/MASTER_PROMPT_V2.md §2 and give PASS/FAIL with the command output or screenshot path; (2) sign in as each of the 12 human roles on web and mobile web (:8082) and confirm landing, navigation, allowed and forbidden behaviour; (3) run forbidden-strings on source and built bundles; (4) grep for raw colours, non-Material icon imports in Android code, emoji in UI; (5) open the app at 390/768/1280 px in light/dark and compare to design/preview.html; (6) check no screen shows success it did not observe; (7) verify docs/KNOWN_LIMITATIONS.md matches reality. Output a defect list ranked by severity with reproduction steps. Fix nothing.
```
