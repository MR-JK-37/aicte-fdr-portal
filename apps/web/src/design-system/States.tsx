import React from 'react';
import { Icon, type IconName } from './Icon';
import { Button } from './Button';
import { Kosh, type KoshPose } from './Kosh';

export function LoadingState({ label }: { label?: string }) {
  return (
    <div className="empty" role="status" aria-live="polite">
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: '50%',
          border: '3px solid var(--field-strong, #e1e6f8)',
          borderTopColor: 'var(--azure, #3b78d8)',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      <p>{label ?? 'Loading…'}</p>
    </div>
  );
}

export interface EmptyStateProps {
  icon?: IconName;
  koshPose?: KoshPose;
  title: string;
  body?: string;
  actionLabel?: string;
  onAction?: () => void;
}

/**
 * Empty state: always contains Kosh mascot (calm pose), bold title, explanatory body, and optional action.
 * (DESIGN_SPEC §5 / §8)
 */
export function EmptyState({
  koshPose = 'calm',
  title,
  body,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="empty" data-testid="empty-state">
      <Kosh pose={koshPose} size={90} />
      <b>{title}</b>
      {body && <p>{body}</p>}
      {actionLabel && onAction && (
        <Button variant="primary" compact onClick={onAction}>
          {actionLabel}
        </Button>
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
export function ErrorState({
  title = 'Something went wrong',
  body,
  correlationId,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="empty" role="alert" data-testid="error-state">
      <Kosh pose="error" size={90} />
      <b>{title}</b>
      {body && <p>{body}</p>}
      {correlationId && (
        <small style={{ color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>
          Correlation ID: {correlationId}
        </small>
      )}
      {onRetry && (
        <Button variant="soft" compact onClick={onRetry} style={{ marginTop: 8 }}>
          Retry
        </Button>
      )}
    </div>
  );
}

export function ForbiddenState() {
  return (
    <div className="empty" role="alert" data-testid="forbidden-state">
      <Kosh pose="lock" size={90} />
      <b>Access restricted</b>
      <p>Your signed-in role does not have authorization to view this resource.</p>
    </div>
  );
}

export function OfflineState({ what, onRetry }: { what?: string; onRetry?: () => void }) {
  return (
    <div className="empty" role="alert" data-testid="offline-state">
      <Kosh pose="offline" size={90} />
      <b>{what ? `${what} unavailable` : 'Temporarily unavailable'}</b>
      <p>The connection to the secure server was interrupted. Retrying automatically.</p>
      {onRetry && (
        <Button variant="soft" compact onClick={onRetry} style={{ marginTop: 8 }}>
          Reconnect
        </Button>
      )}
    </div>
  );
}
