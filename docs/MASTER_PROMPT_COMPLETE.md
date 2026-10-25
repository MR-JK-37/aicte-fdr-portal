# MASTER_PROMPT_COMPLETE — AICTE Security Deposit / FDR Portal (SIH PS 26265): fix, complete, match the reference design

You are Claude Code. This single file is the complete work order. Read ALL of it before acting. The same material also exists as separate files in the repo (docs/, design/); they are identical copies and remain authoritative if you edit anything. Also read, on demand: `CLAUDE.md`, `docs/spec/SPEC_v3.md`, `docs/MASTER_PROMPT.md` (v1 module behaviour F-01…F-28, M-01…M-21), `design/preview.html` (render it with Playwright and LOOK at it), `design/reference/reference-sheet.png` (the owner's target look; style reference only — never reproduce its brand assets).

How to run: start with PART 6 prompt A (plan only), then B…K one per fresh session. Never skip an exit gate. Never claim anything you have not run. Open the app and read screenshots after every UI change.



---

# PART 1 — MASTER PROMPT V2 (work order, gates, streams)

(source: `docs/MASTER_PROMPT_V2.md`)

# MASTER_PROMPT_V2 — "Fix, complete, and make it beautiful" (AICTE Security Deposit / FDR Portal, SIH PS 26265)

You are Claude Code, working in the existing monorepo (web at :3000, FastAPI at :8000, Expo at :8082). A first build exists. A live inspection (`docs/AUDIT_REPORT.md`) found: the backend is a decent skeleton; the web app is a hard-coded mock that never calls it; the mobile app does not start; there is no real authentication or role system in either client; simulation features that were removed from scope are still in the UI. Your job is to turn it into the real product described by `docs/spec/SPEC_v3.md`, with the new design in `design/`, **without breaking what already works** and **without claiming anything you have not run**.

**Precedence.** (1) `CLAUDE.md` non-negotiables → (2) this file → (3) `docs/AUTH_ROLES_MATRIX.md` → (4) `design/DESIGN_SPEC.md` + `design/tokens.*` + `design/preview.html` (+ `docs/DESIGN_RESEARCH.md`) → (5) `docs/MASTER_PROMPT.md` (v1) for module behaviour F-01…F-28, M-01…M-21, notifications §10, AI §14, security §15, API §16 → (6) `docs/spec/SPEC_v3.md`. Where v1 §13 (dark/Liquid-Glass design) or v1 voice/simulation content conflicts with v2, **v2 wins**. If two sources of equal rank disagree, stop and ask one precise question.

---

## 0. Operating contract (read twice)

1. **Evidence or it did not happen.** A task is done only when you have run the command that proves it and pasted the summary line (pass counts, status codes, screenshot paths). Never write "should work". Never mark a task complete with a failing or skipped test you did not explain.
2. **Look at the real running app.** You have a shell and Playwright. After every UI change, start the stack (`make dev`), open the page in headless Chromium, take screenshots at 390 / 768 / 1280 px in light and dark, **read the images**, compare with `design/preview.html`, and fix differences. Check the browser console and network log: zero errors, and every number on screen traceable to an API response.
3. **Branch first, never destroy.** `git switch -c v2/fix-and-complete`. Commit in small conventional commits. Do not delete working backend code; replace it only with something tested. Never force-push, never `--no-verify`.
4. **No fabrication anywhere.** No hard-coded business data in clients, no mock fetches in e2e tests (use the real API against a test database), no placeholder success, no fake "healthy", no `setTimeout` pretending to be a network call, no random/Math-derived numbers in UI. Synthetic data exists only in `packages/fixtures` and the staging seed, behind `APP_ENV != production`, with a persistent "STAGING — SYNTHETIC DATA" banner.
5. **Verify library facts.** The inspection saw Expo SDK 58 / Metro 0.87 / pnpm workspaces. Read the official docs for each pinned version before using an API; record versions and URLs in `docs/STACK_LOCK.md`. If a package or prop does not exist, use the documented fallback and write it down.
6. **Ask only for genuine blockers** (a missing credential, a policy decision from `docs/OPEN_DECISIONS.md`). Otherwise decide, write the decision into `docs/DECISIONS.md` (ADR style, 5 lines), and continue.
7. **Work the streams in order** (R0 → R9). Do not start stream N+1 until stream N's exit gate is green. Keep `docs/PLAN.md` as a living checklist; tick items only with evidence.
8. **Task discipline:** one concern per commit; update `docs/TRACEABILITY.md`; add tests with the code (including negative/authorisation tests); regenerate the OpenAPI client; keep `make verify` green.
9. **Honest UI language.** Use only these state words for external dependencies: `Not configured`, `Temporarily unavailable`, `Pending source response`, `Provider accepted`, `Evidence received`, `Human verified`, `Bank-confirmed`, `Ledger-reconciled`, `Inconclusive`. Never show success you did not observe.

---

## 1. Defects you must fix (from the audit — each has a test that proves the fix)

| ID | Defect | Fix summary | Proof |
|---|---|---|---|
| A-01 | Mobile bundle 503: `react-native-web` unresolved; entry is `./apps/mobile/node_modules/expo/AppEntry`; Metro started at repo root | R0 §R0.3 | `expo export --platform web` and `--platform android` succeed; Playwright loads `:8082` and sees the login screen |
| A-02 | Web never calls the API | R3 | Network assertion: each screen issues ≥1 `/v1/*` request; lint forbids literal business data in `apps/web/src` |
| A-03 | No auth; client-side role dropdown with 5 fake roles | R2 | `e2e:roles` for 12 human roles; production bundle contains no role switcher |
| A-04 | "AI Voice Call", "Clock Live", "SIMULATION" badge, "Simulate Statement Ingestion", "Simulate Tamper", "Browse File (Demo FDR)" | R1 | `forbidden-strings` CI test over built bundles and source |
| A-05 | Connectors shown HEALTHY with fake latency; "Chain integrity 100% valid"; "Statutory escalation ladder" | R1/R4 | UI reads `/v1/admin/registry`, scheduler status and a real chain-verify job |
| A-06 | Release page auto-"Eligible", all green, "Sign & Issue QR Certificate" | R4 | Checklist built from policy rows; maturity alone cannot create approval; no certificate issuance |
| A-07 | L0–L3 evidence ladder | R1/R3 | Evidence shown as five separate attribute pills with source/date/reviewer |
| A-08 | Reports/exports fake | R4 | Async `export_jobs` with revalidated download |
| A-09 | Text-to-SQL tab | R1 | Removed; policy Q&A only via `/v1/ai/policy-qa` with resolvable citations |
| A-10 | Missing backend modules | R4 | Each endpoint listed in §R4 exists with tests |
| A-11…A-16 | Docs CDN, old theme, i18n status, favicon, marketing chips, hard-coded sample data | R1/R5/R8 | Checklist items G-xx below |

---

## 2. The "no mistakes" acceptance gate (all must be true before you report done)

**Boot and platform**
- G-01 `make dev` starts DB, API, web (:3000) and mobile (:8082 with LAN URL printed for Expo Go) from a clean clone; `make verify` is green.
- G-02 `http://localhost:8082` renders the app on web; `expo export` for web + Android + iOS bundles succeeds; a dev build installs on an Android emulator and an iOS simulator when available (otherwise record "blocked: <reason>").
- G-03 `http://localhost:8000/docs` is available only when `APP_ENV != production`, with assets served locally (no CDN).

**Honesty / reality**
- G-04 Production-guard: startup refuses `DEMO_MODE`, `MOCK_BANK_PROVIDER`, `SIMULATED_CLOCK`, `FAKE_PUSH_SUCCESS`; test proves it by injecting each.
- G-05 `forbidden-strings` scan over source **and** built bundles finds none of: `AI Voice`, `Voice Call`, `Clock Live`, `Simulat`, `Demo FDR`, `SIMULATION`, `Text-to-SQL`, `L0`, `L1 Only`, `Gold Standard`, `Eligible for Release` (as a literal), sample FDR numbers, role-switcher markup.
- G-06 Every number, status, date and name in both clients comes from the API; screens with no data show designed empty states; loading shows skeletons.
- G-07 No connector displays a state it did not observe; unconfigured providers show `Not configured`.

**Authentication and roles**
- G-08 Each of the 12 human roles can sign in (password + TOTP; passkey where supported), sees the landing and navigation in `AUTH_ROLES_MATRIX.md` **from `/v1/me/navigation`**, and every allowed screen loads real data.
- G-09 Each role is denied every forbidden route/API call (403/404 as specified), cross-tenant ids return 404, and a stale role after downgrade is denied on the next request.
- G-10 Step-up is enforced **server-side** for every action in AUTH §2.2(3) (test calls the API without step-up → 401/403 with `step_up_required`).
- G-11 Session management works: list, revoke one, revoke all, idle/absolute timeout, refresh rotation + reuse detection, lockout, password reset, invitation acceptance.
- G-12 SoD: same-person maker/checker is rejected at API **and** DB; no one can grant themselves a role; IAM Admin / Platform Operator cannot approve business actions.

**Functionality**
- G-13 The six PS scenarios (new FDR submission, discrepancy identification, validity tracking, approaching maturity, renewal, authorised release) pass end-to-end in Playwright on web and Maestro on mobile, using real API + DB on staging config.
- G-14 Dashboard counts equal list totals (test); export respects scope and masks identifiers; CSV injection neutralised.
- G-15 Search never returns out-of-scope rows (property test); saved views work.
- G-16 Reminder scheduler: DB-leased, heartbeat visible, idempotent per key, **no invented schedule** — with no approved schedule, admin sees the alert and the scanner records `skipped: no approved schedule`.
- G-17 Release: checklist from approved policy version; clearances separate; recommendation ≠ requester; decision needs step-up and delegation headroom; `EXECUTION_PENDING` until trusted execution evidence is recorded and independently reviewed.
- G-18 Audit: hash chain verifies via a real job; tamper test (direct DB edit in a test DB) is detected; UI shows the real result and timestamp.
- G-19 Receipts: signed PDF + QR, public verify page minimal and rate-limited; tampered PDF fails.

**Realtime and notifications**
- G-20 A change by user A appears on user B's open screen within seconds via SSE (Playwright two-context test); reconnect with `Last-Event-ID` replays missed events and re-authorises each.
- G-21 Inbox is the source of truth; push state ladder CREATED → … → ACTIONED tracked; with FCM/APNs credentials absent the UI says `Not configured` and the inbox + SSE still work; with credentials present a real test push reaches a real device (record evidence) — if no device/credentials: `blocked: <reason>`.
- G-22 Lock-screen payloads contain no sensitive values (canary-string test); logout de-registers the push token and clears caches.

**Design**
- G-23 `python3 -I design/check_tokens.py` passes; no raw colours outside tokens (lint); both themes; Reduce Motion / Transparency / Increased Contrast honoured.
- G-24 **Every screen matches the reference-derived look in `design/preview.html` and `DESIGN_SPEC.md` §5–6**: lavender canvas, white 20-px cards with soft shadow, azure duotone icons, **black pill primary**, soft-red pill destructive, floating white pill tab bar (all icons azure, active = light-blue capsule + blue bold label), top bar = wordmark + thin black progress (real profile completion) + bell + read-only role pill, hero card with ring/sparkles/peeking Kosh, grouped list cards with chevrons, black selected chips/segments, bottom sheets over a blurred scrim, Kosh empty states. The **design-contract tests** (R5.0) pass on web and mobile web; screenshots at 390/768/1280/1920 × light/dark × en/hi/ta are attached; `design-reviewer` PASS.
- G-25 Android uses **Material Symbols only** and iOS **SF Symbols only** for every icon, through one `<Icon>` wrapper over `expo-symbols` with `name={{ios, android, web}}` (lint + a test enumerates icon usage); web uses **Phosphor Duotone** only. No emoji in UI. The floating tab bar is built with `expo-router/ui` headless tabs.
- G-26 Web and mobile have identical capability (generated `docs/PARITY_MATRIX.md` has no unexplained gaps); mobile adds M-01…M-21.
- G-27 a11y: axe-core zero serious/critical; keyboard-only path for every flow; 200% font scale on mobile without clipping; Hindi/Tamil at +40% text length without clipping.

**Security**
- G-28 gitleaks clean; no secrets in repo/images; dependency audit has no high/critical; headers (CSP, HSTS in prod, frame-ancestors none, no-sniff, referrer-policy) tested; uploads pass EICAR/magic-byte/zip-bomb tests; logs scrubbed (canary test).
- G-29 RLS pool-isolation test and missing-context-zero-rows test pass.

---

## 3. Stream R0 — Inventory, repair, boot

R0.1 `git switch -c v2/fix-and-complete`. Read `CLAUDE.md`, this file, `docs/AUDIT_REPORT.md`, `docs/AUTH_ROLES_MATRIX.md`, `design/DESIGN_SPEC.md`, and the v1 sections named in the precedence list. Write `docs/PLAN.md` (≤2 pages) and `docs/DECISIONS.md`.
R0.2 **Inventory the repo** and write `docs/INVENTORY.md`: directory map, stack/versions (`docs/STACK_LOCK.md`), how each app starts, test commands and their current pass/fail, migration state, list of routes with a column "has authz / scope / RLS / idempotency / audit+outbox / tests" (fill by reading code and running tests — **do not assume**). Run the existing test suites; record failures; fix those that block you.
R0.3 **Fix the mobile bundler (A-01).** Known facts: Expo SDK 58 / Metro 0.87 / pnpm; Metro was started at the monorepo root; `react-native-web/dist/exports/AppRegistry` could not be resolved; entry was `expo/AppEntry`. Do, in order, verifying against the Expo monorepo and Expo Router docs for the pinned SDK:
  1. Start Expo **from `apps/mobile`** (script: `pnpm --filter mobile start --host lan --port 8082`). Never from the repo root.
  2. `apps/mobile/package.json`: `"main": "expo-router/entry"`; `app.json`/`app.config.ts` has `scheme`, `plugins: ["expo-router"]`, `web.bundler: "metro"`, `web.output: "single"`.
  3. Install web deps with `npx expo install react-native-web react-dom @expo/metro-runtime` inside `apps/mobile` so versions match the SDK.
  4. pnpm: ensure Metro can see hoisted deps — use the setup the Expo docs recommend for pnpm monorepos for this SDK (commonly `node-linker=hoisted` in `.npmrc`, or explicit `watchFolders`/`resolver.nodeModulesPaths` in `metro.config.js`); `npx expo-doctor` must report no errors.
  5. Prove: `npx expo export --platform web` exits 0; open `http://localhost:8082` in Playwright and assert the sign-in screen text; `npx expo export --platform android` and `--platform ios` exit 0.
  6. Make the API base URL configurable per environment (`EXPO_PUBLIC_API_URL`); on a phone `localhost` is wrong, so the LAN URL is used by default in dev; document in `README`.
R0.4 `make dev` (docker compose for Postgres/MinIO/ClamAV/Mailpit as needed + API with `--reload` + web + mobile) and `make dev-stop`; `make verify`; `make seed-staging` (R2).
R0.5 **ADR-001 identity provider:** read the API's current auth code. If it already provides argon2id passwords, TOTP, passkeys, refresh rotation, lockout and server-side sessions behind an interface, keep it; otherwise implement the missing parts or integrate Keycloak behind `IdentityProvider`. One identity system only. Record the decision.
R0.6 Spikes still needed (S-02 Material Symbols pipeline on Android; S-03 iOS SF Symbols via `expo-symbols`; S-04 FCM/APNs sandbox availability; S-05 passkeys in Expo (`react-native-passkeys` or the verified alternative) and WebAuthn on web). Write results to `docs/spikes/`.
**Exit gate R0:** G-01..G-03 true; inventory and plan written; baseline test results recorded.

## 4. Stream R1 — Purge simulation and fakes; honest states

R1.1 Delete (code, routes, assets, strings, translations, tests): AI voice/call UI and any telephony/STT/TTS code or dependencies; "Clock Live" and any simulated/time-travel control in the UI; the "SIMULATION" badge; "Simulate Statement Ingestion"; "Simulate Tamper"; "Browse File (Demo FDR)"; Text-to-SQL; the L0–L3 evidence model (replace with evidence attributes per F-06; migrate data model if it exists); hard-coded instruments/institutions/KPIs/connector latencies; marketing technology chips in the footer.
R1.2 Time travel exists **only** inside automated tests through an injectable `Clock` (prod rejects the test clock). The UI never offers it.
R1.3 Replace with honest components: `ConnectorStatus` (reads `/v1/admin/registry`; states Not configured / Configured, untested / Healthy (last real check + latency from the health-check endpoint) / Degraded / Failing), `ChainStatus` (reads the last real verification job), `ReminderScheduleBanner` (approved / unapproved example / none).
R1.4 Add `scripts/forbidden-strings.mjs` + pytest wrapper run in `make verify` over `apps/*/src`, `backend/app`, and **built** web/mobile bundles (list from G-05). Add the production-guard test (G-04). Add a CI check that production Docker images contain no `packages/fixtures` and no seed code.
**Exit gate R1:** G-04, G-05, G-07; screenshots show no removed feature.

## 5. Stream R2 — Authentication and the 13 roles (follow `docs/AUTH_ROLES_MATRIX.md` exactly)

R2.1 **Data model/migrations:** `users`, `credentials` (argon2id hash, TOTP secret encrypted, passkey credentials, recovery code hashes), `sessions` (device, ip-area, created/last-seen/expires, revoked_at, refresh family id), `role_assignments` (user, role, scope JSON, valid_from/to, ticket ref, approver), `role_permissions` (generated from the matrix; seeded by migration, **not** by fixtures), `invitations`, `login_attempts`, `step_up_events`, `delegations` (limits). RLS policies on all tenant tables; app role cannot bypass.
R2.2 **Endpoints (all under `/v1`)** with OpenAPI + tests: `POST /auth/login`, `POST /auth/mfa/verify`, `POST /auth/mfa/totp/enrol|confirm`, `POST /auth/passkeys/register/options|verify`, `POST /auth/passkeys/login/options|verify`, `POST /auth/step-up` (+ `step_up_required` problem type), `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/logout-all`, `POST /auth/password/forgot|reset|change`, `GET /auth/sessions`, `DELETE /auth/sessions/{id}`, `POST /auth/recovery-codes/regenerate`, `POST /auth/invitations/accept`, `GET /me`, `GET /me/permissions`, **`GET /me/profile-completion`** (percentage + remaining items; feeds the top-bar progress and first-run checklist), **`GET /me/navigation`** (server-built manifest: items with `key, label_key, icon_key, route, badge_source, required_permission`, plus the landing route and mobile tab subset), `GET/PATCH /me/preferences`.
R2.3 **Authorisation:** one `authorise(principal, action, resource, context)` used by every route (v1 §8.4); allow-list serialisers; RLS context set per transaction; cross-tenant → 404; step-up and SoD per matrix; delegation limits server-side; permissions evaluated per request (no role claims trusted from tokens).
R2.4 **Web auth:** `/login` (entry selector hint, e-mail + password, passkey button, forgot link, error states, lockout message), MFA challenge, MFA enrolment wizard (TOTP QR + recovery codes), step-up modal (`StepUpSheet`), reset password, accept invitation, session list in Profile → Security, idle-timeout warning, route guards that read `/me/navigation`, 401/403/404 pages. **Remove the role dropdown and any client-side role logic.**
R2.5 **Mobile auth:** the same screens natively; tokens in Keychain/Keystore; biometric re-lock after background timeout; passkeys; deep-link-safe login redirect; logout clears everything (v1 F-01 AC).
R2.6 **Staging seed & walkthrough:** `make seed-staging` per AUTH §4; `e2e:roles` for web (Playwright) and mobile (Maestro) iterating all 12 human roles; screenshots per role.
R2.7 **Generated negative matrix:** role × verb × scope tests produced from the `role_permissions` table; CI fails on drift from `AUTH_ROLES_MATRIX.md` (parse the table).
**Exit gate R2:** G-08, G-09, G-10, G-11, G-12, G-29.

## 6. Stream R3 — Contract, generated clients, real data everywhere

R3.1 Publish one OpenAPI document (`/v1/openapi.json`); generate `packages/api-client` (TypeScript types + fetch client) in CI; fail CI if the committed client is stale. Use problem+json errors with `correlation_id`; idempotency keys on safe writes; `409 STALE_VERSION` handling.
R3.2 Web: TanStack Query for server state, one `apiFetch` wrapper (cookies, CSRF header, correlation id, problem+json mapping to designed error states); mobile: same client with bearer auth. Optimistic UI only for reversible actions.
R3.3 **Delete every hard-coded array and number** in `apps/web/src` and `apps/mobile`; add the lint rule `no-business-literals` (fails on FDR-number patterns, ₹ literals outside formatters and tests, `Cr`/`Lakh` strings, bank names in arrays).
R3.4 SSE client (`/v1/stream`) with auth, `Last-Event-ID`, backoff, per-event cache invalidation, a visible "live" indicator that reflects the real connection.
R3.5 i18n: ICU catalogue (en authoritative, hi, ta), `translation_catalog_status` (`machine-draft | reviewed`), Indian digit grouping, `lang` attributes, text-expansion test.
**Exit gate R3:** G-06 and the Playwright network assertion (every screen hits `/v1/*`).

## 7. Stream R4 — Missing backend modules (each with migrations, authz, scope/RLS, audit+outbox, OpenAPI, tests)

| Module | Endpoints (minimum) | Notes / AC |
|---|---|---|
| Dashboard (F-16) | `GET /dashboard/summary` (scope-filtered counts: active, expiring by horizon, matured, renewed, released, pending verification, open observations, awaiting institution, reconciliation exceptions, release by stage, overdue + ageing buckets + evidence-attribute distribution), `GET /dashboard/my-work`, `GET /dashboard/due-soon`, `GET /dashboard/activity` | Each count carries a `drilldown` filter object; counts equal list totals (test); no single score |
| Reports & exports | `GET /reports/catalogue`, `POST /reports/{key}/runs`, `GET /export-jobs`, `GET /export-jobs/{id}`, `GET /export-jobs/{id}/download`, schedules CRUD | Async jobs; scope/reason/row-count/file-hash/expiry; permission **revalidated at download**; CSV-injection neutralised; every export audited |
| Audit (F-18) | `GET /audit/events`, `GET /audit/events/{id}`, `GET /audit/access-logs`, `GET /audit/chain/status`, `POST /audit/chain/verify` (job), `POST /audit/exports` | Signed checkpoints; verification job result persisted; Auditor read-only; sensitive reads themselves audited |
| Users & access (F-01/F-19) | `GET/POST /users`, `GET/PATCH /users/{id}`, `POST /users/{id}/unlock`, `GET/POST /invitations`, `POST /role-assignments/requests`, `POST /role-assignments/{id}/approve|reject`, `GET/POST /recertification-campaigns`, `GET/POST /institutions/{id}/users` | Maker-checker + step-up; nobody grants own role; revocation ends sessions immediately |
| Search & views (F-17) | `GET /search`, `GET/POST/PATCH/DELETE /saved-views` | FTS + `pg_trgm` on scoped fields; identifier search by blind index only; cursor pagination; timeout |
| Reminders & scheduler (F-10) | `GET /reminder-schedules`, `POST …/versions`, `POST …/approve` (maker-checker), `GET /scheduler/status`, `GET /reminders`, `GET /calendar/maturities`, `POST /calendar/feed-token`, `GET /calendar/feed.ics?token=` | DB-leased scheduler with heartbeat; idempotency key per (instrument, rule, window, recipient); **no approved schedule ⇒ alert, not invented reminders**; feed token revocable, content minimal |
| Help, support, rights (F-21/F-22) | `GET /help/articles`, `POST /support-requests`, `GET /support-requests`, `POST /rights-requests` | Correlation ID auto-attached; scope-checked attachments; due dates |
| Retention (F-22) | `GET/POST /retention/classes`, `POST /legal-holds` | No disposal until configured; held records never disposed |
| Release & policy hardening (F-12/F-13) | existing `/release-requests/*`, `/policies/*` | Checklist built from approved policy rule rows; penalty rules `BLOCKED`; no certificate issuance; approver ≠ author; execution evidence reviewed by a second person |
| Notifications (F-14) | existing + `GET /inbox?since=`, preferences, device status | Provider state honest; test push through the real pipeline labelled TEST |

**Exit gate R4:** G-14..G-19 for the backend part; OpenAPI diff reviewed; migration up/down tested.

## 8. Stream R5 — Design system and web app

R5.0 **Design-contract tests first.** Before styling anything, write Playwright (web + mobile web :8082) tests that assert the reference-derived rules from `DESIGN_SPEC.md` using computed styles and `data-testid`s: top bar has `wordmark`, `progress-mini`, `bell`, `role-pill` (role pill background = `--role-fill`, text contrast ≥4.5); primary buttons are pills with background `--ink`; destructive pair uses `--danger-container`; cards radius 20 and no 1-px border; tab bar is `position: fixed/absolute`, radius ≥ 24, floating shadow, 12-px side inset, 4–5 items, active item background = `--primary-container` and label colour = `--primary`, inactive labels `--text-1`, every tab icon colour = `--azure`; list rows 52–56 high with hairline separators and chevrons; chips/segments selected background = `--ink`; sheets have a grabber, 28-px top radius and a scrim with blur; empty states contain the Kosh SVG; no raw colours in computed styles outside the token set (collect all `color`/`background-color` values on a page and assert they are in the token palette ± opacity). These tests are the executable form of the preview.
R5.1 `packages/design-tokens` re-exports `design/tokens.ts`; web consumes `design/tokens.css` via Tailwind v4 `@theme` mapping (no raw colours elsewhere; add the `no-raw-colour` lint for CSS/TS/TSX/Kotlin/Swift). Fonts: Inter + Plus Jakarta Sans self-hosted subsets with licence files.
R5.2 Build the component library listed in `DESIGN_SPEC.md` §5 with Storybook (or an equivalent `/design` route in staging): every component in light/dark, every state, Hindi/Tamil expansion, keyboard and screen-reader behaviour. Use headless accessible primitives (e.g. Radix) styled by tokens. Icons: **Phosphor (MIT) with the `duotone` weight for nav and list icons** (azure), `regular` elsewhere, through one `<Icon name>` wrapper with a closed enum of logical keys.
R5.3 Draw the Kosh illustration set (SVG, original soft-3D shield-coin character — DESIGN_SPEC §8; start from `kosh()` in `design/build_preview.py`): poses smile, wow, calm, peek, search, document, lock, offline, error, celebrate, plus 12 avatar variants; and the `fdr·portal` wordmark (heavy lowercase with a blue ring-and-dot mark). Never reproduce the reference product's mascot, name or wordmark.
R5.4 Web shell: floating sidebar card + top bar (⌘K search, bell with live count from SSE, role pill read-only, avatar menu, language, theme) on the lavender canvas; below 768 px the sidebar is replaced by the floating pill tab bar; layout/width rules from the spec.
R5.5 **Screens** (all fed by the API; all states designed). Build per role from `AUTH_ROLES_MATRIX.md` §5 and v1 §11 items 1–20: sign-in/MFA/step-up/invitation/onboarding application · role homes · institutions · instruments list/detail (tabs: Overview with provenance pills · Versions & diff · Documents · Evidence & verification · Reconciliation · Observations · Renewal lineage · Release · Timeline · Notifications) · submission wizard · document review (viewer ↔ extracted fields) · verification workbench + bank-verifier portal · reconciliation workspace · observations inbox/detail · queues & workload · release request detail (checklist, clearances, recommendation, decision with step-up, execution) · renewals + maturity calendar + reminder schedule · reports & exports · notifications + preferences · profile & security · admin (users, roles, policy registry, connectors, templates, retention, DLQ, scheduler, feature registry) · audit workspace · help/support/rights · public receipt verification · error pages.
R5.6 Visual QA matrix and `design-reviewer` sign-off for every route (G-23, G-24, G-27). PWA install + web push only if the adapters are configured; otherwise the UI says `Not configured`.
**Exit gate R5:** design-contract tests green, web G-24 portion, G-25 (web), G-27 (web), the six PS scenarios on web.

## 9. Stream R6 — Mobile app

R6.1 Expo Router app with the **floating pill tab bar built on `expo-router/ui` headless tabs** (`Tabs`, `TabSlot`, `TabList`, `TabTrigger`, `useTabTrigger` for focused state) — not native tabs, because on iOS 26 the system draws the bar and ignores custom backgrounds, and on Android native tabs are the stock M3 bar (see `docs/DESIGN_RESEARCH.md`). 4–5 role-specific tabs from `/me/navigation`; pad every scroll view with `useFloatingTabBarHeight()`. Icons: one `<Icon>` wrapper over `expo-symbols` (`name={{ ios, android, web }}`; verify against SDK 58 docs, fallback `@expo/material-symbols`): Android = Material Symbols (FILL 1 when selected, azure), iOS = SF Symbols hierarchical, azure; the notification small icon is a Material Symbol drawable. Android keeps M3 behaviour (ripples, 48-dp targets, predictive back, edge-to-edge, Roboto Flex); iOS keeps SF Pro, large titles, sheets with detents, haptics. Native-tabs/Liquid-Glass bar only behind a default-off flag.
R6.2 Same screens, data and permissions as web (cards instead of dense tables); implement M-01…M-21 from v1 §9A (push, notification centre sync, biometric lock, secure screens, document scanner + chunked resumable upload, quick actions, widgets with counts only, deep links, QR scanner, add to calendar, local "remind me again", encrypted offline read cache, request queue with idempotency keys, adaptive layouts, device management with real test push, update gating, privacy toggles, diagnostics). **No voice/speech features.**
R6.2a **Expo Go first.** Follow `docs/EXPO_GO_VS_DEV_BUILD.md`: the app must open in Expo Go; Android remote push, passkeys and widgets are `requires: dev-build` (honest UI state, never faked). Bottom sheets = JS sheet over an `expo-blur` `BlurView` scrim (Android: `BlurTargetView` + `dimezisBlurViewSdk31Plus`; below API 31 a dimmed scrim).
R6.3 Maestro flows for the six PS scenarios and `e2e:roles` for all 12 human roles on Android emulator and iOS simulator where available; screenshots (small/large phone, tablet, 200% font scale, light/dark).
R6.4 Parity: generate `docs/PARITY_MATRIX.md` from route/screen manifests; CI fails on unexplained gaps.
**Exit gate R6:** G-02, G-13 (mobile), G-24..G-27 (mobile).

## 10. Stream R7 — Realtime, push, notifications end-to-end
Outbox consumer, recipient resolution from current scope, inbox-first persistence, versioned localised templates (reviewed-only), FCM HTTP v1 (Android), APNs token auth (iOS), Web Push (VAPID), e-mail adapter (disabled until SMTP configured), preferences, device lifecycle, DLQ + replay, funnel metrics, SSE with `Last-Event-ID` replay + per-event re-authorisation. Android remote push and passkeys need a development build (`docs/EXPO_GO_VS_DEV_BUILD.md`); in Expo Go prove inbox + SSE + local notifications. Verify on real devices when credentials exist; otherwise prove inbox + SSE + the `Not configured` UI and mark `blocked: <reason>` in `docs/PREFLIGHT.md`. **Exit gate:** G-20..G-22.

## 11. Stream R8 — Hardening, performance, docs
Security checklist (v1 §15/§17.3), headers, rate limits, upload pipeline tests, secrets scan, dependency audit, backup/restore drill, k6 load test (record, don't invent SLAs), runbooks, `docs/KNOWN_LIMITATIONS.md`, `docs/DEMO_SCRIPT.md` for the six scenarios using staging data with the banner, `README` quick-start for a new developer (clone → `make dev` → open URLs → sign in as each seeded role). **Exit gate:** G-28, G-29 and all remaining gates.

## 12. Stream R9 — Independent final audit (fresh session, separate prompt in `PHASED_PROMPTS_V2.md`)

---

## 13. Anti-patterns (each one has burned a build; do not repeat)
- Hiding a problem with CSS or a feature flag instead of removing the fake. Renaming "Simulate" to "Test". Leaving dead routes that still return fake data.
- Catching exceptions to show a success toast. `setTimeout` as a network stub. Mocking `fetch` in e2e.
- Putting the role in `localStorage`/JWT claims and trusting it. Hiding buttons as the only authorisation.
- A "green" badge for anything not backed by a specific evidence record. Merging evidence attributes into a score.
- Hex colours or magic numbers in components. A second icon set on Android. Emoji icons. Using native tabs and then wondering why the floating pill cannot be styled. Using `primary` for icons or `azure` for text (contrast). Redrawing the reference product's mascot or copying its wordmark instead of using Kosh and `fdr·portal`.
- Starting Metro/Expo from the wrong directory; installing React Native packages with `npm install` instead of `npx expo install`.
- Declaring done after unit tests only. Declaring done without opening the app and reading the screenshots.

## 14. Reporting (at the end of each stream and at the end of R8)
`docs/phase-reports/R<n>.md`: what changed (files/modules), commands run with result summaries, screenshots/paths, gates now true (G-xx), gates still false with reason, defects found/fixed, new risks, open decisions touched. Update `docs/TRACEABILITY.md`. End with one line: `STREAM R<n>: PASS` or `STREAM R<n>: BLOCKED — <reason>`.



---

# PART 2 — AUTHENTICATION, ROLES, NAVIGATION (build data)

(source: `docs/AUTH_ROLES_MATRIX.md`)

# AUTH_ROLES_MATRIX.md — authentication, roles, landing screens, navigation

This file is **data for the build**: Claude Code turns it into `role_permissions`, the navigation manifest (`GET /v1/me/navigation`), route guards, seeds for staging, and the generated negative-test matrix. If it disagrees with `docs/spec/SPEC_v3.md` §5, SPEC wins and this file is corrected. Session numbers below are safe defaults pending decision D-08 (AICTE identity/security policy); they are config, never constants.

## 1. The 13 roles (+ public)

| # | Key | Role | Side | Scope attribute | MFA | Landing (web / mobile) | Mobile tabs (4–5) | Web sidebar |
|---|---|---|---|---|---|---|---|---|
| 1 | `INST_ORG_ADMIN` | Institution organisation administrator | Institution | own `institution_id` | Required | Institution home | Home · Deposits · Inbox · Profile | Home, Deposits, Documents, Observations, Renewals & maturity, Releases, Users, Reports, Help |
| 2 | `INST_SUBMITTER` | Institution submitter / compliance officer | Institution | own institution (+ assigned programmes) | Required | Institution home | Home · Deposits · Inbox · Profile | Home, Deposits, Documents, Observations, Renewals & maturity, Releases, Help |
| 3 | `INST_VIEWER` | Institution viewer | Institution | own institution, read-only | Required | Institution home (read-only) | Home · Deposits · Inbox · Profile | Home, Deposits, Documents, Maturity calendar, Help |
| 4 | `INTAKE_OFFICER` | Intake / registry officer | AICTE | region(s) or all, per assignment | Required | Intake queue | Home · Queue · Inbox · More | Home, Intake queue, Onboarding requests, Institutions, Instruments, Search, Reports |
| 5 | `SCRUTINY_OFFICER` | Scrutiny officer | AICTE | assigned cases / region | Required | Scrutiny queue | Home · Cases · Inbox · More | Home, My queue, Cases, Document review, Observations, Search, Reports |
| 6 | `FINANCE_VERIFIER` | Finance / verification officer | AICTE | region or all, per assignment | Required | Verification workbench | Home · Verify · Inbox · More | Home, Verification requests, Statements & reconciliation, Exceptions, Release execution, Reports |
| 7 | `REGIONAL_SUPERVISOR` | Regional supervisor / bureau reviewer | AICTE | region | Required | Workload board | Home · Cases · Inbox · More | Home, Workload board, Cases, Releases (recommend), Reports, Reminder schedule |
| 8 | `COMPETENT_AUTHORITY` | Competent authority / release approver | AICTE | delegation limits (amount, region, programme) | Required + **step-up on every decision** | Decisions pending | Home · Decisions · Inbox · More | Home, Decisions, Release requests, Reports |
| 9 | `AUDITOR` | Audit / compliance reviewer | AICTE | read-only, all | Required | Audit workspace | Home · Audit · Inbox · More | Home, Audit timeline, Access logs, Chain verification, Policy versions, Control-evidence export |
| 10 | `IAM_ADMIN` | Identity / access administrator | AICTE | users and role assignments (no case data) | Required + step-up | Access admin | Home · Access · Inbox · More | Home, Users, Role assignments, Recertification, Sessions, Invitations |
| 11 | `PLATFORM_OPERATOR` | Platform / security operator | AICTE | system only (no case content by default) | Required + step-up | System health | Home · System · Inbox · More | Home, System health, Connectors, Scheduler, Dead-letter queue, Feature registry, Policy registry (read) |
| 12 | `INTEGRATION_SERVICE` | Integration service identity | Machine | specific connector scope | mTLS / signed client credentials (no UI) | — | — | — |
| 13 | `BANK_VERIFIER` | Participating bank verifier (conditional; disabled until onboarding approved) | External | own bank + assigned requests only | Required | Assigned requests | Requests · Inbox · Profile | Assigned requests, Responses, Help (isolated minimal UI) |
| — | Public | Unauthenticated | — | none | — | Public receipt verification only | — | — |

`Policy registry` editing (draft→review→approved) is a separate permission `manage_policy` granted to a policy-owner assignment (maker ≠ approver), **not** to Platform Operator by default.

## 2. Authentication (all roles)

### 2.1 Sign-in methods
- Primary: e-mail/username + password (argon2id; breached-password check offline list; min length 12; no composition rules) **or** passkey (WebAuthn, discoverable credential). Second factor: TOTP or passkey. Recovery codes (10, single-use, hashed). SMS OTP is **not** a factor.
- Identity provider: ADR-001 in Phase R0. Default is "use the identity module already in the API **if** it meets §2 fully; otherwise Keycloak (OIDC + PKCE) behind the same `IdentityProvider` interface". Never ship two live identity systems. Never invent an AICTE SSO; Parichay/NIC SSO is an adapter slot only (D-08).
- Web: API-issued session cookie (`__Host-` prefix, HttpOnly, Secure, SameSite=Strict) + CSRF protection (Origin check + double-submit token). No tokens in `localStorage`.
- Mobile: system-browser/native auth with PKCE or native passkey flow; access token (≤15 min) in memory, rotating refresh token in Keychain / Android Keystore bound to the device record; biometric unlock is a local convenience after a server session, never proof of role.

### 2.2 Flows to build (web **and** mobile, same screens)
1. **Sign in** (`/login`): entry selector Institution / AICTE staff / Bank is only a hint for copy and passkey preference; **the role comes from the account, never from the selector**. Wrong portal → same generic failure message.
2. **MFA challenge** and **MFA enrolment** (first login is blocked from everything else until enrolled for roles marked Required): TOTP QR + manual key + recovery codes shown once; passkey registration.
3. **Step-up** modal/sheet (fresh factor ≤5 min) before: approve/reject/defer release; record execution evidence; forfeit; change policy status; grant/revoke role; change connector state; bulk un-mask identifiers; break-glass; export of unmasked data. The server demands it; the client prompt is a convenience.
4. **Forgot / reset password** (single-use 30-min token, rate-limited, no account enumeration, resets sessions, requires MFA afterwards).
5. **Invitation acceptance** (single-use, expiry 72 h, bound to one institution/role; sets password + MFA).
6. **Institution onboarding application** (public form → documents → Intake officer verifies authority → account activated). E-mail verification alone never grants authority.
7. **Session & device management** (Profile → Security): list with device, IP area, last active; revoke one / all; "Sign out everywhere".
8. **Lockout and throttling**: progressive delay per account+IP, lock after 10 failures for 15 min (IAM Admin can unlock); suspicious-login notification (new device/country).
9. **Idle and absolute timeouts** (defaults): staff 15 min idle / 8 h absolute; institution 30 min idle / 12 h absolute; bank verifier 15 min / 8 h; mobile refresh up to 30 days with device binding, but sensitive screens re-lock after 2 min in background (biometric). Session-expiry warning 60 s before.
10. **Role change / revocation takes effect on the next request** (no cached role in tokens; permissions fetched per request or version-checked). Assignment end revokes sessions of that role immediately.
11. **Logout**: server-side revoke + clear client state; mobile also deletes push token registration, offline cache and scheduled local notifications.

### 2.3 Hard rules
- No client-side role switcher, no role in `localStorage`, no `?role=` parameter, no UI hiding as the only control. The web build must not contain a "switch role" control in production; in staging, switching means **signing in as a different seeded user**.
- Every endpoint: authenticate → action permission → scope → resource state → delegation/SoD → field visibility (SPEC §4.2, MASTER_PROMPT §8.4). Cross-tenant ids return 404.
- Navigation and screen capabilities come from the server: `GET /v1/me` (identity, role assignments, scope summary, assurance level) + `GET /v1/me/permissions` (verbs per scope) + `GET /v1/me/navigation` (the sidebar/tab manifest for this user) + `GET /v1/me/profile-completion` (server-computed percentage and the list of remaining items: name, designation, verified mobile, language, MFA enrolled, optional passkey, notification permission on mobile; drives the top-bar progress and the first-run checklist). The clients render from these; role names are never hard-coded in UI logic except for copy.
- Separation of duties enforced in DB + service: submitter ≠ intake ≠ recommender ≠ evidence reviewer ≠ approver ≠ execution recorder ≠ execution reviewer on the same release; no self-approval; no granting yourself a role; Platform Operator and IAM Admin cannot perform business approvals.

## 3. Permission verbs per role (✓ allowed, ◐ scoped/conditional, — denied) — encode as data
Verbs: view, create_draft, edit_draft, submit, upload_evidence, download_evidence, raise_observation, respond_observation, assign_case, recommend, verify_bank_evidence, reconcile_statement, resolve_exception, request_release, approve_release, execute_release_record, export_report, manage_institution_users, manage_roles, manage_policy, configure_integrations, view_audit, administer_platform, view_unmasked_identifiers, manage_templates, break_glass.

| Verb | 1 Org admin | 2 Submitter | 3 Viewer | 4 Intake | 5 Scrutiny | 6 Finance | 7 Supervisor | 8 Authority | 9 Auditor | 10 IAM | 11 Platform | 13 Bank |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| view | ◐own | ◐own | ◐own | ◐ | ◐ | ◐ | ◐region | ◐ | ✓ro | users only | system only | ◐assigned |
| create_draft / edit_draft / submit | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — |
| upload_evidence | ✓ | ✓ | — | ◐ | ◐ | ◐ | — | — | — | — | — | ◐response |
| download_evidence | ◐own | ◐own | ◐own | ◐ | ◐ | ◐ | ◐ | ◐ | ◐logged | — | — | ◐assigned |
| raise_observation | — | — | — | ◐ | ✓ | ◐ | ✓ | — | — | — | — | — |
| respond_observation | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — |
| assign_case | — | — | — | ✓ | — | — | ✓ | — | — | — | — | — |
| recommend | — | — | — | — | ✓ | — | ✓(≠requester) | — | — | — | — | — |
| verify_bank_evidence | — | — | — | — | — | ✓(reviewer ≠ requester) | — | — | — | — | — | — |
| reconcile_statement / resolve_exception | — | — | — | — | — | ✓ | ◐review | — | — | — | — | — |
| request_release | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — |
| approve_release | — | — | — | — | — | — | — | ✓ step-up + delegation | — | — | — | — |
| execute_release_record | — | — | — | — | — | ✓ + second-person review | — | — | — | — | — | — |
| export_report | ◐own | ◐own | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — |
| manage_institution_users | ✓own | — | — | ✓onboarding | — | — | — | — | — | — | — | — |
| manage_roles | — | — | — | — | — | — | — | — | — | ✓ maker-checker + step-up | — | — |
| manage_policy | — | — | — | — | — | — | ◐author | ◐approver | — | — | — | — |
| configure_integrations / administer_platform | — | — | — | — | — | — | — | — | — | — | ✓ + step-up, second approver for prod-enable | — |
| view_audit | — | — | — | — | — | — | ◐region | — | ✓ | ◐access logs | ◐system | — |
| view_unmasked_identifiers | ◐own | ◐own | — | ◐ | ◐ | ✓ | ◐ | ◐ | ◐logged | — | — | ◐assigned |
| break_glass | — | — | — | — | — | — | — | — | — | request | request | — |

The authoritative cell values come from SPEC §5; the build generates the test matrix from the table in the database, so any drift fails CI.

## 4. Staging users and the role walkthrough (how "all roles work" is proven)
- `make seed-staging` (refuses to run when `APP_ENV=production`) creates, for two synthetic tenants (Institution A, Institution B) and one synthetic bank, **one user per role** with a random password and a pre-enrolled TOTP secret written to `./.local/staging-users.json` (gitignored, never printed to logs). Persistent banner "STAGING — SYNTHETIC DATA". Production images contain neither the seed code nor the fixtures (CI inspects the image).
- `pnpm --filter web e2e:roles` and `pnpm --filter mobile e2e:roles` (Playwright / Maestro) for **each of the 12 human roles**: sign in with password + TOTP → assert landing screen and the exact nav manifest → open every allowed nav item (no 4xx/5xx, no console errors, data is from the API) → attempt every forbidden route and API call (expect 403/404 and the forbidden screen) → try cross-tenant ids → sign out → back button shows login. Screenshots to `artifacts/roles/<role>/<surface>/<route>.png`.
- Pool-isolation and stale-role tests from MASTER_PROMPT §8.5 / F-01 remain mandatory.

## 5. Role home screens (what each landing shows — all from the API)
1–3 Institution: greeting hero card (real counts), "Needs attention" (open observations, release requests awaiting documents), due-soon maturities, quick actions (viewer: none), onboarding completion bar **only while onboarding is incomplete**.
4 Intake: queue with ageing, onboarding requests, duplicates/merge review.
5 Scrutiny: my queue, observations awaiting institution, extraction reviews, due today.
6 Finance: verification requests awaiting bank, statement batches, reconciliation exceptions, executions to record / review.
7 Supervisor: workload per officer, SLA ageing (no invented targets before D-13), release requests awaiting recommendation, reminder coverage.
8 Authority: decisions pending with checklist status and delegation headroom; step-up on action.
9 Auditor: chain-verification status, recent sensitive reads, export log, policy-version viewer.
10 IAM: pending role requests (maker-checker), recertification campaign, locked accounts, invitations.
11 Platform: connector states ("Not configured" is a normal state), scheduler heartbeat, DLQ depth, notification funnel, build/version.
13 Bank: assigned requests, due dates, response upload; nothing else.



---

# PART 3 — DESIGN SPEC (reference-matched 'Lavender Ledger')

(source: `design/DESIGN_SPEC.md`)

# DESIGN_SPEC.md — "Lavender Ledger" v2.1 (reference-matched) — web + iOS + Android

Supersedes the v1 dark/Liquid-Glass spec (archived in `design/archive-v1-dark/`). Source of truth for colour: `tokens.ts` → generated `tokens.css`, verified by `python3 -I design/check_tokens.py` (192 contrast checks). The visual contract is `design/preview.html` (regenerate with `python3 -I design/build_preview.py`). **If code and preview differ, fix the code.** Research notes and sources: `docs/DESIGN_RESEARCH.md`.

## 1. Intent: match the reference, adapted to this product
The owner supplied a reference sheet (9 mobile screens of a light-lavender consumer app). The goal is that every screen of this product *looks and behaves the same way*: same palette character, same card/list/button/tab-bar/sheet language, same proportions, same hierarchy, same friendliness. What changes is only what must change:
- Own name, wordmark, mascot and copy (the reference product's brand assets are not reproduced). The mascot is an original character, "Kosh", drawn in the same soft-3D, glossy, friendly style (see §8).
- Icons follow platform rules (Android Material Symbols, iOS SF Symbols, web Phosphor Duotone) but are tinted and weighted to give the same blue duotone look.
- Accessibility: the reference's pale blues were measured and nudged where needed to reach WCAG AA (§2).
- Every number and status is real (from the API), including the top-bar progress slot (§5).

## 2. Colour (measured from the reference, then AA-corrected)
Pixel-sampled reference values → our tokens: outer backdrop `#dce4fc` → `canvasDeep #dde5fb`; app background `#f4f4fc` → `canvas #f4f5fd`; cards `#fcfcfc–#fdfdff` → `surface #ffffff`; field/textarea `#ebeef7` → `field #eceff8`; progress track `#e3e8fb` → `fieldStrong #e1e6f8`; black buttons `#181818–#272727` → `ink #1a1a1e`; soft-red pill bg `#fce6e8` → `dangerContainer #fde4e6`; icon/label blue `#3b78d8` → `azure #3b78d8` (non-text); "Pro" pill periwinkle `#7393e8` → `roleFill #4570da` (darkened so white text passes 4.5:1); hero banner `#c4d3f2 → #f6f5fd` → `heroFrom #c9d7f7 → heroTo #f5f6fe`.

| Token | Light | Dark | Use |
|---|---|---|---|
| canvas / canvasDeep | `#f4f5fd` / `#dde5fb` | `#0c0e1b` / `#080a14` | App background / page backdrop on wide screens |
| surface / surfaceMuted | `#ffffff` / `#f8f9fe` | `#151833` / `#1b1f3d` | Cards, sheets, tab bar / inner wells |
| field / fieldStrong | `#eceff8` / `#e1e6f8` | `#212649` / `#2a305a` | Inputs, textarea, search, segmented track / progress track |
| azure | `#3b78d8` | `#7aa5ff` | **Icons, toggle-on, progress fill** (≥3:1, non-text only) |
| primary | `#2d63cf` | `#8fb0ff` | Blue **text**: active tab label, links (5.53:1 on white, 4.72:1 on the capsule) |
| primaryContainer | `#e6edff` | `#1e2d75` | Active tab capsule, selected wash |
| roleFill / onRoleFill | `#4570da` / `#ffffff` | `#8fb0ff` / `#0a1a5e` | Role pill (the reference's "Pro" pill) |
| ink / onInk | `#1a1a1e` / `#ffffff` | `#f3f4fb` / `#0c0e1b` | **Black pill primary buttons**, selected chips and segments, thin progress line |
| dangerContainer / onDangerContainer | `#fde4e6` / `#b0303f` | `#5a1428` / `#ffd9e0` | Soft-red pill ("Reject", "Sign out") |
| text1 / text2 / text3 | `#14141a / #474b62 / #656981` | `#f3f4fb / #bdc1d8 / #9a9fba` | All ≥4.5:1 on canvas, surface, muted, field |
| outline / hairline | `#80859f` / `#e6e9f6` | `#7f85a8` / `#2b3058` | Control borders (≥3:1) / dividers (decorative) |
| ok · warn · info · error · pending · neutral (+Container/on…) | see `tokens.ts` | see `tokens.ts` | Status pills (icon + label + tint, never colour alone) |

Rules: (1) one black-pill primary action per screen; blue-filled buttons are rare secondary emphasis; (2) no hard card borders — soft shadow + whitespace; (3) icon blue is `azure`, blue text is `primary` — never the other way round; (4) gradients only on the hero card, the progress fill and illustrations; (5) no raw hex outside `tokens.*` (lint `no-raw-colour`); (6) evidence attributes are separate pills: Declared (neutral), Extracted (pending tint), Bank-confirmed (ok + check), Ledger-reconciled (info + link), Inconclusive/Rejected (warn/error).

## 3. Typography
Reference: very bold, geometric, tight headings; small quiet section labels; bold list-row titles.
- Web: display/headings/wordmark **Plus Jakarta Sans 800** (OFL, self-hosted subset); body **Inter 500**; Noto Sans Devanagari/Tamil fallbacks. Tabular numerals for money/dates.
- iOS: SF Pro (system) with heavy weights for titles (Large Title 34/800, Title 22/700), 17/600 row titles, 12/600 section labels.
- Android: Roboto Flex via the M3 scale, titles at weight 700–800, honouring font scale to 200%.
- Scale (web, `typeWeb`): Hero greeting 31–36/34–42 ·800 · Screen title 28/32 ·800 · Section title 20/26 ·800 · Row title 15–16/20 ·700 · Body 16/24 ·500 · Footnote 13/18 · Section label 12/16 ·700 (text3, sentence case).
- Amounts Indian grouping (`₹ 35,00,000`); dates `24 Oct 2026`; identifiers monospace and masked (`XXXX 4417`).

## 4. Shape, space, elevation (measured: phone width 210 px in the sheet ≈ 390 pt)
Cards radius 20; chips/buttons/inputs-in-cards pill (button height 48 — measured: 26 px on a 211-px-wide phone ≈ 48 pt; compact 40); fields in cards radius 14; sheets top radius 28; tab bar radius 28 with an inner capsule radius 22; avatar circle. Screen gutter 12–16; card padding 14–16; list rows 52–56 high with a hairline between rows. Shadows `shadow.card`, `shadow.floating`, `shadow.sheet` (soft, bluish, low contrast). Backdrop behind a sheet: `scrim` at 30–40% + blur 6 px.

## 5. Components (the reference's vocabulary; build once per platform with identical names)
1. **TopBar** (every main screen): wordmark left · thin black **ProgressMini** (56 px line + `NN%`) · bell (filled, black; live unread dot) · **RolePill** (periwinkle-blue filled, white bold text, shows the signed-in role, read-only). The progress slot shows **profile completion computed by the server** (`GET /v1/me/profile-completion`: name, designation, verified mobile, language, MFA enrolled, optional passkey, notification permission on mobile). It is real data; at 100% it shows a check instead of the number. Web: same bar inside the top bar.
2. **HeroCard** (role home only): gradient `heroFrom → heroTo`, info chip top-left (`Region: South`), round black edit button top-right (opens Profile), a big ring + sparkles behind **Kosh peeking over the bottom edge**, two-line bold greeting bottom-left, one line of real status.
3. **GroupedList**: section label (12/700 text3) + white card of rows: leading duotone icon in `azure` (22–24), bold title, optional small subtitle, optional trailing value, chevron. Two or three groups per screen ("Needs attention", "Main", "Policies and terms").
4. **FloatingTabBar**: white pill (radius 28, floating shadow, 12 px side inset, 64 high) with 4 equal tabs; **all icons are azure duotone; inactive labels are text1 bold 11; the active tab gets a light-blue capsule (`primaryContainer`) and a `primary` bold label**. Home indicator sits below. Role-specific tabs from `GET /me/navigation`.
5. **Buttons**: black pill (primary), soft-blue pill, **soft-red pill** (destructive), full-width in cards and sheets; side-by-side pair "black + soft-red" for binary decisions (Return/Reject).
6. **Chips/Segmented**: filter chips (selected = black pill, others white) and segmented control (track `field`, selected = black pill) — e.g. All · Reminders · Observations · Decisions; avatar-picker tabs Name · Shape · Mood · Colour.
7. **Cards with inputs**: grey `field` inputs inside white cards, a `0/500` counter on textareas, select rows with trailing icon, toggle row (azure track, white knob).
8. **ProfileCard**: big circular avatar (initials; photo only if the user uploads one) with a small round azure **edit badge**; region label top-left; pencil top-right.
9. **CompletionCard**: `fieldStrong` card with one sentence, a gradient azure progress bar and `NN%`.
10. **BottomSheet**: grabber, rounded top 28, Kosh illustration + one sentence + black pill; blurred, dimmed backdrop. Desktop: centred modal. Mobile implementation: a JS sheet (Reanimated + Gesture Handler) over an `expo-blur` `BlurView` scrim, because `@expo/ui`'s BottomSheet is a native modal that cannot blur the app behind it and ignores custom backdrops (verified in SDK 58 docs). On Android `BlurView` needs a `BlurTargetView` around the app root and `blurMethod="dimezisBlurViewSdk31Plus"`; below Android 12 fall back to a plain dimmed scrim. `@expo/ui` BottomSheet remains the fallback for simple, non-blurred sheets.
11. **EmptyState**: Kosh in a calm pose, bold one-liner, one faint explanatory sentence; no action unless there is a real one.
12. **ListPerson/Institution row**: avatar (initials), bold name, small grey sub-line, chevron.
13. Web additions in the same language: floating **sidebar card** (pill nav items, same capsule active state), hero banner, KPI cards (value is `—` until loaded), tables inside white cards with `primarySoft` row hover, evidence legend card.
14. Also: `DiffView`, `Timeline`, `ProvenanceDrawer`, `StepUpSheet`, `DataTable` → `CaseCard` on phones, `Toast`/`Banner`, `Skeleton`. Mandatory states for every data view: loading, empty, error (with correlation ID), forbidden, offline/unavailable, stale-version conflict.

## 6. Screen-by-screen mapping from the reference (build these exactly)
| Reference screen | This product | Notes |
|---|---|---|
| Mood picker sheet (tabs + 4×3 tile grid + black Save) | **Profile → Choose your avatar** (tabs Name · Shape · Mood · Colour; 12 Kosh avatar tiles; Save) | Optional personalisation; initials remain the default; no personal photo required |
| Home (hero "Hello, Ivan", "Best" and "Main" lists, tab bar) | **Role home**: hero greeting + real status; "Needs attention" list; "Main" list of role actions | Lists come from the API (observations, due soon, queues) |
| Profile (avatar card, toggle, Main list, Policies list) | **Profile**: avatar card with region, toggle ("Show my name to institutions" or role-relevant), Main (Two-step verification, Passkeys, Devices and sessions, Language, Appearance), Policies and terms | Same structure |
| Chat request (header, bubble, textarea + black Send, black + soft-red pair) | **Observation reply** (institution) and **Release decision** (authority): header card, message bubble, reason textarea with counter, black primary, black + soft-red pair (Return / Reject) | Step-up sheet before approval |
| Blurred background + bottom sheet with mascot + black button | **Ask the handbook** sheet (policy Q&A with clause citation), also used for onboarding tips and step-up | AI is bounded: always cites a stored clause or says it cannot find one |
| Notifications empty state with chips | **Notifications** (All · Reminders · Observations · Decisions) with Kosh empty state | Real inbox |
| People (search card + available profiles list) | **Institutions / Users directory** (Intake, IAM roles) | Scope-filtered |
| Profile completion (avatar with edit badge, progress card 56%, grey fields, select row, black Save) | **Complete your profile** (also the first-run checklist) | Drives the top-bar progress |
| Tab bar variants | The four-tab bar per role (see `docs/AUTH_ROLES_MATRIX.md`) | |
| (none) | Sign-in, MFA, step-up, errors, reports, audit, admin | Same components and spacing |

## 7. Icons
- One logical key set (reuse the table in `design/archive-v1-dark/DESIGN_SPEC_v1_dark.md` §8) and one `<Icon name>` wrapper per platform.
- **Android: Material Symbols only.** With the pinned SDK 58, `expo-symbols` renders Material Symbols on Android (`SymbolView name={{ ios, android, web }}`; weights via `expo-symbols/androidWeights/*`); alternative `@expo/material-symbols` (+ `@expo/ui` `Icon`). Outlined, weight 500 for list icons, FILL 1 on the selected tab, tinted `azure`. Verify props against the pinned docs (spike S-02) and record in `STACK_LOCK.md`. Notification small icon is a Material Symbol exported as a monochrome drawable.
- **iOS: SF Symbols only**, `type="hierarchical"` (gives the two-tone depth seen in the reference), tint `azure`, weight semibold.
- **Web: Phosphor Icons (MIT), `duotone` weight** for nav and list icons (gives the reference's two-tone look), `regular` elsewhere; one wrapper with a closed enum. No other set.
- No emoji. No raster icons. The preview's hand-drawn duotone icons are placeholders for the real sets.

## 8. Mascot "Kosh" and illustration (original, soft-3D)
Style to match the reference: glossy soft-3D render feel, rounded, friendly, one hero character with a few expressive poses, peeking over card edges, sitting in rings with sparkles.
Kosh: a blue shield-coin with a white rounded face plate, small oval dark eyes with a highlight, rosy cheeks and a smile; two little blue hands for the "peeking" pose. Gradients `#8fb4ff → #3b78d8 → #2556b8`, soft top-left highlight, rim line, soft ground shadow. Poses (SVG for web, react-native-svg for mobile): `smile`, `wow` (sheet), `calm` (empty), `peek` (hero), `search`, `document`, `lock`, `offline`, `error`, `celebrate`; plus 12 avatar variants (pose × tint). Reference drawing is in `design/build_preview.py` (`kosh()`).
Do not reproduce the reference product's character (large round eyes with brows, fluffy fur, black or blue creature), its logo or wordmark. `design-reviewer` fails any resemblance. Kosh appears on: sign-in, role-home hero, empty states, sheets, onboarding, error pages — never on dense data screens.

## 9. Navigation
- Phone (iOS, Android, web <768): `FloatingTabBar` as above. **Implementation: `expo-router/ui` headless `Tabs / TabSlot / TabList / TabTrigger`** (Expo's native tabs cannot be restyled this way: on iOS 26 the system draws the bar and ignores `backgroundColor`; on Android they render the standard M3 NavigationBar). Content gets bottom padding equal to bar height + inset. Android keeps M3 behaviour (ripple/state layers, 48 dp targets, predictive back); iOS keeps haptics and swipe-back.
- Web ≥768: floating sidebar card + top bar with search (⌘K), progress, bell, role pill, avatar. Max content width 1200.
- The role pill is read-only and comes from the session; there is no role switcher anywhere.
- Optional enhancement (default off): iOS 26 Liquid Glass tab bar via native tabs, if the owner prefers system look over the reference look.

## 10. Motion and feedback
Spring-like 160–320 ms; tab change cross-fade; sheet slides up with scrim fade; button press scale .98 + light haptic (iOS) / ripple (Android); progress fill animates once; Kosh may blink once on empty states (respect Reduce Motion). No looping decoration.

## 11. Content design
Short, warm but precise sentences ("Nothing here yet", "Reminders, observations and decisions will appear here as soon as they happen."). Sentence-case labels. Never claim verification not evidenced. Errors: what happened, what is safe, what to do, correlation ID. Hindi/Tamil +40% length without clipping.

## 12. Accessibility and QA gates (blocking)
WCAG 2.1 AA (2.2 target); visible 3 px focus ring; screen-reader names include state; Dynamic type/font scale 200%; Reduce Motion / Transparency / Increased Contrast. Gates: `check_tokens.py` passes · no raw colours (lint) · screenshots 390/768/1280/1920 × light/dark × en/hi/ta compared with `preview.html` · device screenshots (small/large iPhone, iPad, Pixel, tablet, 200% font) · axe zero serious/critical · `design-reviewer` PASS for every screen · icon-source lint (Android Material Symbols only; iOS SF Symbols only; web Phosphor only).



---

# PART 4 — DESIGN TOKENS (tokens.ts — source of truth for colour, shape, type)

(source: `design/tokens.ts`)

```typescript
/**
 * tokens.ts — AICTE FDR Portal design tokens v2 ("Lavender Ledger").
 * Shared by web (TS) and React Native (iOS + Android). Mirrors tokens.css.
 * `design/check_tokens.py` verifies parity and WCAG contrast in CI. Do not hand-edit one file without the other.
 *
 * Look: light lavender canvas · white rounded cards with soft shadow · azure/blue accent · black pill primary
 * buttons · soft-red pill for destructive actions · floating pill tab bar with a light-blue active capsule.
 * Light is the hero theme; dark is a full, tested counterpart (follows the system, user-overridable).
 */

export const brand = {
  azure: '#3b78d8',
  ink: '#1a1a1e',
  lavender: '#f4f5fd',
} as const;

export const light = {
  canvasDeep: '#dde5fb', // page backdrop behind the app frame on wide web screens
  canvas: '#f4f5fd', // app background
  surface: '#ffffff', // cards, sheets, floating bars
  surfaceMuted: '#f8f9fe', // grouped-list inner wells, table zebra, quote boxes
  field: '#eceff8', // input / search / segmented-track fill
  fieldStrong: '#e1e6f8', // pressed field, progress track
  hairline: '#e6e9f6', // dividers only (decorative)
  outline: '#80859f', // control borders, unchecked toggles (>= 3:1)
  text1: '#14141a',
  text2: '#474b62',
  text3: '#656981',
  textDisabled: '#a5a9bf', // decorative / disabled only
  primary: '#2d63cf', // blue text: links, active tab label (icons use azure)
  onPrimary: '#ffffff',
  primaryContainer: '#e6edff', // active tab capsule, selected chip, info wash
  onPrimaryContainer: '#163a8f',
  primarySoft: '#eff3ff', // selected-row wash
  ink: '#1a1a1e', // black pill buttons
  onInk: '#ffffff',
  danger: '#c0183f', // filled destructive
  onDanger: '#ffffff',
  dangerContainer: '#fde4e6', // soft red pill ("Block", "Reject")
  onDangerContainer: '#b0303f',
  ok: '#0b7a4b', okContainer: '#d5f5e5', onOkContainer: '#064a2d',
  warn: '#8f5a00', warnContainer: '#ffebc2', onWarnContainer: '#5c3a00',
  info: '#2d63cf', infoContainer: '#e6edff', onInfoContainer: '#163a8f',
  error: '#c0183f', errorContainer: '#ffdce2', onErrorContainer: '#8a0f2d',
  pending: '#5b3fb0', pendingContainer: '#e7e0ff', onPendingContainer: '#33207a',
  neutral: '#555b70', neutralContainer: '#e8eaf3', onNeutralContainer: '#333749',
  focus: '#2d63cf',
  scrim: '#0f1230',
  azure: '#3b78d8',
  roleFill: '#4570da',
  onRoleFill: '#ffffff',
  heroFrom: '#c9d7f7',
  heroTo: '#f5f6fe',
} as const;

export const dark = {
  canvasDeep: '#080a14',
  canvas: '#0c0e1b',
  surface: '#151833',
  surfaceMuted: '#1b1f3d',
  field: '#212649',
  fieldStrong: '#2a305a',
  hairline: '#2b3058',
  outline: '#7f85a8',
  text1: '#f3f4fb',
  text2: '#bdc1d8',
  text3: '#9a9fba',
  textDisabled: '#5d6283',
  primary: '#8fb0ff',
  onPrimary: '#0a1a5e',
  primaryContainer: '#1e2d75',
  onPrimaryContainer: '#dce4ff',
  primarySoft: '#1a2352',
  ink: '#f3f4fb', // inverted pill in dark
  onInk: '#0c0e1b',
  danger: '#ff7a93',
  onDanger: '#4a0617',
  dangerContainer: '#5a1428',
  onDangerContainer: '#ffd9e0',
  ok: '#47d69a', okContainer: '#0f3b2a', onOkContainer: '#bff3db',
  warn: '#ffb938', warnContainer: '#4a3305', onWarnContainer: '#ffe2a8',
  info: '#8fb0ff', infoContainer: '#1e2d75', onInfoContainer: '#dce4ff',
  error: '#ff7a93', errorContainer: '#5a1428', onErrorContainer: '#ffd9e0',
  pending: '#b8a4ff', pendingContainer: '#33257a', onPendingContainer: '#e7e0ff',
  neutral: '#a4a9c2', neutralContainer: '#2a2f4d', onNeutralContainer: '#dde0ef',
  focus: '#8fb0ff',
  scrim: '#000000',
  azure: '#7aa5ff',
  roleFill: '#8fb0ff',
  onRoleFill: '#0a1a5e',
  heroFrom: '#1f2a5e',
  heroTo: '#151833',
} as const;

/** Material 3 colour schemes for Android (brand-seeded, NOT wallpaper-derived). Map 1:1 to Compose ColorScheme. */
export const m3Light = {
  primary: '#2d63cf', onPrimary: '#ffffff', primaryContainer: '#e6edff', onPrimaryContainer: '#163a8f',
  secondary: '#14151c', onSecondary: '#ffffff', secondaryContainer: '#e2e5f6', onSecondaryContainer: '#14151c',
  tertiary: '#5b3fb0', onTertiary: '#ffffff', tertiaryContainer: '#e7e0ff', onTertiaryContainer: '#33207a',
  error: '#c0183f', onError: '#ffffff', errorContainer: '#fde4e6', onErrorContainer: '#b0303f',
  background: '#f4f5fd', onBackground: '#14141a',
  surface: '#f4f5fd', onSurface: '#14141a', surfaceVariant: '#e1e6f8', onSurfaceVariant: '#474b62',
  outline: '#80859f', outlineVariant: '#e6e9f6', scrim: '#0f1230',
  inverseSurface: '#14151c', inverseOnSurface: '#f3f4fb', inversePrimary: '#8fb0ff',
  surfaceDim: '#dde5fb', surfaceBright: '#ffffff',
  surfaceContainerLowest: '#ffffff', surfaceContainerLow: '#f8f9fe', surfaceContainer: '#eceff8',
  surfaceContainerHigh: '#e6e9f6', surfaceContainerHighest: '#e1e6f8',
} as const;

export const m3Dark = {
  primary: '#8fb0ff', onPrimary: '#0a1a5e', primaryContainer: '#1e2d75', onPrimaryContainer: '#dce4ff',
  secondary: '#f3f4fb', onSecondary: '#0c0e1b', secondaryContainer: '#2a305a', onSecondaryContainer: '#f3f4fb',
  tertiary: '#b8a4ff', onTertiary: '#25186a', tertiaryContainer: '#33257a', onTertiaryContainer: '#e7e0ff',
  error: '#ff7a93', onError: '#4a0617', errorContainer: '#5a1428', onErrorContainer: '#ffd9e0',
  background: '#0c0e1b', onBackground: '#f3f4fb',
  surface: '#0c0e1b', onSurface: '#f3f4fb', surfaceVariant: '#2a305a', onSurfaceVariant: '#bdc1d8',
  outline: '#7f85a8', outlineVariant: '#2b3058', scrim: '#000000',
  inverseSurface: '#f3f4fb', inverseOnSurface: '#12131c', inversePrimary: '#2d63cf',
  surfaceDim: '#080a14', surfaceBright: '#2a305a',
  surfaceContainerLowest: '#080a14', surfaceContainerLow: '#111430', surfaceContainer: '#151833',
  surfaceContainerHigh: '#1b1f3d', surfaceContainerHighest: '#212649',
} as const;

export const radius = { xs: 8, sm: 12, md: 16, lg: 20, xl: 28, pill: 999 } as const;
export const space = { 0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48, 16: 64 } as const;

/** Soft, low-contrast shadows. Cards float; there are no hard borders on cards. */
export const shadow = {
  card: '0 1px 2px rgba(35,40,110,0.04), 0 6px 20px rgba(35,40,110,0.06)',
  floating: '0 2px 4px rgba(35,40,110,0.06), 0 12px 32px rgba(35,40,110,0.12)',
  sheet: '0 -8px 40px rgba(35,40,110,0.16)',
} as const;

export const size = {
  tapIos: 44, tapAndroid: 48, tapWeb: 40,
  buttonHeight: 48, buttonHeightCompact: 40, inputHeight: 48, chipHeight: 36,
  tabBarHeight: 64, tabBarInset: 12, topBarHeight: 56,
  sidebarWidth: 264, sidebarCollapsed: 80, contentMax: 1200, readMax: 720,
} as const;

export const motion = {
  fast: 160, base: 240, slow: 320,
  easeStandard: 'cubic-bezier(0.2, 0, 0, 1)',
  easeEmphasized: 'cubic-bezier(0.3, 0, 0, 1)',
} as const;

/** Type. iOS uses SF Pro (system). Android uses Roboto Flex. Web uses Inter (body) + Plus Jakarta Sans (display). */
export const typeWeb = {
  display: { size: 32, line: 38, weight: 800, tracking: -0.02 }, // "Hello, Asha"
  title1: { size: 24, line: 30, weight: 800, tracking: -0.015 },
  title2: { size: 20, line: 26, weight: 700, tracking: -0.01 },
  headline: { size: 16, line: 22, weight: 700, tracking: 0 }, // list-row title
  body: { size: 16, line: 24, weight: 500, tracking: 0 },
  callout: { size: 15, line: 22, weight: 500, tracking: 0 },
  footnote: { size: 13, line: 18, weight: 500, tracking: 0 },
  caption: { size: 12, line: 16, weight: 600, tracking: 0.01 }, // section label ("MAIN")
  button: { size: 16, line: 20, weight: 700, tracking: 0 },
} as const;

export const typeApple = {
  largeTitle: { size: 34, weight: '800' }, title1: { size: 28, weight: '800' }, title2: { size: 22, weight: '700' },
  headline: { size: 17, weight: '600' }, body: { size: 17, weight: '400' }, callout: { size: 16, weight: '400' },
  subhead: { size: 15, weight: '500' }, footnote: { size: 13, weight: '500' }, caption: { size: 12, weight: '600' },
} as const;

export const typeM3 = {
  displaySmall: { size: 36, line: 44, weight: 700 }, headlineMedium: { size: 28, line: 36, weight: 700 },
  headlineSmall: { size: 24, line: 32, weight: 700 }, titleLarge: { size: 22, line: 28, weight: 600 },
  titleMedium: { size: 16, line: 24, weight: 600 }, bodyLarge: { size: 16, line: 24, weight: 400 },
  bodyMedium: { size: 14, line: 20, weight: 400 }, labelLarge: { size: 14, line: 20, weight: 600 },
  labelMedium: { size: 12, line: 16, weight: 600 },
} as const;

export type Theme = typeof light;
export const themes = { light, dark } as const;

```


---

# PART 5 — DESIGN RESEARCH (measurements and platform decisions)

(source: `docs/DESIGN_RESEARCH.md`)

# DESIGN_RESEARCH.md — what was measured and what was researched (24 Oct 2026)

## 1. Measurements from the reference sheet (736×1308 px, 9 phone screens)
Method: pixel sampling and zoomed crops. Dominant colours: app background ≈ `#f4f4fc` (≈50% of pixels), cards ≈ `#fcfcfc`, outer backdrop ≈ `#dce4fc`, black buttons `#181818`, soft-red pill `#fce6e8`, icon blue ≈ `#3b78d8`, "Pro" pill ≈ `#7393e8`, field grey ≈ `#ebeef7`, progress track ≈ `#e3e8fb`.
Structure observed: top bar = heavy wordmark · short black progress line + `0%` · filled bell · periwinkle pill. Hero banner = light periwinkle gradient card with sparkles, big ring, mascot peeking over the bottom edge, bold two-line greeting, round black pencil button. Lists = white cards with a small grey section label, duotone blue icons, bold titles, chevrons. Tab bar = floating white pill, four tabs, **all icons blue duotone**, active tab = soft light-blue capsule with blue bold label, inactive labels near-black bold. Buttons = black pills; destructive = soft pink pill with brick-red text; side-by-side pair for binary choices. Inputs = grey fills inside white cards, `0/120` counter. Sheet = white, top radius ≈28, grabber, mascot + one sentence + black button over a blurred dimmed backdrop. Empty state = small mascot illustration, bold line, faint sentence. Chips: selected = black pill.
Accessibility measurements of the raw reference colours: icon blue on white 4.32:1 (fine for icons, not for text); white on the "Pro" pill 2.97:1 (fails); soft-red text 3.92:1 (fails). Our tokens keep the look and fix these (primary text blue `#2d63cf` 5.53:1; role pill `#4570da` with white text ≥4.5:1; red text `#b0303f` ≥4.5:1 on the pink pill).

## 2. Platform research and decisions
| Question | Finding | Decision |
|---|---|---|
| Can Expo Router **native tabs** produce the floating white pill? | Native tabs expose `tintColor`, `indicatorColor`, `iconColor`, `labelStyle` etc., but on iOS 26+ "the system draws the tab bar" and `backgroundColor`, `blurEffect`, `shadowColor` have no effect; on Android they render Material's navigation bar. Docs do not describe a floating bar. | Use **`expo-router/ui` headless tabs** (`Tabs`, `TabSlot`, `TabList`, `TabTrigger`, `useTabTrigger`) — supported on Android, iOS and web — to build the floating pill. Native tabs stay as an optional alternative if the owner prefers the system look. |
| iOS 26 tab bars | Rebuilding with Xcode 26 gives system Liquid Glass bars that float and can minimise on scroll; on older iOS the classic bar appears. | The reference look does not use glass. Liquid Glass is an optional, default-off flag for iOS 26 only. |
| Material 3 Expressive navigation | Google replaced the tall M3 bar with a shorter "flexible" bar and supports horizontal items on medium windows; M3 indicators are already pill-shaped. | Our custom pill bar mirrors M3's capsule indicator, keeps 48 dp targets and ripples; use rail/horizontal layout on tablets/foldables. |
| Material Symbols on Android in Expo SDK 58 | `expo-symbols` (SDK 58) renders SF Symbols on iOS and **Google Material Symbols on Android and web** via `name={{ ios, android, web }}`; Android weights from `expo-symbols/androidWeights/*`. `@expo/material-symbols` ships XML drawables for `@expo/ui` `Icon` (outlined only by default). | Use `expo-symbols` as the single mobile `<Icon>` implementation (verify in spike S-02); `@expo/material-symbols` is the fallback. This replaces the earlier hook rule that banned `expo-symbols` in Android code. |
| Two-tone icon depth | SF Symbols support hierarchical rendering; Android Material Symbols have fill axis; web Phosphor has a `duotone` weight. | iOS hierarchical + azure tint; Android filled-when-selected + azure tint; web Phosphor Duotone. |
| Heading typeface | Bold geometric grotesques pair well with Inter-class body; Plus Jakarta Sans and Manrope are the common free choices. | Plus Jakarta Sans 800 (display) + Inter 500 (body), both OFL, self-hosted; Noto fallbacks for Hindi/Tamil. |
| Expo Go limits | Remote push on Android is unavailable in Expo Go (SDK 53+); passkeys and widgets need a dev build; `expo-blur` works but Android needs `BlurTargetView`; `@expo/ui` BottomSheet is a native modal with limited props. | Build for Expo Go first, mark dev-build items honestly — see `docs/EXPO_GO_VS_DEV_BUILD.md`. Bottom sheet = JS sheet over a `BlurView` scrim. |
| Safe-area/bottom padding with absolute bars | React Navigation does not pad content for absolutely positioned bars. | Provide `useFloatingTabBarHeight()` and pad every scroll view. |

## 3. Reference product
Searches for a public case study of the reference app returned no usable documentation; its design was therefore reconstructed from the image itself. Its brand assets (name, wordmark, mascot) are intentionally not reproduced.

## Sources
- Expo Go vs dev builds, expo-blur, notifications, @expo/ui: see `docs/EXPO_GO_VS_DEV_BUILD.md`
- Expo Router native tabs (SDK 58): https://docs.expo.dev/versions/v58.0.0/sdk/router/native-tabs.md
- Expo Router UI (headless tabs, SDK 58): https://docs.expo.dev/versions/v58.0.0/sdk/router/ui.md
- Expo Router tabs: https://docs.expo.dev/router/advanced/tabs.md
- expo-symbols (SDK 58): https://docs.expo.dev/versions/v58.0.0/sdk/symbols.md
- @expo/material-symbols: https://cdn.jsdelivr.net/npm/@expo/material-symbols@0.1.1/README.md
- iOS 26 tab bars with Liquid Glass: https://www.donnywals.com/exploring-tab-bars-on-ios-26-with-liquid-glass/
- Material 3 Expressive navigation: https://9to5google.com/2025/05/14/material-3-expressive-navigation/



---

# PART 5b — EXPO GO VS DEVELOPMENT BUILD (what can run where)

(source: `docs/EXPO_GO_VS_DEV_BUILD.md`)

# Expo Go vs development build — what works where (SDK 58)

The owner opens the mobile app through **Expo Go** (`exp://<LAN-IP>:8082`). Some required features cannot run there. This table is binding: build everything so the app **boots and is usable in Expo Go**, mark each feature that needs a development build with `requires: dev-build` in code and in `docs/PREFLIGHT.md`, and never fake it.

| Capability | Expo Go | Dev build / release | Rule |
|---|---|---|---|
| Floating pill tab bar (`expo-router/ui`) | Yes | Yes | Core; must work in Expo Go. |
| `expo-symbols` (SF Symbols iOS / Material Symbols Android+web) | Yes | Yes | Core icon implementation; fallback `@expo/material-symbols`. |
| `expo-blur` scrim | Yes (iOS). Android: wrap the app root in `BlurTargetView` and pass `blurTarget` + `blurMethod="dimezisBlurViewSdk31Plus"` to `BlurView` | Yes | Below Android 12 (API 31) fall back to a plain dimmed scrim. Never rely on blur for legibility. |
| Bottom sheets | Yes — JS sheet (Reanimated + Gesture Handler) over a blurred scrim | Yes | `@expo/ui` BottomSheet is a native modal with limited props and cannot blur the app behind it; use it only for simple sheets. |
| Local notifications (reminders, "remind me again") | Yes | Yes | Core. |
| **Remote push on Android** (FCM) | **No** (removed from Expo Go since SDK 53) | Yes — needs a development build + FCM credentials | `requires: dev-build`. In Expo Go the inbox + SSE still work; the device screen shows `Push needs the installed app` — never a fake success. |
| Remote push on iOS (APNs) | Limited; needs credentials and a registered device | Yes | Verify on a real device only; otherwise `blocked: <reason>`. |
| Passkeys (WebAuthn) | No | Yes — dev build + `associatedDomains` (iOS) / `assetlinks.json` (Android) on the real domain | `requires: dev-build`. Password + TOTP works everywhere and is the baseline. |
| Biometric lock, secure screens, document scanner, QR scanner, quick actions, deep links | Mostly yes (check each module; some config plugins need a build) | Yes | Test in Expo Go first; list any that need a build. |
| Home-screen widgets | No | Yes (config plugin / native target) | `requires: dev-build`; counts only, never amounts. |
| Custom native modules / config plugins | No | Yes | Avoid unless a requirement forces it. |

## Rules for the builder
1. `make dev` must produce a bundle that opens in Expo Go and on `http://localhost:8082` with no red screens.
2. Feature-detect at runtime (`Constants.executionEnvironment`, `Device.isDevice`, permission and module availability) and show the honest state text from the design spec (`Not configured`, `Needs the installed app`), never a silent no-op.
3. `docs/PREFLIGHT.md` lists every `requires: dev-build` item with the exact command to produce the build (`eas build --profile development --platform android|ios`) and the credentials needed (FCM service account, APNs key, Apple team, domain files).
4. Gate G-02 and G-20..G-22 are met in Expo Go only for the non-dev-build subset; the remainder is verified on a development build and recorded.

## Sources
- Expo Go limitations / dev builds: https://docs.expo.dev/develop/development-builds/introduction/
- expo-notifications (Android remote push removed from Expo Go in SDK 53): https://docs.expo.dev/versions/v58.0.0/sdk/notifications/
- expo-blur (Android BlurTargetView): https://docs.expo.dev/versions/v58.0.0/sdk/blur-view/
- @expo/ui bottom sheet: https://docs.expo.dev/versions/v58.0.0/sdk/ui/
- Passkeys with Expo: https://docs.expo.dev/versions/v58.0.0/sdk/local-authentication/ (+ platform associated-domains docs)



---

# PART 6 — PHASED PROMPTS (paste one per fresh session)

(source: `docs/PHASED_PROMPTS_V2.md`)

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



---

# PART 7 — AUDIT OF THE FIRST BUILD (what is broken and missing)

(source: `docs/AUDIT_REPORT.md`)

# AUDIT_REPORT.md — live inspection of the first build (24 Oct 2026)

**What was inspected:** the running app on the owner's machine, through Chrome: web portal `http://localhost:3000` (all 11 top-level tabs, the utility chips, the role dropdown, network traffic), FastAPI docs `http://localhost:8000/docs` and the full OpenAPI document `/v1/openapi.json` (89 routes), and the mobile web preview `http://localhost:8082` (including the Metro bundle response).
**What was NOT inspected (so nothing below claims it):** source code, tests, database/RLS, Docker config, authenticated API behaviour (no credentials were used or entered), Expo Go on a physical device, push delivery. Those need the repository; Phase R0 of the v2 prompt starts by auditing them.

**Verdict:** the backend is a credible skeleton. The web app is a **static, hard-coded mock** that does not talk to it. The mobile app **does not run** (bundle fails). Authentication for the 13 roles is **not implemented in any client**. The build is **not** "completed" against the v3 spec; it is roughly a quarter of the way there, with the right bones.

---

## 1. Findings (ranked)

### Critical
| ID | Finding | Evidence | Why it matters |
|---|---|---|---|
| A-01 | **Mobile app does not start.** The Metro bundle request returns HTTP 503 `UnableToResolveError: react-native-web/dist/exports/AppRegistry`, and the entry resolved is the default `./apps/mobile/node_modules/expo/AppEntry` (not `expo-router/entry`). Metro was started from the monorepo root (`…/SIH`), `react-native-web` is not installed/resolvable under pnpm, and `main` is not the router entry. `http://localhost:8082` is a blank white page. The Expo Go deep link will hit the same bundler (not verified on a device). | `AppEntry.bundle?platform=web…` → 503 JSON | There is no mobile app to review, and every mobile requirement is unmet. |
| A-02 | **The web portal makes no calls to the backend.** During page load and navigation of all 11 tabs, the only requests to `localhost:8000` were the Swagger page's own `openapi.json`. Every number, table row, status and button is hard-coded in the front end. | Network log: no `/v1/*` XHR/fetch from `:3000` | The "real, real-time" requirement is unmet. The dashboard is a picture. |
| A-03 | **No authentication in the web UI and no real roles.** There is no sign-in screen, no password field, no MFA, no session. The "role" is a client-side dropdown with five options (`Institution`, `Scrutiny Officer`, `Competent Authority`, `Bureau Admin`, `Auditor`). Anyone can switch to Competent Authority in one click. `Bureau Admin` is not a spec role, and "Institution" is one generic entry where the spec has three (Org Admin, Submitter, Viewer). Intake/Registry, Finance/Verification, Regional Supervisor, IAM Admin, Platform Operator, Bank Verifier and the integration identity do not exist in the UI. The API does have `/auth/login`, `/auth/logout`, `/auth/step-up`, `/me`, `/me/permissions` — none are used. | Role `<select>` options enumerated; no `input[type=password]` in DOM | Defeats the whole security model (SPEC §4–5). |
| A-04 | **Simulation and demo features are present in the UI** although they were explicitly removed from scope: an **"AI Voice Call"** header chip and **per-row "AI Voice Call"** buttons in the reminder queue; a **"Clock Live"** chip; a **"SIMULATION"** badge next to the product name; **"Simulate Statement Ingestion"**; **"Simulate Tamper"** on every audit block; **"Browse File (Demo FDR)"**. | Visible on Submit FDR, Bank Verification, Reminder Ladder, Audit Chain, header | Violates non-negotiable #1; would be disqualifying in a real review. |

### High
| ID | Finding | Evidence |
|---|---|---|
| A-05 | **Dishonest status displays.** Admin & Connectors shows every connector **HEALTHY** with latencies (e.g. bank gateway 342 ms, PFMS, DigiLocker, FCM, APNs) and "checked" timestamps although no connector is configured. Audit page shows **"Chain integrity 100% valid"** without a verification run. Reminder page is titled **"Statutory escalation ladder"** although the schedule is unapproved (D-10). | Admin, Audit, Reminder screenshots |
| A-06 | **Release screen implies automatic eligibility.** "Eligible for Release" with an all-green checklist and a **"Sign & Issue QR Certificate"** step are hard-coded. Maturity ≠ release permission; the checklist must come from approved policy rows with independent evidence; the portal must not issue a substitute sanction/NOC. | Release Authorization screenshot |
| A-07 | **Evidence model is the old L0–L3 ladder** ("L1 Only", "L2 Branch Verified", "L3 Gold Standard", an "Evidence levels" filter, an L0–L3 distribution on the dashboard). The spec forbids collapsing evidence into one score; attributes are separate (Declared · Extracted · Bank-confirmed · Ledger-reconciled · Inconclusive/Rejected). | Dashboard, Search, Bank Verification |
| A-08 | **Reports are fake.** "Generate Report File", "Generated exports & downloads history" and the KPI tiles (₹1,50,00,000 pool, ₹75,00,000 compliant) are static; no `/reports` or `/exports` API exists. | Reports screenshot; OpenAPI |
| A-09 | **AI Copilot includes "Text-to-SQL Analytics".** Unconstrained text-to-SQL is excluded by the spec (injection and data-leak risk). Policy Q&A must go through `/ai/policy-qa` with citation resolution. | AI Copilot tab |

### Medium
| ID | Finding |
|---|---|
| A-10 | **Backend gaps** (no routes at all): dashboard/KPIs, reports & exports (async jobs), audit viewer + chain verification, users/roles/assignments/recertification/invitations, MFA/passkeys/session list, global search + saved views, reminder schedule & scheduler status, maturity calendar, renewals/lineage UI endpoints beyond `instruments/lineage`, help/support/grievance, retention/legal-hold/rights, templates admin, institution-user management. |
| A-11 | `/docs` (Swagger) loads its JS/CSS from `cdn.jsdelivr.net`; docs must be disabled or self-hosted in production. `/openapi.json` 404 while `/v1/openapi.json` works — pick one documented path. |
| A-12 | Visual design is the retired dark neon theme; no empty/error/forbidden/offline states observed; header is crowded (11 tabs + 5 chips in two rows) and does not collapse for phones. |
| A-13 | Language switcher (EN / हिंदी / தமிழ்) is present; translation completeness not verified; spec requires reviewed vs machine-draft status per key. |

### Low
A-14 `favicon.ico` 404 on API origin. A-15 footer technology chips ("PostgreSQL 16", "Vite", etc.) are marketing, not information — remove. A-16 hard-coded sample institutions and FDR numbers (AXIS-FDR-99201, SBI-881920, HDFC-441029, PNB-771829) must be removed from every production path.

---

## 2. What exists (keep and harden)
The API surface is a good skeleton and mirrors the spec's modules: `auth` (login, logout, step-up), `me`, `me/permissions`; admin registry (feature/connector states + health checks); public receipt verification; institutions + onboarding (apply, review, batch-import); instruments (draft, submit, transition, versions, receipt, lineage); observations (create, send, respond, resolve) + case comments; intake/scrutiny/assign queues; documents (upload-intent, direct upload, download, extract, extraction review); bank verification requests (create, respond, decision, escalate); statement import, batches, lines, exceptions; discrepancy evaluate/generate-observation/acknowledge; policies (import-drafts, approve); release-requests (checklist rule, clearances, recommendation, decision, execution, discharge); notifications (list/read/ack/action, device register/revoke, preferences, test, DLQ + replay, funnel); SSE `/stream`; AI (`status`, `policy-qa`, `case-summary`, `translation-draft`); health/ready probes. Whether each handler enforces authorisation, scope, RLS, idempotency, optimistic concurrency and audit/outbox is **unverified** and is the first thing Phase R0 tests.

## 3. Coverage against the spec (modules F-01…F-28, mobile M-01…M-21)

Legend: **API** = route exists (behaviour unverified) · **MOCK** = UI only, hard-coded · **—** = nothing.

| Module | State | Gap to close |
|---|---|---|
| F-01 Identity, sessions, MFA, step-up, recertification | API (login/step-up) · UI — | Entire client auth; MFA/passkeys; sessions list; lockout; invitations; recovery; recertification |
| F-02 Institution registry & onboarding | API · UI MOCK | Real screens; merge-review queue; import wizard with dry run |
| F-03 Instrument register & versions | API · UI MOCK | Real list/detail/wizard, diff view, receipts |
| F-04 Document vault/upload pipeline | API · UI MOCK ("Demo FDR") | Real upload (resumable), scan status, hash, viewer |
| F-05 OCR/extraction review | API · UI — | Side-by-side review UI |
| F-06 Bank verification & evidence decision | API · UI MOCK | Workbench + isolated bank-verifier portal |
| F-07 Statement import & reconciliation | API · UI MOCK | Real import UI, matches, exceptions; remove "simulate" |
| F-08 Discrepancy engine | API · UI — | Rule list, outputs as draft observations |
| F-09 Observations/casework | API · UI — | Inbox/detail/threads (internal vs institution-visible) |
| F-10 Lifecycle & escalation scheduler | — / MOCK ladder | Scheduler, approved-schedule gate, reminders, heartbeat, admin alert |
| F-11 Renewal & lineage | API (lineage) · UI — | Lineage graph, gap/overlap |
| F-12 Release workflow | API · UI MOCK (auto-eligible) | Policy-built checklist, clearances, maker-checker, step-up, execution evidence |
| F-13 Policy registry | API · UI — | Diff/approve UI, effective dates, BLOCKED penalties |
| F-14 Notifications (inbox, FCM/APNs/Web Push, DLQ, funnel) | API · UI MOCK (connectors fake HEALTHY) | Real inbox, preferences, device status, honest provider state |
| F-15 Realtime SSE | API (`/stream`) · UI — | Client subscription with Last-Event-ID |
| F-16 Dashboard, reports, exports | — · MOCK | Whole module |
| F-17 Search & saved views | — · MOCK | Whole module |
| F-18 Audit & access logging, chain verification | — · MOCK | Viewer, verification job, checkpoints |
| F-19 Admin (users, roles, connectors, DLQ, templates, retention) | partial (registry, DLQ) | Users/roles/assignments, templates, retention |
| F-20 Receipts & verifiable QR | API (public verify) · UI — | Public page, signed PDF, QR |
| F-21 Help/support/grievance · F-22 Retention/rights | — · static text | Workflows |
| F-23 Migration/bulk import · F-24 Queues/workload · F-25 Comments | partial API · — | UI + supervisor board |
| F-26 Policy Q&A / case summary | API (`/ai/*`) · UI partial + disallowed text-to-SQL | Wire to API, citations, remove SQL |
| F-27 i18n · F-28 Accessibility | switcher only | Catalogue, review status, a11y pass |
| M-01…M-21 (push, biometric lock, scanner, QR, widgets, offline cache, quick actions…) | **Nothing runnable** | All |

## 4. What to do next (in this order)
1. **Make it boot and make it honest (R0–R1):** fix the Expo/Metro setup so web preview, Expo Go and a dev build all start; remove every simulation/demo/fake-health item (A-04, A-05, A-16); add the production-guard test.
2. **Real authentication and the 13 roles (R2):** login, MFA, step-up, sessions, invitations, navigation manifest from the server, staging users, role walkthrough tests (A-03).
3. **Wire both clients to the API with a generated client (R3)** and delete every hard-coded array.
4. **Fill the missing backend modules (R4):** dashboard, reports/exports, audit, users/roles, search, reminders/scheduler, sessions, help, retention.
5. **Apply the new design system on web and mobile (R5–R6)** from `design/preview.html` and `design/DESIGN_SPEC.md`.
6. **Realtime + push + mobile-native features (R7)**, then **hardening, a11y, performance, docs (R8)** and an **independent final audit (R9)**.

## 5. Features and functions to add (beyond the first build)
Role-aware home with live "Needs your action" and real counts · global search / ⌘K palette with saved views and shareable deep links · maturity calendar with a tokenised **.ics subscription feed** and "add to calendar" on mobile · bulk actions + keyboard shortcuts for officers · document viewer with side-by-side extraction review and region highlights · case timeline with provenance drawer on every fact · institution onboarding checklist with a **real** progress bar · per-role digest e-mail (opt-in, only when SMTP is configured) · notification preferences with quiet hours for optional categories only · dark mode, font scale, Hindi/Tamil with review status · institution compliance summary report · public receipt verification page + in-app QR scanner · import wizard (mapping versions, dry-run) · delegation and access-recertification admin UI · status banner for degraded integrations and maintenance windows · printable scoped case summary · mobile: document scanner, biometric lock, home-screen widgets (counts only), quick actions, offline read cache, device/notification status with a real test push.

