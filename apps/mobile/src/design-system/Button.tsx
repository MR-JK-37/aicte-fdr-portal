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
 * Hand-built (not from `@expo/ui`) — buttons are not one of the gaps S-02
 * flagged, but the universal `@expo/ui` Button doesn't expose M3 state
 * layers (hover/focus/press 8/10/16%) distinctly from HIG press styling,
 * so a platform-aware hand implementation matches DESIGN_SPEC §7/§13
 * metrics more faithfully than the cross-platform default would.
 */
export function Button({ variant = 'filled', label, onPress, disabled, accessibilityLabel }: ButtonProps) {
  const { tone, m3, minTouchTarget } = useAppTheme();
  const isAndroid = Platform.OS === 'android';

  const bg = {
    filled: isAndroid ? m3.primary : tone.accent,
    tonal: isAndroid ? m3.primaryContainer : tone.accentContainer,
    outline: 'transparent',
    text: 'transparent',
    destructive: isAndroid ? m3.error : tone.error,
  }[variant];

  const fg = {
    filled: isAndroid ? m3.onPrimary : tone.onAccent,
    tonal: isAndroid ? m3.onPrimaryContainer : tone.onAccentContainer,
    outline: tone.text1,
    text: isAndroid ? m3.primary : tone.accent,
    destructive: isAndroid ? m3.onError : tone.bg,
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
