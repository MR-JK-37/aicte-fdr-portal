# Stream R2.5 — Mobile sign-in UI, and two real bugs found by actually testing it (2026-10-24)

Mirrors the web auth UI (`docs/phase-reports/R2-web-ui.md`) on `apps/mobile` against the same real
backend. This report exists mainly because **actually running this end-to-end in a browser found
two real, independent bugs that no unit test or typecheck caught** — recorded in detail because
they're exactly the kind of thing "tests pass" can hide.

## What was built
- **`apps/mobile/src/lib/secureStorage.ts`**: wraps `expo-secure-store` (real Keychain/Keystore on
  iOS/Android) with a `localStorage` fallback on the web-preview target only (its native module is
  an empty stub on web — verified by reading the installed package, not assumed). Documented as a
  real platform limitation, not a simulated success: production mobile builds always use the real
  secure storage path.
- **`apps/mobile/src/lib/apiClient.ts`**: bearer-token API client (mobile has no cookies) with
  in-memory access token + `app_sessions`-backed refresh token persisted via the above. Added
  `openapi-fetch`/`@aicte-fdr/api-client`/`expo-secure-store` as new mobile dependencies.
- **`apps/mobile/src/auth/{AuthContext,LoginScreen,MfaEnrolmentWizard,StepUpContext}.tsx`**: React
  Native equivalents of the web auth components, same password→TOTP two-step login flow, same real
  MFA enrolment (candidate secret shown as copyable text — no QR renderer, same gap as web),
  same step-up hook pattern.
- **`apps/mobile/src/screens/MoreScreen.tsx`**: the "Active Signatory Role" multi-select button grid
  (A-03 — a second, mobile-specific client-side role switcher that forbidden-strings' regex-based
  web-only `<option>` check never caught, because React Native doesn't have `<option>` elements) is
  gone — replaced with a read-only role display, a real "Two-step verification" row opening the MFA
  wizard, and a real "Sign out" row.
- **`App.tsx` / `app/_layout.tsx`**: gates on `useAuth()`'s status, same shape as web.

## Two real bugs found by testing this in an actual browser, not assumed fixed
Everything above typechecked clean and the existing icon-hygiene/forbidden-strings checks passed —
none of that would have caught either of these. Found by loading `:8082`, logging in with a real
test account, and reading the console/network tab.

### Bug 1 — Metro lazy-route bundling duplicates `AuthContext.tsx` as two separate module instances
Wrapping `<AuthProvider>` around `<Slot/>` in `app/_layout.tsx` (the obvious place — it's exactly
how `apps/web/src/main.tsx` does it) threw `useAuth must be used inside AuthProvider` at runtime,
even though the component tree is correctly nested in source. Added a one-line
`console.log('AUTHCONTEXT_MODULE_LOADED')` at the top of the context module and watched the
browser console: it logged **twice** per page load. Expo Router's `lazy=true` bundle splitting
loads `app/_layout.tsx` and `app/index.tsx` → `../App.tsx` as separate chunks that don't dedupe
this shared module, so `createContext()` ran twice, producing two different Context objects — a
Provider mounted in one chunk is invisible to a consumer in the other.
**Fix:** moved `AuthProvider`/`StepUpProvider` into `App.tsx` itself, wrapping a `Gate` component
in the same module as every `useAuth()`/`useStepUp()` call site, so Provider and consumers are
always in the same bundle regardless of Metro's chunking. Documented in both `_layout.tsx` and
`App.tsx` so the next person doesn't lose time rediscovering it, and doesn't "fix" it by moving the
provider back to the first place Expo Router convention suggests.

### Bug 2 — No CORS on the backend; browsers (but not real mobile apps) need it
With the context fix in place, login got further but failed with a generic network error (visible
as a 503 in the devtools network tab, which is misleading — it's a CORS block, not a real server
503; confirmed by `curl`ing the same endpoint directly and getting a correct 200/401). The FastAPI
app had **no `CORSMiddleware` at all**. A packaged native iOS/Android app is not a browser and
isn't subject to CORS, but the Expo *web* preview target (the only mobile target this sandbox can
actually run — no device/emulator available) is. Added `CORSMiddleware` with an explicit
origin allow-list (`http://localhost:3000`, `http://localhost:8082` — `allow_credentials=True`
requires an explicit list, not `"*"`, per the CORS spec) via a new `settings.cors_allowed_origins`.

