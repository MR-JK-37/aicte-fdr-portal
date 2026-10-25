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
