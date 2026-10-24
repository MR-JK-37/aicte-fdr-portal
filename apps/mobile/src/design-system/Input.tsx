import React, { useState } from 'react';
import { View, Text, TextInput as RNTextInput, StyleSheet, type TextInputProps as RNTextInputProps } from 'react-native';
import { useAppTheme } from './theme';

export interface TextInputProps extends Omit<RNTextInputProps, 'style'> {
  label?: string;
  helperText?: string;
  errorText?: string;
  /** ₹ amount field — shows the currency prefix, tabular numerals, numeric keyboard. */
  amount?: boolean;
}

export function TextInput({ label, helperText, errorText, amount, ...rest }: TextInputProps) {
  const { tone } = useAppTheme();
  const [focused, setFocused] = useState(false);
  return (
    <View style={styles.field}>
      {label && <Text style={[styles.label, { color: tone.text2 }]}>{label}</Text>}
      <View
        style={[
          styles.wrap,
          { backgroundColor: tone.surfaceHigh, borderColor: errorText ? tone.error : focused ? tone.accent : tone.outlineVariant },
        ]}
      >
        {amount && <Text style={[styles.affix, { color: tone.text3 }]}>₹</Text>}
        <RNTextInput
          style={[styles.input, { color: tone.text1 }]}
          placeholderTextColor={tone.text3}
          keyboardType={amount ? 'decimal-pad' : rest.keyboardType}
          onFocus={(e) => { setFocused(true); rest.onFocus?.(e); }}
          onBlur={(e) => { setFocused(false); rest.onBlur?.(e); }}
          accessibilityLabel={rest.accessibilityLabel ?? label}
          {...rest}
        />
      </View>
      {errorText ? (
        <Text style={[styles.helper, { color: tone.error }]} accessibilityRole="alert">{errorText}</Text>
      ) : helperText ? (
        <Text style={[styles.helper, { color: tone.text3 }]}>{helperText}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  field: { gap: 4 },
  label: { fontSize: 13, fontWeight: '600' },
  wrap: { flexDirection: 'row', alignItems: 'center', gap: 8, height: 44, paddingHorizontal: 12, borderRadius: 12, borderWidth: 1 },
  affix: { fontSize: 16, fontVariant: ['tabular-nums'] },
  input: { flex: 1, fontSize: 16 },
  helper: { fontSize: 12 },
});
