import React from 'react';
import { Icon, type IconName } from './Icon';
import { Button } from './Button';

export function LoadingState({ label }: { label?: string }) {
  return (
    <div className="ds-state" role="status" aria-live="polite">
      <div className="ds-spinner" />
      <span className="ds-state__body">{label ?? 'Loading…'}</span>
    </div>
  );
}

export interface EmptyStateProps {
  icon?: IconName;
  title: string;
  body?: string;
  actionLabel?: string;
  onAction?: () => void;
}

/** Empty state: icon + 1 line + 1 action, per DESIGN_SPEC §5. */
export function EmptyState({ icon = 'inbox', title, body, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="ds-state">
      <Icon name={icon} size={32} />
      <span className="ds-state__title">{title}</span>
      {body && <span className="ds-state__body">{body}</span>}
      {actionLabel && onAction && (
        <Button variant="tonal" onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}

export interface ErrorStateProps {
  title?: string;
  body?: string;
  correlationId?: string;
  onRetry?: () => void;
}

/** Error state always shows a correlation ID (CLAUDE.md non-negotiable #9 / DESIGN_SPEC §10). */
export function ErrorState({ title = 'Something went wrong', body, correlationId, onRetry }: ErrorStateProps) {
  return (
    <div className="ds-state" role="alert">
      <Icon name="error" size={32} />
      <span className="ds-state__title">{title}</span>
      {body && <span className="ds-state__body">{body}</span>}
      {correlationId && <span className="ds-state__correlation">Correlation ID: {correlationId}</span>}
      {onRetry && <Button variant="outline" onClick={onRetry}>Retry</Button>}
    </div>
  );
}

export function ForbiddenState() {
  return (
    <div className="ds-state" role="alert">
      <Icon name="lock" size={32} />
      <span className="ds-state__title">You do not have access to this</span>
      <span className="ds-state__body">Ask your administrator to grant the right permission and scope, then try again.</span>
    </div>
  );
}

export function OfflineState({ what = 'This feature' }: { what?: string }) {
  return (
    <div className="ds-state" role="status">
      <Icon name="offline" size={32} />
      <span className="ds-state__title">{what} is temporarily unavailable</span>
      <span className="ds-state__body">The connected service is not reachable right now. Your data is safe; try again shortly.</span>
    </div>
  );
}
