# DESIGN_SPEC.md — AICTE FDR Portal

Authoritative design rules for web, iOS and Android. Tokens: `tokens.css`, `tokens.ts` (verified by `check_tokens.py`). Summary in `docs/MASTER_PROMPT.md` §13. If a platform API named here does not exist in the pinned version, follow the stated fallback and record it in `docs/STACK_LOCK.md`.

## 1. Intent
A calm, authoritative, government-grade financial-compliance tool that feels native on each platform:
- **Web + iOS:** Apple Human Interface Guidelines — clarity, deference to content, depth; Liquid Glass for the navigation/control layer.
- **Android:** Material Design 3 (Expressive where verified) with Material Symbols for every icon.
- It must never look like a template or generated UI. Restraint, hierarchy, alignment, and real content states carry the quality — not decoration.

## 2. Colour (dark is the hero theme; light follows the system)
Base `#050505`, violet `#3b0a6b`, cyan `#00eeff`. Violet is for **fills, tint, selected-row wash, glass tinting and glows** — never text or icon colour on the dark base (1.40:1).

| Pair (dark) | Ratio | Use |
|---|---|---|
| `#f0f0f0` on `#050505` / on `#2c292d` | 17.88 / 12.60 | Primary text |
| `#b9b9b9` on `#050505` / `#2c292d` | 10.39 / 7.32 | Secondary text |
| `#919191` on `#050505` / `#2c292d` | 6.47 / 4.56 | Tertiary text (AA minimum — never go darker than this on dark surfaces) |
| `#646464` | — | Disabled/decorative only (never informative) |
| `#00eeff` on `#050505` / `#2c292d` | 14.24 / 10.04 | Accent text, icons, focus ring |
| `#00363b` on `#00eeff` | 9.22 | Text/icon on cyan fills (buttons, chips) |
| `#84f3ff` on `#004f55` | 7.22 | Tonal accent container |
| `#eedbff` on `#3b0a6b` | 11.25 | Text on violet container |
| `#958e98` on `#050505` | 6.41 | Control borders (≥3:1 required, met) |
| `#4a454e` on `#050505` | 2.19 | Hairlines/dividers only (decorative) |

Status colours (dark): ok `#3ddc97`, warn `#ffb020`, info `#7aa7ff`, error `#ff5c7a`, pending `#b69cff`, neutral `#9aa0ad` (≥4.5:1 on all dark surfaces). Light-theme counterparts are darker (ok `#0b6b45`, warn `#8a5a00`, info `#1f4fb3`, error `#b3123a`, pending `#5b3fb0`, neutral `#555b66`; ≥5.6:1 on `#fef7fc`). **Status is never colour alone** — always icon + text label.

Surfaces (tonal elevation, dark): `#050505` base → `#0f0d11` → `#151316` → `#1d1b1e` → `#211f22` → `#2c292d`. Light: `#fef7fc` → `#f8f1f6` → `#f2ebf0` → `#ece5ea` → `#e7e0e5`.
Elevation on dark is expressed by tonal steps and hairlines, not heavy shadows.

## 3. Typography
- Web/iOS: SF Pro on Apple devices via the system stack (never self-host SF on the web); **Inter** (OFL, self-hosted, subset) as the non-Apple fallback; Noto Sans Devanagari / Noto Sans Tamil for Indic scripts. Sizes per `typeApple`. Tabular numerals for money, dates, counts. Monospace for identifiers (FDR no., UTR) with grouping (e.g. `XXXX 1234`).
- Android: Roboto / Roboto Flex, scale per `typeM3`. Respect user font scale up to 200% — layouts must reflow, never clip.
- Indian number grouping for ₹ (1,00,00,000) via `Intl.NumberFormat('en-IN')` / locale equivalents. Amounts right-aligned in tables with currency symbol in the header, not each cell, unless mixed currency.

## 4. Layout
- 4-pt grid. Content max width 1280 px for reading screens; tables use full width with sticky header and column chooser.
- Web: left sidebar (glass, 264 px, collapsible to 72 px) + toolbar (glass) + content on solid surfaces. Dense tables: 36 px rows on pointer, 44 px on touch. Detail screens: summary header (identity, state chips, key dates) → tabs → content; a right-hand "provenance & activity" drawer is available everywhere.
- Phone: single column, sticky primary action, cards for list rows (title, state chip, two key facts, chevron), full detail on tap.
- Tablet/foldable/desktop: list-detail panes; Android uses window-size classes (compact/medium/expanded); iPad uses adaptable sidebar/tab bar.
- Forms: label above input, helper text below, inline validation on blur, error summary at top for long forms, never placeholder-as-label.

