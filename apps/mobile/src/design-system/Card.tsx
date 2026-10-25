import React from 'react';
import { View, StyleSheet, Platform, type ViewProps } from 'react-native';
import { useAppTheme } from './theme';

export interface CardProps extends ViewProps {
  elevated?: boolean;
}

/**
 * Lavender Ledger Card — Solid content surface, radius 20, soft shadow, no 1px border.
 * (DESIGN_SPEC §4, §5.4, §9)
 */
export function Card({ elevated, style, ...rest }: CardProps) {
  const { tone, isDark } = useAppTheme();
  return (
    <View
      style={[
        styles.base,
        {
          backgroundColor: elevated
            ? tone.surfaceHigh
            : isDark
            ? tone.surface
            : '#ffffff',
          shadowColor: '#1e1b4b',
          shadowOffset: { width: 0, height: elevated ? 4 : 2 },
          shadowOpacity: isDark ? 0.25 : 0.05,
          shadowRadius: elevated ? 12 : 8,
          elevation: elevated ? 4 : 2,
        },
        style,
      ]}
      {...rest}
    />
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: 20,
    borderWidth: 0,
    padding: 16,
  },
});
