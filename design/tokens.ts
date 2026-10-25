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
  canvasDeep: '#edf2fa', // page backdrop behind the app frame on wide web screens
  canvas: '#f8fafd', // app background
  surface: '#ffffff', // cards, sheets, floating bars
  surfaceMuted: '#f6f8fc', // grouped-list inner wells, table zebra, quote boxes
  field: '#eff2f7', // input / search / segmented-track fill
  fieldStrong: '#e2e7f0', // pressed field, progress track
  hairline: '#e8edf5', // dividers only (decorative)
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
  heroFrom: '#dbe5fc',
  heroTo: '#f9fbfe',
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

/** Evidence attribute presentation (never colour-only: shape + icon + label) */
export const evidenceChip = {
  declared:        { label: 'Institution-declared', shape: 'outlined', iconKey: 'declared' },
  extracted:       { label: 'Document-extracted',   shape: 'dashed',   iconKey: 'scan' },
  bankConfirmed:   { label: 'Bank-confirmed',       shape: 'filled',   iconKey: 'verified' },
  ledgerReconciled:{ label: 'Ledger-reconciled',    shape: 'filled',   iconKey: 'link' },
  inconclusive:    { label: 'Inconclusive',         shape: 'warning',  iconKey: 'help' },
  rejected:        { label: 'Rejected',             shape: 'stop',     iconKey: 'blocked' },
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