### Bug 3 (found right after fixing #2) — the mobile API client's auth-header wrapper silently stripped `Content-Type`
With CORS fixed, login reached the server but failed with a Pydantic validation error:
`"Input should be a valid dictionary ... 'input': b'{"email":...}'"` — the body arrived as raw
bytes with no `Content-Type: application/json`. `openapi-fetch` calls the custom `fetch` as
`fetch(request, requestInitExt)` where `request` is an already-built `Request` (with its own
`Content-Type` header) and `requestInitExt` is a separate, mostly-empty init object. The mobile
wrapper built its headers from `new Headers(init?.headers)` — ignoring `input`'s own headers — then
passed that (near-empty) `Headers` object as part of the second `fetch(request, init2)` argument,
which **overrides** the Request's real headers entirely per the Fetch spec, discarding
`Content-Type` even though the body itself was untouched. **Fix:** build the headers from
`input.headers` when `input` is a `Request` instance, falling back to `init?.headers` otherwise.

## The stale-deployment problem this also surfaced
Testing against `http://localhost:8000` revealed the **live, long-running `fdr-portal-api-1`
Docker container (built at 2026-10-24T10:21:30Z, 19+ hours before this point in the session) was
still running the pre-R2 code** — `curl`ing the live login endpoint with an intentionally wrong
password returned **HTTP 200 and a valid token**, confirming the exact bypass this stream spent two
earlier slices fixing was still live and reachable the whole time, despite every automated test
passing. The cause: `docker inspect` showed no source volume mount — the image bakes in the source
at build time, and nothing in this session's work had rebuilt it; `services/api`'s automated tests
run against a separate local `uv` venv process, which is why they never caught this gap. **Fixed by
rebuilding and redeploying** `api`, `worker`, and `migrate` (each has its own separate image despite
sharing a Dockerfile — the first rebuild attempt only targeted `api`+`worker` and the `migrate`
service failed with "Can't locate revision" because its stale image didn't have the new migration
files) via `docker compose build` + `up -d`. Re-verified with `curl`: wrong password → 401, correct
password → 200 with the new session-aware response shape (`expires_in: 900`, real `refresh_token`,
embedded `session_id`).
**This is a real process gap worth naming explicitly**: automated tests (pytest against a local
venv) and the actual deployed service can silently diverge in this dev setup, and nothing flags it.
Not fixed this session (tracked below).

## Evidence
- Full end-to-end manual verification via `mcp__claude-in-chrome` against the real rebuilt backend
  (not mocked): real login with a real test account (created, then deactivated afterward —
  `audit_log` references it so the row can't be deleted, which is correct append-only behaviour,
  not a cleanup failure), real MFA enrolment (computed the actual TOTP code for the shown secret
  with `pyotp` and confirmed it), real recovery codes displayed, real read-only role pill, real
  honest empty states on the home screen (no fabricated instruments/reminders).
- `cd services/api && pytest -m "not slow" -q` → 613 passed, 3 failed (same pre-existing,
  unrelated `test_outbox_scheduler.py` issue), `ruff check .` clean.
- `pnpm -r build` (full workspace) → clean.
- `pnpm --filter web test` → 18/18 (unaffected by backend CORS/mobile changes).
- `apps/mobile`: `tsc --noEmit` clean, icon-hygiene script clean (23 files).
- `node scripts/forbidden-strings.mjs apps/web/src apps/mobile services/api/app` → clean (the
  mobile role-switcher button grid removal closes the gap the web-only `<option>` regex couldn't
  see).
- `npx expo export --platform web` → exit 0 (re-verified after all fixes).

## Carried forward — explicitly NOT done this session
1. **No automated check that the live deployed container matches source.** The stale-deployment
   bug above was found by manual testing, not by any gate. Worth adding something like a
   `make redeploy` step to the phase workflow, or a smoke-test hitting the live `:8000` after any
   backend change — not built this session.
2. QR code rendering for MFA enrolment (same gap as web — secret/URI shown as text).
3. Biometric unlock is still the honest "not implemented yet" placeholder from R1 — this session
   added real password+TOTP auth, not biometric re-lock (M-03).
4. `cors_allowed_origins` is a hard-coded local-dev list; a real staging/production deployment
   needs this driven by actual config, not the code default.

## Open decisions touched
None new.

---
**STREAM R2 (mobile UI slice): PASS** — mobile can now sign in, enrol MFA, and sign out against
the real backend, verified end-to-end in a real browser session rather than assumed from passing
unit tests. Two real cross-cutting bugs (Metro module duplication, missing CORS) and one
mobile-specific header bug were found and fixed along the way, plus the significant discovery that
the live dev deployment had been running pre-R2, vulnerable code the whole time this stream's
earlier slices were "done" — now redeployed and re-verified.
