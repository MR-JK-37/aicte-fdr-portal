import React from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useAppTheme } from './theme';
import { Icon, type IconName } from './Icon';
import { Button } from './Button';

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  const { tone } = useAppTheme();
  return (
    <View style={styles.state} accessibilityRole="progressbar">
      <ActivityIndicator color={tone.accent} />
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

export function EmptyState({ icon = 'inbox', title, body, actionLabel, onAction }: EmptyStateProps) {
  const { tone } = useAppTheme();
  return (
    <View style={styles.state}>
      <Icon name={icon} size={32} color={tone.text3} />
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
      <Icon name="error" size={32} color={tone.error} />
      <Text style={[styles.title, { color: tone.text1 }]}>{title}</Text>
      {body && <Text style={[styles.body, { color: tone.text3 }]}>{body}</Text>}
      {correlationId && <Text style={[styles.mono, { color: tone.text3 }]}>Correlation ID: {correlationId}</Text>}
      {onRetry && <Button variant="outline" label="Retry" onPress={onRetry} />}
    </View>
  );
}

export function OfflineState({ what = 'This feature' }: { what?: string }) {
  const { tone } = useAppTheme();
  return (
    <View style={styles.state}>
      <Icon name="offline" size={32} color={tone.text3} />
      <Text style={[styles.title, { color: tone.text1 }]}>{what} is temporarily unavailable</Text>
      <Text style={[styles.body, { color: tone.text3 }]}>The connected service is not reachable right now. Your data is safe; try again shortly.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  state: { alignItems: 'center', justifyContent: 'center', gap: 10, padding: 32 },
  title: { fontSize: 16, fontWeight: '600', textAlign: 'center' },
  body: { fontSize: 13, textAlign: 'center' },
  mono: { fontFamily: 'monospace', fontSize: 11 },
});
