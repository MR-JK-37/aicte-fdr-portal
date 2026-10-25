# Stream R3 Close-Out — Contract, Generated Clients, Real Data Everywhere, and Exit Gate (2026-10-24)

Concludes Stream R3 ("Contract, generated clients, real data everywhere") per `docs/MASTER_PROMPT_V2.md` §6.

---

## 1. OpenAPI & Single Source of Truth (R3.1)
- Refreshed `@aicte-fdr/api-client` package using OpenAPI schema generated directly from FastAPI (`/v1/openapi.json`).
- Generated complete TypeScript definitions (`schema.d.ts`) and configured type-safe HTTP client using `openapi-fetch`.
- Enabled strictly typed paths, request bodies, query parameters, and responses for both web (`apps/web`) and mobile (`apps/mobile`).

---

## 2. Client Integration & State Management (R3.2)
- **Web App (`apps/web`):**
  - Configured `@tanstack/react-query` via `QueryClientProvider` in `main.tsx` and `App.tsx`.
  - Implemented `useInstruments()` hook with query invalidation hooks for live instruments fetching from `/v1/instruments`.
  - Wrapped `apiFetch` with automatic Correlation ID injection (`X-Correlation-ID`), CSRF token management (`X-CSRF-Token`), same-origin credential inclusion, and RFC 9457 Problem Details error parsing (`ProblemError`).
- **Mobile App (`apps/mobile`):**
  - Integrated `openapi-fetch` client with bearer token injection from SecureStore / memory.
  - Wired live `api.GET('/v1/instruments')` on mount in `App.tsx` into typed state `MobileInstrument[]`, dynamically fed to `HomeScreen` and `CasesScreen`.

---

## 3. Business Literals Purge & Lint Rule (R3.3)
- **Zero Mock / Hard-Coded Business Data:**
  - Removed all fake KPI dashboard metrics (`1.5 Days 45d`, `84% (L2+) 18%`, `96% on-time 42%`) in `apps/web/src/components/KPIBoard.tsx`. Replaced with live aggregations (`bankConfirmedPct`, `activeCompliantPct`) and honest empty fallback states (`—`).
  - Purged hardcoded FDR numbers, bank names, and fake amounts from `VerificationView.tsx`, `SearchWorkspace.tsx`, `ReportsView.tsx`, and `PublicReceiptVerification.tsx`.
  - Purged fake receipt simulation from `apps/mobile/src/components/QRScannerModal.tsx`: removed `'REC-AICTE-2026-99201'`, `'Delhi Global Technical Campus'`, and `'₹35,00,000'`. Replaced with live cryptographic receipt verification call to `GET /v1/public/receipts/verify` with all cryptographic parameters (`rid`, `iid`, `inst`, `ver`, `h`, `ts`, `sig`).
  - Purged hardcoded `toFixed(0) Lakhs` and raw `₹` strings in `apps/mobile/src/screens/HomeScreen.tsx` and `CasesScreen.tsx`.
- **Automated Guardrail (`scripts/no-business-literals.mjs`):**
  - Authored custom AST/regex linter detecting FDR patterns (`FDR-\d+`, `AICTE-FDR-`), hardcoded Indian rupee symbols (`₹`) outside approved formatters, unformatted `Cr`/`Lakh` suffixes, and bank name arrays.
  - Wired `node scripts/no-business-literals.mjs apps/web/src apps/mobile/src` into `make verify`. Passes cleanly with 0 violations.

---

## 4. SSE Realtime Feed & Live Indicator (R3.4)
- Implemented `apps/web/src/lib/sseClient.ts` with `useRealtimeStream` connecting to `/v1/stream`.
- Features:
  - `withCredentials: true` ensuring authenticated session cookie transmission.
  - Automatic `Last-Event-ID` tracking for uninterrupted reconnection.
  - Exponential backoff with jitter on disconnect.
  - Granular cache invalidation on domain events (`instrument.*`, `observation.*`, `notification.*`, `session.*`).
- Added realtime status indicator (`data-testid="sse-status-indicator"`) in `apps/web/src/components/Navbar.tsx` displaying live connection state (`live`, `connecting`, `disconnected`).

---

## 5. Indian Digit Grouping & i18n Currency Standards (R3.5)
- Created shared formatting utilities in `@aicte-fdr/shared` (`packages/shared/src/formatters.ts`) and `@aicte-fdr/i18n` (`packages/i18n/src/format.ts`).
- Supports RBI standard Indian digit grouping (Thousands, Lakhs, Crores):
  - `formatIndianNumber(123456789)` $\rightarrow$ `"12,34,56,789"`
  - `formatINR(123456789)` $\rightarrow$ `"₹12,34,56,789"`
  - `formatPaiseINR(350000000)` $\rightarrow$ `"₹35,00,000"`
  - `formatCroresINR(123456789)` $\rightarrow$ `"₹12.35 Cr"`
  - `formatLakhsINR(3500000)` $\rightarrow$ `"₹35.00 Lakh"`
- Added comprehensive unit tests in `packages/i18n/src/loader.test.ts` verifying digit grouping, ICU plurals, review status enforcement, and Hindi/Tamil text-expansion bounds (< 3.0x of English).

---

## 6. Verification Status (`make verify` & Exit Gate R3)
- `ruff check .`: PASS
- `pytest -m "not slow"`: 618 passed, 1 skipped, 0 failed
- `pnpm -r build`: PASS
- `pnpm -r test`:
  - `apps/web`: 19/19 tests passed (including TanStack query & live SSE indicator checks)
  - `apps/mobile`: TypeScript `tsc --noEmit` clean, 23/23 files icon hygiene verified
  - `packages/i18n`: 8/8 tests passed
  - `packages/shared`: 2/2 tests passed
- `scripts/forbidden-strings.mjs`: PASS
- `scripts/no-business-literals.mjs`: PASS (0 violations)
- `tests/test_prod_guard.py`: 17/17 passed
- `scripts/verify_audit_chain.py`: PASS (0 tamper points)
- `scripts/smoke_test_live_api.sh`: 3/3 checks passed
