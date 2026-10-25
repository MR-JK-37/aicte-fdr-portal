# Stream R5 Closeout Report — Design System and Web App

**Status:** PASS  
**Branch:** `v2/fix-and-complete`  
**Milestone:** Stream R5 (Design system and web app per `docs/MASTER_PROMPT_V2.md` §8)  
**Date:** 2026-10-24  

---

## 1. Executive Summary

Stream R5 delivered the complete reference-derived **Lavender Ledger (v2.1)** design system and web application shell for the AICTE Security Deposit (FDR) Portal, adhering strictly to `design/DESIGN_SPEC.md` and the exit criteria in `docs/MASTER_PROMPT_V2.md`.

All styling is token-driven and mathematically verified against WCAG 2.1 AA standards. Zero synthetic/fabricated data exists in the client; all screens query live endpoints (`/v1/instruments`, `/v1/me`, `/v1/me/navigation`, `/v1/me/profile-completion`, etc.) via `@tanstack/react-query` and `@aicte-fdr/api-client`.

---

## 2. Deliverables & Technical Architecture

### 2.1 R5.0 Design-Contract Tests First (`DesignContract.test.tsx`)
Written and executed prior to finalizing layout and visual components:
- **Location:** `apps/web/src/design-system/DesignContract.test.tsx`
- **10 Core Contract Assertions:**
  1. Top bar contains `wordmark`, `progress-mini`, `bell`, `role-pill`.
  2. Role pill has background `--role-fill` and text `--on-role-fill` with WCAG contrast $\ge 4.5:1$ (measured 4.65:1).
  3. Primary buttons are pills with background `--ink` (`#1a1a1e`) and text `--on-ink` (`#ffffff`).
  4. Destructive action buttons use `--danger-container` (`#fde4e6`) with text `--on-danger-container` (`#b0303f`).
  5. Cards have radius 20px and soft shadow (`--shadow-card`), without 1-px borders.
  6. Floating tab bar has `position: fixed`, radius 28px, floating shadow, 12px side inset, active capsule in `--primary-container` with `--primary` text, and all icons tinted `--azure`.
  7. List rows are 52–56px high with hairline separators and chevrons.
  8. Segmented controls use track `--field` and selected black pill `--ink`.
  9. Bottom sheets have a grabber bar, 28px top radius, and blurred scrim (`backdrop-filter: blur(6px)`).
  10. Empty states render the Kosh mascot SVG.

### 2.2 R5.1 Design Tokens, Contrast Verification & Lint Rule
- **Authoritative Tokens:** `design/tokens.ts` and `design/tokens.css` defining the Lavender Ledger palette:
  - Canvas: `#f4f5fd` (light), `#080a14` (dark)
  - Surface: `#ffffff` (light), `#151833` (dark)
  - Field: `#eceff8` (light), `#1b1f3d` (dark)
  - Ink: `#1a1a1e` (primary action pill)
  - Azure: `#3b78d8` (icons and non-text interactive accents)
  - Primary text: `#2d63cf`
  - Role Fill: `#4570da` (contrast on white text 4.65:1)
  - Danger Container: `#fde4e6`
- **Parity & Contrast Guard:** `design/check_tokens.py` executes:
  - 96 token parity checks between `tokens.css` and `tokens.ts`.
  - 192 WCAG contrast checks across all surfaces and containers.
  - Result: `192 contrast checks passed; 96 token parity checks passed; tokens OK`.
- **Self-Hosted Typography:**
  - `@fontsource/inter` (weights 400, 500, 600, 700) for body and UI.
  - `@fontsource/plus-jakarta-sans` (weights 700, 800) for display, headings, and wordmark.
  - SIL Open Font License files preserved in `apps/web/public/fonts/LICENSE-Inter.txt` and `LICENSE-PlusJakartaSans.txt`.
  - Zero external CDN dependencies in `apps/web/index.html`.
- **Zero Raw Color Lint (`scripts/no-raw-colour.mjs`):**
  - Enforces that no CSS/TS/TSX file in `apps/web/src` contains raw hex colors outside the token palette.
  - Verification: `node scripts/no-raw-colour.mjs apps/web/src` exits 0 (`no-raw-colour: OK`).

### 2.3 R5.2 Component Library & Phosphor Duotone Icons
- Headless, accessible primitives implemented in `apps/web/src/design-system/`:
  - `Button.tsx`: Black pill primary (`btn-primary`), soft blue (`btn-soft`), soft red destructive (`btn-danger-soft`), full-width in cards and sheets.
  - `Card.tsx`: Solid white card with 20px radius, soft shadow, no 1px border.
  - `FloatingTabBar.tsx`: Floating pill navigation (radius 28px, floating shadow, 12px inset, 64px height) with light-blue active capsule (`primaryContainer`) and azure duotone icons.
  - `TopBar.tsx`: Top navigation bar with wordmark, progress-mini, bell, and role pill.
  - `Sidebar.tsx`: Floating sidebar card (radius 20px, soft shadow) with pill nav items and capsule active state.
  - `BottomSheet.tsx`: 28px top radius, sheet grabber bar, blurred scrim.
  - `States.tsx`: Loading, EmptyState, ErrorState, ForbiddenState, OfflineState — all integrated with Kosh SVG illustrations.
  - `EvidenceChip.tsx` & `StatusBadge.tsx`: Pill badges with semantic container tokens and icon mappings.
  - `primitives.css`: Comprehensive CSS classes for all components.
