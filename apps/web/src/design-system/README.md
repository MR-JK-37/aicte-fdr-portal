# apps/web design system

Web primitives for AICTE FDR Portal, implementing `design/DESIGN_SPEC.md`
§6/§8/§11/§13 on top of `@aicte-fdr/design-tokens` (CSS custom properties)
and `@aicte-fdr/i18n`.

## Icon set: **Lucide** (`lucide-react`)

Chosen over Phosphor per MASTER_PROMPT §13.2's "spike picks one":
`lucide-react` was already a dependency before this phase, ships
tree-shaken per-icon ES modules, and its default stroke sits close to
1.5px — the weight DESIGN_SPEC §8 asks web icons to approximate relative to
SF Symbols. All icon usage goes through the single `<Icon name="…">`
component in `Icon.tsx`, whose `IconName` is a **closed enum** matching the
logical-key table in `design/DESIGN_SPEC.md` §8 exactly (`dashboard`,
`institution`, `verified`, `declared`, …). Never import `lucide-react` icons
directly outside this file — SF Symbols and Material Symbols must never
appear on web (licence + DESIGN_SPEC §8 rule); routing every icon through
one enum is what makes that enforceable by code review instead of by hope.

## What's here

| File | What |
|---|---|
| `tokens-entry.css` | `@import`s `@aicte-fdr/design-tokens/css/tokens.css` — the only place token CSS variables enter the app |
| `primitives.css` | Component styles, all via `var(--token)` — zero hard-coded colours |
| `theme.tsx` | `<ThemeProvider>`/`useTheme()` — dark/light/system, `data-theme` + `data-reduce-transparency` attrs on `<html>` |
| `Icon.tsx` | Closed-enum Lucide wrapper |
| `Button.tsx` | filled / tonal / outline / text / destructive, icon-only variant |
| `Input.tsx` | `TextInput` (+ `amount` ₹-prefixed variant), `SearchInput`, `Select` — label above, helper below, inline error |
| `Card.tsx` | Solid surface — **never glass** (content layer rule, DESIGN_SPEC §6) |
| `Sidebar.tsx` / `Toolbar.tsx` | Liquid-Glass navigation/control-layer shells, built on the shared `.glass` class in tokens.css (blur+saturate, `-webkit-` prefix, `@supports not (backdrop-filter)` fallback, reduced-transparency/contrast overrides already wired — nothing re-implemented here) |
| `EvidenceChip.tsx` | Declared / Extracted / Bank-confirmed / Ledger-reconciled / Inconclusive / Rejected — distinct shape + icon + label per attribute, never colour alone |
| `StatusBadge.tsx` | ok/warn/info/error/pending/neutral — icon + text always |
| `States.tsx` | `LoadingState`, `EmptyState`, `ErrorState` (shows correlation ID), `ForbiddenState`, `OfflineState` |
| `DesignSystemShowcase.tsx` | Dev-only `/_design-system` route rendering every primitive, both themes, en/hi/ta — see below |

## Showcase route

`main.tsx` renders `<DesignSystemShowcase />` instead of `<App />` when
`location.pathname` starts with `/_design-system`. It is not linked from any
navigation — visit it directly (`pnpm --filter web dev`, then
`http://localhost:3000/_design-system`). Toggle theme / reduce-transparency
/ locale from the controls at the top; this is what `design-reviewer` and
humans should look at before any real screen exists.

## Known deviation to track

`design/tokens.css` includes a `@theme inline { … }` block, which is
**Tailwind v4** syntax. `apps/web` is currently pinned to Tailwind v3.4 (pre-
existing, not changed by this phase). The primitives above therefore read
CSS custom properties directly (`var(--bg)`, etc.) via plain CSS classes
rather than through Tailwind's v4 `@theme` token mapping — Tailwind utility
classes (`flex`, `gap-*`, …) still work fine for layout under v3. If/when
the repo upgrades to Tailwind v4, `@theme inline` in tokens.css becomes
usable directly and `primitives.css`'s token usage can migrate to Tailwind
utilities if desired; this is a deliberate, documented deferral, not a bug.
