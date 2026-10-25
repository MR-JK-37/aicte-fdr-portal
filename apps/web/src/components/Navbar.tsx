import React from 'react';
import { Wordmark } from '../design-system/Wordmark';
import { Icon } from '../design-system/Icon';
import { AppRole } from '../types';
import { useAuth } from '../auth/AuthContext';

export interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  role: AppRole;
  lang: string;
  setLang: (lang: string) => void;
  onOpenCommandPalette?: () => void;
  onOpenNotifications?: () => void;
  onLogout?: () => void;
  unreadNotificationsCount?: number;
  sseStatus?: 'connecting' | 'live' | 'disconnected';
  profileCompletionPct?: number;
}

/**
 * TopBar Navbar component (Stream R5.4 / DESIGN_SPEC §5.1 / G-24).
 * Floating header on lavender canvas:
 * Wordmark + AICTE title · ⌘K search · thin black ProgressMini · live SSE indicator ·
 * bell with unread dot · language selector · read-only Role Pill · sign-out.
 */
export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  role,
  lang,
  setLang,
  onOpenCommandPalette,
  onOpenNotifications,
  onLogout,
  unreadNotificationsCount = 0,
  sseStatus = 'disconnected',
  profileCompletionPct = 68,
}) => {
  const { user } = useAuth();
  const initials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n: string) => n[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : 'AK';

  return (
    <header
      data-testid="topbar"
      className="topbar"
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 'var(--z-nav, 40)',
        background: 'var(--surface)',
        boxShadow: 'var(--shadow-card)',
        padding: '0 20px',
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '14px',
      }}
    >
      {/* Brand & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <Wordmark />
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontFamily: 'var(--font-display, "Plus Jakarta Sans", sans-serif)',
                fontWeight: 800,
                fontSize: '16px',
                lineHeight: '20px',
                color: 'var(--text1)',
                letterSpacing: '-0.02em',
              }}
            >
              AICTE FDR Portal
            </span>
            <span
              style={{
                fontSize: '10px',
                fontWeight: 700,
                background: 'var(--primary-container)',
                color: 'var(--primary)',
                padding: '2px 6px',
                borderRadius: 'var(--radius-pill, 999px)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              Regulation
            </span>
          </div>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text3)',
              lineHeight: '14px',
            }}
          >
            Security Deposit Compliance Engine
          </span>
        </div>
      </div>

      {/* Global Command Palette Trigger Button (⌘K) */}
      {onOpenCommandPalette && (
        <button
          type="button"
          onClick={onOpenCommandPalette}
          title="Press ⌘K or Ctrl+K to jump anywhere"
          aria-label="Search or jump (⌘K)"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            height: '36px',
            padding: '0 12px',
            borderRadius: 'var(--radius-pill, 999px)',
            background: 'var(--field)',
            border: 'none',
            color: 'var(--text2)',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'background var(--dur-fast, 160ms)',
          }}
        >
          <Icon name="search" size={16} color="var(--azure)" />
          <span className="hidden sm:inline">Search / Jump</span>
          <kbd
            style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '2px 6px',
              borderRadius: '6px',
              background: 'var(--surface)',
              color: 'var(--text2)',
              boxShadow: 'var(--shadow-card)',
            }}
          >
            ⌘K
          </kbd>
        </button>
      )}

      {/* Actions, Profile Completion, SSE, Notifications, Role */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>

        {/* Realtime Stream (SSE) Status Indicator */}
        <div
          data-testid="sse-status-indicator"
          title={`Realtime Feed: ${sseStatus}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            height: '32px',
            padding: '0 10px',
            borderRadius: 'var(--radius-pill, 999px)',
            background: 'var(--field)',
            fontSize: '11px',
            fontWeight: 700,
            color: 'var(--text2)',
          }}
        >
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              backgroundColor:
                sseStatus === 'live'
                  ? 'var(--ok, #0b7a4b)'
                  : sseStatus === 'connecting'
                  ? 'var(--warn, #8f5a00)'
                  : 'var(--text3, #80859f)',
            }}
          />
          <span className="hidden lg:inline">
            {sseStatus === 'live' ? 'Live' : sseStatus === 'connecting' ? 'Connecting…' : 'Offline'}
          </span>
        </div>

        {/* Public Receipt Verification Gateway */}
        <button
          type="button"
          onClick={() => setCurrentTab('public_receipt')}
          title="Public Verification Gateway (No Auth)"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            height: '36px',
            padding: '0 12px',
            borderRadius: 'var(--radius-pill, 999px)',
            background: currentTab === 'public_receipt' ? 'var(--primary-container)' : 'var(--field)',
            border: 'none',
            color: currentTab === 'public_receipt' ? 'var(--primary)' : 'var(--text2)',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          <Icon name="qr" size={15} color="var(--azure)" />
          <span className="hidden md:inline">Public Verify</span>
        </button>

        {/* Notification Bell */}
        {onOpenNotifications && (
          <button
            type="button"
            data-testid="bell"
            onClick={onOpenNotifications}
            title="Notifications"
            aria-label={`Notifications (${unreadNotificationsCount} unread)`}
            className="bellw"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-pill, 999px)',
              background: 'var(--field)',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            <Icon name="notifications" size={18} color="var(--ink)" />
            {unreadNotificationsCount > 0 && (
              <span
                data-testid="bell-dot"
                className="bell-dot"
                style={{
                  position: 'absolute',
                  top: '2px',
                  right: '2px',
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: 'var(--danger)',
                }}
              />
            )}
          </button>
        )}

        {/* Language Selector combobox (accessible name Language) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            height: '36px',
            padding: '0 8px',
            borderRadius: 'var(--radius-pill, 999px)',
            background: 'var(--field)',
          }}
        >
          <Icon name="language" size={14} color="var(--text3)" />
          <select
            aria-label="Language"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text1)',
              fontSize: '12px',
              fontWeight: 600,
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="en">EN</option>
            <option value="hi">हिंदी</option>
            <option value="ta">தமிழ்</option>
          </select>
        </div>

        {/* Read-only Role Pill */}
        <span
          data-testid="role-pill"
          className="pill-role"
          title="Your role (set by server, not switchable)"
          style={{
            background: 'var(--role-fill)',
            color: 'var(--on-role-fill)',
            textTransform: 'capitalize',
            letterSpacing: '0.02em',
          }}
        >
          {role.replace(/_/g, ' ')}
        </span>

        {/* User Avatar Initials (ui-refrence.png) */}
        <div
          className="avatar sm"
          title={user?.full_name || 'User Profile'}
          style={{
            cursor: 'pointer',
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #c9d7f7, #e6edff)',
            color: 'var(--primary)',
            display: 'grid',
            placeItems: 'center',
            fontWeight: 800,
            fontSize: '13px',
            fontFamily: 'var(--font-display)',
            boxShadow: 'var(--shadow-card)',
            flexShrink: 0,
          }}
        >
          {initials}
        </div>

        {/* Sign Out Button */}
        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            title="Sign out"
            aria-label="Sign out"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-pill, 999px)',
              background: 'var(--field)',
              border: 'none',
              color: 'var(--text2)',
              cursor: 'pointer',
            }}
          >
            <Icon name="sign_out" size={16} color="var(--text2)" />
          </button>
        )}
      </div>
    </header>
  );
};