- **Phosphor Duotone Icons (`Icon.tsx`):**
  - Pinned `@phosphor-icons/react` (MIT).
  - Closed enum of 44 logical keys with `duotone` weight for nav/list icons (azure) and `regular` elsewhere.

### 2.4 R5.3 Kosh Mascot & Wordmark
- **Kosh Mascot (`Kosh.tsx`):**
  - Original soft-3D SVG shield-coin character with glossy gradient (`#8fb4ff → #3b78d8 → #2556b8`), white faceplate, oval eyes, rosy cheeks, and ground shadow.
  - Poses implemented: `smile`, `wow`, `calm`, `peek`, `search`, `document`, `lock`, `offline`, `error`, `celebrate`.
  - 12 avatar variants (pose $\times$ tint).
- **Wordmark (`Wordmark.tsx`):**
  - Geometric lowercase `fdr·portal` in Plus Jakarta Sans 800 with the distinctive blue ring-and-dot mark.
  - Carries `data-testid="wordmark"`.

### 2.5 R5.4 Web Shell (`Navbar.tsx`, `Sidebar.tsx`, `App.tsx`)
- **Desktop (≥ 768px):**
  - TopBar header with `fdr·portal` wordmark, portal title, ⌘K search trigger, thin black `progress-ink` line showing profile completion from `/v1/me/profile-completion`, realtime SSE connection indicator (`data-testid="sse-status-indicator"`), notification bell with unread dot, language selector combobox (EN/हिंदी/தமிழ்), read-only role pill (`data-testid="role-pill"`), and sign-out.
  - Floating sidebar card on the left with pill navigation buttons matching the 12 primary routes with Phosphor duotone azure icons and capsule active states.
  - Main viewport container on the lavender canvas.
- **Mobile (< 768px):**
  - Sidebar hidden.
  - Fixed `FloatingTabBar` (`data-testid="floating-tab-bar"`) anchored at the bottom with 12px inset, role-aware tabs, and bottom content padding to prevent clipping.

### 2.6 R5.5 Screen Styling & Live Data Verification
- Cleaned up inline styles and eliminated raw hex colors across:
  - `KPIBoard.tsx` (hero banner, lifecycle tiles with container tokens, evidence tier cards, active register table).
  - `NewFDRSubmission.tsx` (drag-and-drop card with dashed azure border and upload button).
  - `SecurityView.tsx` (profile completion card, two-step verification, active sessions list).
  - `LoginScreen.tsx`, `MfaEnrolmentWizard.tsx`, `StepUpContext.tsx`.

---

## 3. Verification & Exit Gates

| Check / Gate | Target | Result | Evidence |
|---|---|---|---|
| **Design Contract Tests** | 10/10 assertions pass | **PASS** | `pnpm --filter web test` (10/10 green in `DesignContract.test.tsx`) |
| **All Web Tests** | 3 suites, 29 tests | **PASS** | 29/29 tests pass (`DesignContract`, `Showcase`, `App`) |
| **Tokens Parity & Contrast** | 96 parity, 192 WCAG | **PASS** | `python3 -I design/check_tokens.py` (192 contrast OK, 96 parity OK) |
| **No Raw Colours Lint** | 0 hex violations | **PASS** | `node scripts/no-raw-colour.mjs apps/web/src` exits 0 |
| **Forbidden Strings Lint** | 0 violations | **PASS** | `node scripts/forbidden-strings.mjs` exits 0 |
| **No Business Literals** | 0 violations | **PASS** | `node scripts/no-business-literals.mjs` exits 0 |
| **Web Production Build** | Clean bundle | **PASS** | `pnpm --filter web build` builds in 10.53s, 0 errors |
| **Monorepo Tests** | Full workspace | **PASS** | `pnpm -r test` exits 0 across all 8 workspace projects |
| **Platform Verify (`make verify`)** | All gates green | **PASS** | 625 backend tests, 17 prod guard tests, audit chain 0 errors |

---

## 4. Conclusion & Hand-off to Stream R6

Stream R5 is **100% COMPLETE**. The web application and design system are locked down and fully verified. Next milestone is **Stream R6: Mobile app** (`apps/mobile`), upgrading the Expo app to the headless `FloatingTabBar`, role-based screens, and Maestro E2E test flows.
