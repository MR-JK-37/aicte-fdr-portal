import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useAppTheme } from './theme';
import { Icon, type IconName } from './Icon';

export type StatusTone = 'ok' | 'warn' | 'info' | 'error' | 'pending' | 'neutral';

const TONE_ICON: Record<StatusTone, IconName> = {
  ok: 'success',
  warn: 'warning',
  info: 'help',
  error: 'failed',
  pending: 'pending',
  neutral: 'sync',
};

export interface StatusBadgeProps {
  tone: StatusTone;
  label: string;
}

/** Status is never colour alone: icon + text label always. */
export function StatusBadge({ tone: statusTone, label }: StatusBadgeProps) {
  const { tone } = useAppTheme();
  const bg = { ok: tone.ok, warn: tone.warn, info: tone.info, error: tone.error, pending: tone.pending, neutral: tone.neutral }[statusTone];
  return (
    <View style={[styles.badge, { backgroundColor: `${bg}26` }]}>
      <Icon name={TONE_ICON[statusTone]} size={14} color={bg} />
      <Text style={[styles.label, { color: bg }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { flexDirection: 'row', alignItems: 'center', gap: 4, height: 24, paddingHorizontal: 8, borderRadius: 8 },
  label: { fontSize: 12, fontWeight: '600' },
});
