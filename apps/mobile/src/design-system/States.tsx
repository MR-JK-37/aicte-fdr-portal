import React from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useAppTheme } from './theme';
import { Icon, type IconName } from './Icon';
import { Button } from './Button';
import { Kosh } from './Kosh';

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  const { tone } = useAppTheme();
  return (
    <View style={styles.state} accessibilityRole="progressbar">
      <ActivityIndicator color={tone.accent} size="large" />
      <Text style={[styles.body, { color: tone.text2 }]}>{label}</Text>
    </View>
  );
}

export interface EmptyStateProps {
  icon?: IconName;
  title: string;
  body?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ icon, title, body, actionLabel, onAction }: EmptyStateProps) {
  const { tone } = useAppTheme();
  return (
    <View style={styles.state}>
      <Kosh pose="search" size={72} />
      {icon && <Icon name={icon} size={24} color={tone.text3} />}
      <Text style={[styles.title, { color: tone.text1 }]}>{title}</Text>
      {body && <Text style={[styles.body, { color: tone.text3 }]}>{body}</Text>}
      {actionLabel && onAction && <Button variant="tonal" label={actionLabel} onPress={onAction} />}
    </View>
  );
}

export interface ErrorStateProps {
  title?: string;
  body?: string;
  correlationId?: string;
  onRetry?: () => void;
}

export function ErrorState({ title = 'Something went wrong', body, correlationId, onRetry }: ErrorStateProps) {
  const { tone } = useAppTheme();
  return (
    <View style={styles.state} accessibilityRole="alert">
      <Kosh pose="error" size={72} />
      <Text style={[styles.title, { color: tone.text1 }]}>{title}</Text>
      {body && <Text style={[styles.body, { color: tone.text3 }]}>{body}</Text>}
      {correlationId && <Text style={[styles.mono, { color: tone.text3 }]}>Correlation ID: {correlationId}</Text>}
      {onRetry && <Button variant="outline" label="Retry" onPress={onRetry} />}
    </View>
  );
}

export interface OfflineStateProps {
  what?: string;
}

export function OfflineState({ what = 'This feature' }: OfflineStateProps) {
  const { tone } = useAppTheme();
  return (
    <View style={styles.state}>
      <Kosh pose="offline" size={72} />
      <Text style={[styles.title, { color: tone.text1 }]}>{what} is temporarily unavailable</Text>
      <Text style={[styles.body, { color: tone.text3 }]}>
        The connected service is not reachable right now. Your data is safe; try again shortly.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  state: { alignItems: 'center', justifyContent: 'center', gap: 12, padding: 32 },
  title: { fontSize: 16, fontWeight: '700', textAlign: 'center' },
  body: { fontSize: 13, textAlign: 'center', lineHeight: 18 },
  mono: { fontFamily: 'monospace', fontSize: 11 },
});