## 5. Component inventory (build once per platform; same semantics)
Buttons (filled/tonal/outline/text/destructive), icon buttons, chips (filter/assist/status), evidence-attribute chips (shape+icon+label), inputs (text, amount with ₹ prefix, date, select, search, file), segmented control, tabs, list rows, cards (content, solid), tables (sortable, virtualised), data-diff view (before/after per field), **timeline** (state transitions with actor/reason), **provenance drawer**, **checklist table** (SATISFIED / NOT SATISFIED / PENDING SOURCE / NOT APPLICABLE), document viewer (zoom/rotate/pages) + extraction overlay, toast/snackbar, banner (degraded/unconfigured/staging), dialog/sheet/popover, step-up auth sheet, empty state (icon + 1 line + 1 action), skeletons, progress (determinate for uploads), badge counts, avatar (initials only, no stock photos), date range picker, command palette (web), pull-to-refresh (mobile).
Mandatory states for every data view: loading, empty, error (with correlation ID), forbidden, offline/unavailable, stale-version conflict.

## 6. Liquid Glass — web and iOS
**Where:** sidebar, top toolbar, bottom tab bar (iOS), floating action cluster, popovers/menus, sheet grabber area, segmented controls, toasts.
**Where not:** tables, cards, forms, document viewer, charts, anything the user reads at length. Do not stack glass on glass. At most ~3 glass surfaces visible at once.
**Variants:** *regular* (default, adaptive legibility) — use for almost everything. *clear* (more transparent) only over rich media with a dimming layer; this app has little media, so avoid.
**Web recipe:** see `.glass` in `tokens.css` — `backdrop-filter: blur(24px) saturate(180%)` (+`-webkit-`), translucent tint via `color-mix`, 1 px border, inner top highlight, soft shadow. Optional enhancements (feature-detected, never required): SVG `feDisplacementMap` edge refraction (Chromium only), `-apple-visual-effect` on iOS 26 Safari behind `@supports` (verify). Fallbacks: `@supports not (backdrop-filter…)`, `prefers-reduced-transparency`, `prefers-contrast: more`, and an in-app "Reduce transparency" toggle (`data-reduce-transparency`) all produce opaque surfaces with a visible border. Test scroll performance on a mid-range Android phone; if frame drops occur, reduce blur radius or switch the surface to solid.
**iOS native:** `expo-glass-effect` (`GlassView`/container with `glassEffectStyle: 'regular'`) on iOS 26+; below iOS 26 use system material blur with the same tint tokens; honour Reduce Transparency (`AccessibilityInfo.isReduceTransparencyEnabled`). Tab bar via Expo Router native tabs (system Liquid Glass tab bar, minimise on scroll). Verify prop names in the pinned SDK (spike S-03).

## 7. Material 3 on Android
- Components from `@expo/ui/jetpack-compose` where available (spike S-02); otherwise faithful implementations: state layers (8/10/16% hover/focus/press), ripple, tonal elevation, shapes (`m3Shape`), predictive back, edge-to-edge insets.
- Navigation: NavigationBar (compact) → NavigationRail (medium/expanded) → permanent drawer on very wide screens; top app bar small/medium/large with scroll collapse; FAB/extended FAB only for the single primary create action per screen; bottom sheets and snackbars for transient flows.
- **Colour:** brand-seeded `m3Dark` / `m3Light` (no wallpaper dynamic colour by default; optional off-by-default setting "Use device colours").
- **Expressive:** adopt expressive motion (spring), shape and typography emphasis only if the pinned Compose Material 3 / `@expo/ui` exposes it; otherwise standard M3. Never fake it with ad-hoc animations.
- **Material Symbols only.** Android notification small icon is also a Material Symbol exported as a monochrome drawable. Default style Outlined, weight 400, grade 0, optical size 24; FILL=1 for selected state. Include the Apache-2.0 notice in About → Licences.

## 8. Icons — one logical key set, three renderers
Components reference logical keys only; a platform map resolves them. **Verify each symbol exists in the pinned icon packs/SF Symbols app** (record gaps in `docs/STACK_LOCK.md`).

