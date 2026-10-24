/**
 * tokens.ts — AICTE FDR Portal design tokens for web (TS) and React Native (iOS + Android).
 * Mirrors tokens.css. `design/check_tokens.py` verifies parity and contrast in CI.
 * Brand: #050505 base · #3b0a6b violet (fills/tint only; 1.40:1 on base) · #00eeff cyan accent.
 */

export const brand = { base: '#050505', violet: '#3b0a6b', cyan: '#00eeff' } as const;

export const dark = {
  bg: '#050505',
  surfaceLow: '#0f0d11',
  surface: '#151316',
  surfaceHigh: '#1d1b1e',
  surfaceHigher: '#211f22',
  surfaceHighest: '#2c292d',
  stateHover: '#373438',
  text1: '#f0f0f0',
  text2: '#b9b9b9',
  text3: '#919191',
  textDisabled: '#646464', // decorative / disabled only
  onSurface: '#e7e1e5',
  onSurfaceVariant: '#ccc4cf',
  outline: '#958e98',
  outlineVariant: '#4a454e', // hairlines only
  accent: '#00eeff',
  onAccent: '#00363b',
  accentContainer: '#004f55',
  onAccentContainer: '#84f3ff',
  violetContainer: '#3b0a6b',
  onVioletContainer: '#eedbff',
  secondary: '#dab9ff',
  tertiary: '#f2b7c0',
  ok: '#3ddc97', warn: '#ffb020', info: '#7aa7ff', error: '#ff5c7a', pending: '#b69cff', neutral: '#9aa0ad',
} as const;

export const light = {
  bg: '#fef7fc',
  surfaceLow: '#f8f1f6',
  surface: '#f2ebf0',
  surfaceHigh: '#ece5ea',
  surfaceHigher: '#e9e2e7',
  surfaceHighest: '#e7e0e5',
  stateHover: '#ded8dd',
  text1: '#1d1b1e',
  text2: '#4a454e',
  text3: '#615d61',
  textDisabled: '#948f94',
  onSurface: '#1d1b1e',
  onSurfaceVariant: '#4a454e',
  outline: '#7b757f',
  outlineVariant: '#ccc4cf',
  accent: '#006971',
  onAccent: '#ffffff',
  accentContainer: '#84f3ff',
  onAccentContainer: '#002023',
  violetContainer: '#eedbff',
  onVioletContainer: '#2a0053',
  secondary: '#734aa5',
  tertiary: '#805159',
  ok: '#0b6b45', warn: '#8a5a00', info: '#1f4fb3', error: '#b3123a', pending: '#5b3fb0', neutral: '#555b66',
} as const;

/** Material 3 colour scheme (Android). Brand-seeded, NOT wallpaper-derived. Map 1:1 to Compose ColorScheme. */
export const m3Dark = {
  primary: '#00eeff', onPrimary: '#00363b', primaryContainer: '#004f55', onPrimaryContainer: '#84f3ff',
  secondary: '#dab9ff', onSecondary: '#431673', secondaryContainer: '#3b0a6b', onSecondaryContainer: '#eedbff',
  tertiary: '#f2b7c0', onTertiary: '#4b252c', tertiaryContainer: '#653b42', onTertiaryContainer: '#ffd9de',
  error: '#ffb4ab', onError: '#690005', errorContainer: '#93000a', onErrorContainer: '#ffdad6',
  background: '#050505', onBackground: '#e7e1e5',
  surface: '#050505', onSurface: '#e7e1e5', surfaceVariant: '#4a454e', onSurfaceVariant: '#ccc4cf',
  outline: '#958e98', outlineVariant: '#4a454e', scrim: '#000000',
  inverseSurface: '#e7e1e5', inverseOnSurface: '#322f33', inversePrimary: '#006971',
  surfaceDim: '#050505', surfaceBright: '#373438',
  surfaceContainerLowest: '#000000', surfaceContainerLow: '#0f0d11', surfaceContainer: '#151316',
  surfaceContainerHigh: '#211f22', surfaceContainerHighest: '#2c292d',
} as const;

