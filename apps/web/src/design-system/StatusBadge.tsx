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
}

/** Status is never colour alone (DESIGN_SPEC §2/§13.1): icon + text label always. */
export function StatusBadge({ tone, label }: StatusBadgeProps) {
  return (
    <span className={`ds-status-badge ds-status-badge--${tone}`}>
      <Icon name={TONE_ICON[tone]} size={14} />
      {label}
    </span>
  );
}
