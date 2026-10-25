import React from 'react';
import { Wordmark } from './Wordmark';
import { Icon } from './Icon';

export interface TopBarProps {
  role: string;
  profileCompletionPct?: number;
  unreadCount?: number;
  onOpenNotifications?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * TopBar: wordmark + thin black progress (real profile completion) + bell + read-only role pill.
 * Reference: DESIGN_SPEC §5.1 / G-24.
 */
export const TopBar: React.FC<TopBarProps> = ({
  role,
  profileCompletionPct = 68,
  unreadCount = 0,
  onOpenNotifications,
  className = '',
  style,
}) => {
  return (
    <header data-testid="topbar" className={`topbar ${className}`} style={style}>
      <Wordmark />

      <div style={{ flex: 1 }} />

      {/* Profile completion mini progress */}
      <div data-testid="progress-mini" className="topprog">
        <div className="progress-ink">
          <i style={{ width: `${Math.min(100, Math.max(0, profileCompletionPct))}%` }} />
        </div>
        <b>{profileCompletionPct}%</b>
      </div>

      {/* Bell icon with live unread indicator */}
      <button
        type="button"
        data-testid="bell"
        className="bellw"
        onClick={onOpenNotifications}
        aria-label={`Notifications (${unreadCount} unread)`}
        style={{ background: 'transparent', border: 0, padding: 4 }}
      >
        <Icon name="notifications" size={22} color="var(--ink, #1a1a1e)" />
        {unreadCount > 0 && <span className="bell-dot" data-testid="bell-dot" />}
      </button>

      {/* Read-only Role Pill */}
      <span
        data-testid="role-pill"
        className="pill-role"
        style={{
          background: 'var(--role-fill)',
          color: 'var(--on-role-fill)',
        }}
      >
        {role}
      </span>
    </header>
  );
};
