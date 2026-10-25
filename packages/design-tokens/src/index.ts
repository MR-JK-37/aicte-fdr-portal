import * as tokens from '../../../design/tokens';

export * from '../../../design/tokens';

export const m3Shape = tokens.radius;

export const touchTarget = {
  android: tokens.size.tapAndroid,
  ios: tokens.size.tapIos,
};

function enrichTone<T extends Record<string, string>>(tone: T) {
  return {
    ...tone,
    bg: tone.canvas,
    surfaceHigh: tone.surfaceMuted,
    accent: tone.azure,
    accentContainer: tone.primaryContainer,
    onAccent: tone.onPrimary,
    onAccentContainer: tone.onPrimaryContainer,
    outlineVariant: tone.hairline,
  };
}

export const light = enrichTone(tokens.light);
export const dark = enrichTone(tokens.dark);
export const m3Light = enrichTone(tokens.m3Light);
export const m3Dark = enrichTone(tokens.m3Dark);
