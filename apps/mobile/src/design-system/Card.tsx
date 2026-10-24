import React from 'react';
import { View, StyleSheet, type ViewProps } from 'react-native';
import { useAppTheme } from './theme';

export interface CardProps extends ViewProps {
  elevated?: boolean;
}

/** Solid content surface — never glass (DESIGN_SPEC §6: glass is nav/control layer only). */
export function Card({ elevated, style, ...rest }: CardProps) {
  const { tone } = useAppTheme();
  return (
    <View
      style={[
        styles.base,
        { backgroundColor: elevated ? tone.surfaceHigh : tone.surface, borderColor: tone.outlineVariant },
        style,
      ]}
      {...rest}
    />
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 16, borderWidth: 1, padding: 16 },
});
