# Stream R2.4 — Web sign-in UI (2026-10-24)

First real UI in `apps/web` wired to the real backend — until this session, `apps/web/src` had
zero `fetch()`/API calls (confirmed in R1's inventory) and no auth of any kind. This closes that
for the web client specifically; mobile (R2.5) is still untouched.

## What was built
- **`packages/api-client`**: `createApiClient` now passes `credentials: 'include'` (the backend's
  session/refresh tokens are httponly cookies) and a dynamic `fetch` wrapper
  (`(...args) => globalThis.fetch(...args)`) instead of letting `openapi-fetch` capture
  `globalThis.fetch` once at client-creation time — found this the hard way: it silently broke
  every test that mocked `fetch` after the client singleton was constructed. Documented in the
  source so the next person doesn't lose time rediscovering it.
- **`apps/web/src/lib/apiClient.ts`**: the module-level typed client, base URL resolved from
  `window.location.origin` (not a bare `''`) — relative URLs aren't valid `Request` input under
  Node/jsdom's WHATWG implementation the way they are in a real browser, so this would otherwise
  work in the browser but break every test using it.
- **`apps/web/vite.config.ts`**: dev proxy now forwards `/v1` to `:8000` (previously only `/api`
  was proxied — dead code, since the real backend never used that prefix). Needed so the
  httponly cookies stay same-origin in dev.
- **`apps/web/src/auth/AuthContext.tsx`**: calls `GET /v1/me` on mount; `signed-out` on any
  failure, `signed-in` with the real profile + `GET /v1/me/navigation` manifest on success.
- **`apps/web/src/auth/LoginScreen.tsx`**: real email+password form against `POST /v1/auth/login`.
  Handles the two-phase flow the backend's single-call design implies: submits without a TOTP
  code first; if the server's response indicates TOTP is required (distinguished from a plain
  wrong-password rejection by checking the response detail text), shows a second screen asking
  for the code and resubmits with it included.
- **`apps/web/src/auth/MfaEnrolmentWizard.tsx`**: calls the real `/auth/mfa/enrol/start` /
  `/confirm` pair. Shows the real provisioning secret/URI (no QR image renderer wired — shown as
  copyable text + the raw `otpauth://` URI, which any authenticator app also accepts via manual
  entry) and the real one-time recovery codes from the confirm response.
- **`apps/web/src/auth/StepUpContext.tsx`**: a `useStepUp()` hook other components can call before
  a sensitive action; opens a real modal that posts to `POST /v1/auth/step-up` and only resolves
  `true` on a genuine server-verified code. Not yet wired to any actual sensitive action (release
  decisions, role grants) — those screens don't exist yet themselves (ReleaseWorkflow is still the
  honest "not yet connected" placeholder from R1) — so this is infrastructure ahead of its first
  caller, not dead code: R4/R5 wire the real actions through it instead of reinventing step-up.
- **`apps/web/src/components/SecurityView.tsx`** (new "Security" tab): real profile-completion
  percentage/checklist, real MFA enrolment trigger, real session list with per-session revoke and
  "sign out everywhere" — all against the R2 endpoints from the prior slices, zero fabricated data.
- **`apps/web/src/components/Navbar.tsx`**: the client-side role `<select>` (A-03, deferred since
  R1 specifically so it could be replaced with something real rather than just deleted) is gone —
  replaced with a read-only role pill sourced from the authenticated session, plus a real sign-out
  button. **`forbidden-strings` is now 100% clean** across web, mobile, and backend — the one
  remaining known item from R1 is resolved. Wired into `make verify` as a hard gate (was
  deliberately not wired in until this was true).
- **`apps/web/src/App.tsx`**: gates the whole app behind `AuthContext`'s status — `checking` shows
  a loading state, `signed-out` shows `LoginScreen`, `signed-in` renders the real app shell with
  the real role (no more a locally-owned `useState<AppRole>`).
