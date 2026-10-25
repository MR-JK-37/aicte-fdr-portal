import React from 'react';
import { Pressable, Text, StyleSheet, Platform, type GestureResponderEvent } from 'react-native';
import { useAppTheme } from './theme';

export type ButtonVariant = 'filled' | 'tonal' | 'outline' | 'text' | 'destructive';

export interface ButtonProps {
  variant?: ButtonVariant;
  label: string;
  onPress?: (e: GestureResponderEvent) => void;
  disabled?: boolean;
  accessibilityLabel?: string;
}

/**
 * Lavender Ledger Button (DESIGN_SPEC §5.1, §7, §9, §13):
 * - Primary filled: Black Pill (`tone.ink` / `#0f172a`), with white text.
 * - Tonal: `tone.accentContainer` / `primaryContainer`, with `tone.accent` / `azure` text.
 * - Outline: transparent with `tone.outline` border.
 * - Destructive: soft red or `tone.error`.
 */
export function Button({ variant = 'filled', label, onPress, disabled, accessibilityLabel }: ButtonProps) {
  const { tone, m3, isDark, minTouchTarget } = useAppTheme();
  const isAndroid = Platform.OS === 'android';

  const bg = {
    filled: isDark ? '#ffffff' : tone.ink,
    tonal: tone.accentContainer,
    outline: 'transparent',
    text: 'transparent',
    destructive: isDark ? 'rgba(239, 68, 68, 0.2)' : '#fee2e2',
  }[variant];

  const fg = {
    filled: isDark ? '#0f172a' : '#ffffff',
    tonal: isDark ? tone.accent : '#1d4ed8',
    outline: tone.text1,
    text: tone.accent,
    destructive: tone.error,
  }[variant];

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ disabled: !!disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        {
          minHeight: minTouchTarget,
          backgroundColor: bg,
          borderWidth: variant === 'outline' ? 1 : 0,
          borderColor: tone.outline,
          opacity: disabled ? 0.45 : pressed ? (isAndroid ? 0.88 : 0.75) : 1,
        },
      ]}
    >
      <Text style={[styles.label, { color: fg }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    borderRadius: 999,
  },
  label: { fontSize: 15, fontWeight: '600' },
});