| Logical key | Material Symbols (Android) | SF Symbols (iOS) | Web (Lucide/Phosphor; spike picks one) |
|---|---|---|---|
| dashboard | `dashboard` | `square.grid.2x2` | LayoutDashboard |
| institution | `account_balance` | `building.columns` | Landmark |
| instrument | `description` | `doc.text` | FileText |
| documents | `folder_open` | `folder` | FolderOpen |
| verified (bank-confirmed) | `verified` | `checkmark.seal` | BadgeCheck |
| checklist | `fact_check` | `checklist` | ListChecks |
| notifications | `notifications` | `bell` | Bell |
| notifications_active | `notifications_active` | `bell.badge` | BellRing |
| deadline | `schedule` | `clock` | Clock |
| calendar | `calendar_month` | `calendar` | Calendar |
| inbox | `inbox` | `tray` | Inbox |
| search | `search` | `magnifyingglass` | Search |
| filter | `filter_list` | `line.3.horizontal.decrease` | ListFilter |
| upload | `upload_file` | `arrow.up.doc` | FileUp |
| scan | `document_scanner` | `doc.viewfinder` | ScanLine |
| qr | `qr_code_scanner` | `qrcode.viewfinder` | QrCode |
| lock | `lock` | `lock` | Lock |
| biometric | `fingerprint` | `faceid` | Fingerprint |
| security | `shield` | `shield` | Shield |
| history | `history` | `clock.arrow.circlepath` | History |
| settings | `settings` | `gearshape` | Settings |
| profile | `person` | `person` | User |
| sign_out | `logout` | `rectangle.portrait.and.arrow.right` | LogOut |
| warning | `warning` | `exclamationmark.triangle` | TriangleAlert |
| error | `error` | `xmark.octagon` | OctagonX |
| success | `check_circle` | `checkmark.circle` | CircleCheck |
| failed | `cancel` | `xmark.circle` | CircleX |
| pending | `hourglass_top` | `hourglass` | Hourglass |
| sync | `sync` | `arrow.triangle.2.circlepath` | RefreshCw |
| offline | `cloud_off` | `icloud.slash` | CloudOff |
| link (ledger) | `link` | `link` | Link |
| declared | `edit_note` | `square.and.pencil` | FilePenLine |
| help | `help` | `questionmark.circle` | CircleHelp |
| blocked | `block` | `nosign` | Ban |
| receipt | `receipt_long` | `doc.plaintext` | Receipt |
| report | `bar_chart` | `chart.bar` | ChartBar |
| download | `download` | `arrow.down.circle` | Download |
| share | `share` | `square.and.arrow.up` | Share |
| add | `add` | `plus` | Plus |
| language | `translate` | `globe` | Languages |
| devices | `devices` | `iphone` | Smartphone |
| policy | `policy` | `text.book.closed` | BookOpen |
| audit | `manage_search` | `list.bullet.rectangle` | ScrollText |

Rules: no emoji; no mixing sets within a platform; web keeps stroke ≈1.5 px to sit near SF Symbols' weight; SF Symbols never on web/Android; Material Symbols never on iOS/web.

## 9. Motion
Spring-like, 160–320 ms; transitions communicate hierarchy (sheet up, push, tab cross-fade). No parallax, no looping decorative animation. Honour Reduce Motion (replace with fades).

## 10. Content design
Plain, precise, bureaucracy-free English; short sentences; dates as `24 Oct 2026`; amounts as `₹ 35,00,000`; never "AI-powered" marketing copy; never claim certification or verification the system hasn't evidenced. Empty states say what's missing and what the user can do. Error messages say what happened, what is safe, what to do, and show the correlation ID.

## 11. Accessibility acceptance
WCAG 2.1 AA (2.2 target): all text ≥4.5:1, UI/graphics ≥3:1, visible focus, full keyboard path, no focus trap, ARIA only when native semantics are insufficient, screen-reader names include state ("Bank-confirmed, source: State Bank of India letter dated 12 Sep 2026"), reflow at 320 CSS px and 400% zoom, target size ≥44 pt/48 dp, no information by colour alone, motion/transparency/contrast preferences honoured, language attributes set, form errors programmatically associated.

## 12. QA gates (blocking)
`python3 -I design/check_tokens.py` passes · axe-core zero serious/critical · Playwright visual matrix attached · device screenshot matrix attached · `design-reviewer` PASS on every screen listed in the phase.