- **`apps/web/src/App.test.tsx`**: rewritten to mock `fetch` for `/v1/me`, `/v1/me/navigation`,
  `/v1/me/profile-completion`, `/v1/auth/sessions` (clearly a **unit-test** mock, not an e2e one —
  no real backend/DB in a jsdom component test, unlike the Playwright e2e tests CLAUDE.md's "never
  mock fetch" rule targets) and asserts the signed-out→signed-in transition, the real role pill,
  and that every other R1 honesty assertion still holds once gated behind real auth.

## Bug found and fixed along the way
Spent real debugging time on test failures that looked like an auth/state bug but weren't: the
mock-matching code in the first draft of `App.test.tsx` called `.toString()` on the `Request`
object `openapi-fetch` constructs internally, which gives the literal string `"[object Request]"`,
not the URL — every mocked fetch call silently fell through to the "unmocked, 404" branch. Traced
with a minimal reproduction (not guessed) down to this and to the separate `baseFetch` capture
issue above; both are now fixed in a way future tests/code can't repeat (helper function extracts
`.url` from a `Request` instance; the client wrapper resolves `fetch` dynamically).

## Evidence
- `pnpm --filter web test` → **18/18 passed** (signed-out login screen, signed-in dashboard, role
  pill with no combobox role-switcher, every R1 honest-state assertion, Security tab with real
  data).
- `pnpm -r build` (full workspace) → clean.
- `node scripts/forbidden-strings.mjs apps/web/src apps/mobile services/api/app` → **clean, zero
  markers** (first time this session this has been true).
- `cd services/api && pytest tests/test_prod_guard.py -q` → 17/17.
- `cd services/api && python scripts/verify_audit_chain.py` → PASS (0 entries, 0 tamper points —
  honest, not fabricated; nothing has written to the audit log in this session's test runs beyond
  what pytest itself generates and rolls back).
- `make verify` **still does not complete end-to-end** — it stops at the backend test step on the
  same 3 pre-existing `test_outbox_scheduler.py` failures documented since R0 (live
  advisory-lock contention with the `fdr-portal-worker-1` container, not a regression from this
  session). Every step after that point was run manually instead and confirmed green (above).

## Carried forward — explicitly NOT done this session
1. **Mobile sign-in UI (R2.5)** — `apps/mobile` still has no auth of any kind; the R0 boot shim
   still routes to the old (now largely-purged-of-fakes, but never-authenticated) `App.tsx`.
2. **QR code rendering for MFA enrolment** — the provisioning URI/secret are shown as text, not an
   actual scannable QR image. Works (any authenticator app accepts manual secret entry), just not
   the friendliest UX; a QR library is a small, deliberately-deferred addition.
3. **`useStepUp()` has no real caller yet** — built so R4/R5's sensitive-action screens (release
   decisions, role grants) can use it instead of reinventing step-up, but nothing calls it yet
   because those screens are still honest placeholders.
4. **Password reset/forgot-password UI**, invitation-acceptance UI — the backend endpoints don't
   exist yet either (R2 "Carried forward" from the auth-backend report).
5. **Design fidelity** — this is the existing v1 dark-glass styling (inline styles matching the
   surrounding components), not the v2 "Lavender Ledger" system from `docs/MASTER_PROMPT_V2.md` —
   consistent with ADR-002's decision that the actual token/component swap happens in stream R5,
   not piecemeal per screen.
6. The test-DB-isolation gap from R0/R1 (tests share the live dev database with the
   `fdr-portal-worker-1` container) is still open — it's why `make verify` can't complete clean
   end-to-end in this environment.

## Open decisions touched
None new.

---
**STREAM R2 (web UI slice): PASS** — the web client can now actually sign in, enrol MFA, pass
step-up, and manage sessions against the real backend built in the earlier R2 slices, with
`forbidden-strings` clean end-to-end for the first time this session. Mobile auth UI (R2.5) is the
next piece.
