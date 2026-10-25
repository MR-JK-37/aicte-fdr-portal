import React from 'react';
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
  className?: string;
}

/** Status is never colour alone (DESIGN_SPEC §2): icon + text label always. */
export function StatusBadge({ tone, label, className = '' }: StatusBadgeProps) {
  return (
    <span className={`pill pill-${tone} ${className}`} data-testid="status-badge">
      <Icon name={TONE_ICON[tone]} size={13} />
      <span>{label}</span>
    </span>
  );
}
