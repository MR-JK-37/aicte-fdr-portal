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