export const m3Light = {
  primary: '#006971', onPrimary: '#ffffff', primaryContainer: '#84f3ff', onPrimaryContainer: '#002023',
  secondary: '#734aa5', onSecondary: '#ffffff', secondaryContainer: '#eedbff', onSecondaryContainer: '#2a0053',
  tertiary: '#805159', onTertiary: '#ffffff', tertiaryContainer: '#ffd9de', onTertiaryContainer: '#321018',
  error: '#ba1a1a', onError: '#ffffff', errorContainer: '#ffdad6', onErrorContainer: '#410002',
  background: '#fef7fc', onBackground: '#1d1b1e',
  surface: '#fef7fc', onSurface: '#1d1b1e', surfaceVariant: '#e8e0eb', onSurfaceVariant: '#4a454e',
  outline: '#7b757f', outlineVariant: '#ccc4cf', scrim: '#000000',
  inverseSurface: '#322f33', inverseOnSurface: '#f5eff4', inversePrimary: '#00eeff',
  surfaceDim: '#ded8dd', surfaceBright: '#fef7fc',
  surfaceContainerLowest: '#ffffff', surfaceContainerLow: '#f8f2f7', surfaceContainer: '#f2ecf1',
  surfaceContainerHigh: '#ede6eb', surfaceContainerHighest: '#e7e1e5',
} as const;

/** Shapes */
export const radius = { xs: 8, sm: 12, md: 16, lg: 22, xl: 28, full: 999 } as const; // Apple-style (web, iOS)
export const m3Shape = { none: 0, xs: 4, sm: 8, md: 12, lg: 16, xl: 28, full: 999 } as const; // Material 3 (Android)

/** 4-pt spacing */
export const space = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48, 16: 64 } as const;

/** iOS / web type scale (pt/px) — HIG-like */
export const typeApple = {
  largeTitle: { size: 34, weight: '700', line: 41 },
  title1: { size: 28, weight: '700', line: 34 },
  title2: { size: 22, weight: '700', line: 28 },
  title3: { size: 20, weight: '600', line: 25 },
  headline: { size: 17, weight: '600', line: 22 },
  body: { size: 17, weight: '400', line: 22 },
  callout: { size: 16, weight: '400', line: 21 },
  subhead: { size: 15, weight: '400', line: 20 },
  footnote: { size: 13, weight: '400', line: 18 },
  caption: { size: 12, weight: '400', line: 16 },
} as const;

/** Material 3 type scale (sp) — Roboto / Roboto Flex */
export const typeM3 = {
  displayLarge: { size: 57, line: 64, weight: '400' }, displayMedium: { size: 45, line: 52, weight: '400' }, displaySmall: { size: 36, line: 44, weight: '400' },
  headlineLarge: { size: 32, line: 40, weight: '400' }, headlineMedium: { size: 28, line: 36, weight: '400' }, headlineSmall: { size: 24, line: 32, weight: '400' },
  titleLarge: { size: 22, line: 28, weight: '400' }, titleMedium: { size: 16, line: 24, weight: '500' }, titleSmall: { size: 14, line: 20, weight: '500' },
  bodyLarge: { size: 16, line: 24, weight: '400' }, bodyMedium: { size: 14, line: 20, weight: '400' }, bodySmall: { size: 12, line: 16, weight: '400' },
  labelLarge: { size: 14, line: 20, weight: '500' }, labelMedium: { size: 12, line: 16, weight: '500' }, labelSmall: { size: 11, line: 16, weight: '500' },
} as const;

export const touchTarget = { ios: 44, android: 48, webPointer: 36, webTouch: 44 } as const;

export const motion = {
  fastMs: 160, baseMs: 240, slowMs: 320,
  easeSpring: [0.22, 1, 0.36, 1] as const,
} as const;

/** Glass (iOS 26+ via expo-glass-effect; web via CSS). Content layer must never use glass. */
export const glass = {
  blur: 24, saturate: 1.8,
  tintDark: 'rgba(29,27,30,0.58)', tintLight: 'rgba(254,247,252,0.62)',
  borderDark: 'rgba(255,255,255,0.10)', borderLight: 'rgba(29,27,30,0.10)',
  solidFallbackDark: '#1d1b1e', solidFallbackLight: '#f2ebf0',
} as const;

/** Evidence attribute presentation (never colour-only: shape + icon + label) */
export const evidenceChip = {
  declared:        { label: 'Institution-declared', shape: 'outlined', iconKey: 'edit_note' },
  extracted:       { label: 'Document-extracted',   shape: 'dashed',   iconKey: 'document_scanner' },
  bankConfirmed:   { label: 'Bank-confirmed',       shape: 'filled',   iconKey: 'verified' },
  ledgerReconciled:{ label: 'Ledger-reconciled',    shape: 'filled',   iconKey: 'link' },
  inconclusive:    { label: 'Inconclusive',         shape: 'warning',  iconKey: 'help' },
  rejected:        { label: 'Rejected',             shape: 'stop',     iconKey: 'block' },
} as const;
// iconKey is a logical key. Map per platform: Material Symbols name (Android), SF Symbol name (iOS), open-set icon (web).

export type Theme = typeof dark;
