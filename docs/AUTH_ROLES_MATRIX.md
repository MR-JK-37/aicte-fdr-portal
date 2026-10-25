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
