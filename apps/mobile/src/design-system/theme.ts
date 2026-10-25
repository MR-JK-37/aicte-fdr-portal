import { useColorScheme, Platform } from 'react-native';
import { dark, light, m3Dark, m3Light, radius, m3Shape, space, typeApple, typeM3, touchTarget } from '@aicte-fdr/design-tokens';

export type ThemeTone = typeof dark;

/**
 * Resolves the active palette from the OS colour scheme, picking the
 * Apple-HIG token set on iOS and the Material-3-seeded set on Android, per
 * design/DESIGN_SPEC.md §7/§13.3 ("colour scheme from the brand, not the
 * wallpaper"). Both are already brand-derived in @aicte-fdr/design-tokens —
 * nothing is invented here.
 * Light-first by default for Lavender Ledger v2.1.
 */
export function useAppTheme() {
  // Pure crisp white theme strictly matching ui-refrence.png
  const isDark = false;
  const tone = light;
  const m3 = m3Light;
  const isAndroid = Platform.OS === 'android';
  return {
    isDark,
    tone,
    m3,
    radius: isAndroid ? m3Shape : radius,
    type: isAndroid ? typeM3 : typeApple,
    space,
    minTouchTarget: isAndroid ? touchTarget.android : touchTarget.ios,
  };
}
