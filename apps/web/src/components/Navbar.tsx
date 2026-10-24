import React from 'react';
import { Shield, Clock, User, Globe, PhoneCall, Bell, Search, QrCode, MoreHorizontal } from 'lucide-react';
import { AppRole } from '../types';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  role: AppRole;
  setRole: (role: AppRole) => void;
  lang: string;
  setLang: (lang: string) => void;
  simClockOffsetDays: number;
  onOpenSimClock: () => void;
  onTriggerVoiceDemo: () => void;
  onOpenCommandPalette?: () => void;
  onOpenNotifications?: () => void;
  unreadNotificationsCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  role,
  setRole,
  lang,
  setLang,
  simClockOffsetDays,
  onOpenSimClock,
  onTriggerVoiceDemo,
  onOpenCommandPalette,
  onOpenNotifications,
  unreadNotificationsCount = 2,
}) => {
  // Primary core tabs that existing tests check
  const primaryTabs = [
    { id: 'dashboard', label: 'KPI Dashboard' },
    { id: 'search', label: 'Search & Views' },
    { id: 'submit', label: 'Submit FDR (L1)' },
    { id: 'verify', label: 'Bank Verification (L2/L3)' },
    { id: 'reminders', label: 'Reminder Ladder' },
    { id: 'release', label: 'Release Authorization' },
    { id: 'reports', label: 'Reports & Exports' },
    { id: 'copilot', label: 'AI Copilot & SQL' },
    { id: 'audit', label: 'Audit Chain' },
    { id: 'admin', label: 'Admin & Connectors' },
    { id: 'help', label: 'Help & DPDP' },
  ];

  return (
    <header
      className="glass-panel"
      style={{
        borderRadius: '0 0 20px 20px',
        borderTop: 'none',
        padding: '12px 24px',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        backdropFilter: 'blur(24px)',
        borderBottom: '1px solid rgba(0, 238, 255, 0.25)',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8), 0 0 25px rgba(59, 10, 107, 0.4)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
        {/* Logo and Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #3b0a6b, #00eeff)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px rgba(0, 238, 255, 0.45)',
            }}
          >
            <Shield size={20} color="#fff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontFamily: 'var(--font-serif)',
                  fontWeight: 700,
                  fontSize: '18px',
                  letterSpacing: '-0.02em',
                  background: 'linear-gradient(135deg, #ffffff 30%, #ede4f9 70%, #00eeff 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                AICTE FDR Portal
              </span>
              <span
                style={{
                  fontSize: '9px',
                  background: 'rgba(59, 10, 107, 0.6)',
                  color: '#00eeff',
                  border: '1px solid rgba(0, 238, 255, 0.4)',
                  padding: '2px 6px',
                  borderRadius: 6,
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                }}
              >
                REGULATION
              </span>
            </div>
            <div style={{ fontSize: '10px', color: '#c4b5fd', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Security Deposit Compliance Engine
            </div>
          </div>
        </div>

        {/* Global Command Palette Trigger Button */}
        {onOpenCommandPalette && (
          <button
            onClick={onOpenCommandPalette}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              borderRadius: 8,
              background: 'rgba(0, 0, 0, 0.4)',
              border: '1px solid rgba(0, 238, 255, 0.25)',
              color: '#94a3b8',
              fontSize: '12px',
              cursor: 'pointer',
            }}
            title="Press ⌘K or Ctrl+K to jump anywhere"
          >
            <Search size={14} className="text-cyan-400" />
            <span className="hidden sm:inline">Search / Jump</span>
            <kbd style={{ fontSize: '10px', padding: '1px 5px', borderRadius: 4, background: 'rgba(255,255,255,0.1)', color: '#00eeff' }}>
              ⌘K
            </kbd>
          </button>
        )}

        {/* Navigation Tabs Bar */}
        <nav
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
            background: 'rgba(0, 0, 0, 0.35)',
            padding: '3px',
            borderRadius: 10,
            border: '1px solid var(--border-glass)',
            overflowX: 'auto',
            maxWidth: '100%',
          }}
        >
          {primaryTabs.map((tab) => {
            const active = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id)}
                style={{
                  padding: '5px 11px',
                  borderRadius: 7,
                  fontSize: '12px',
                  fontWeight: active ? 600 : 500,
                  color: active ? '#ffffff' : 'var(--text-secondary)',
                  background: active
                    ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(37, 99, 235, 0.25))'
                    : 'transparent',
                  border: active ? '1px solid rgba(6, 182, 212, 0.4)' : '1px solid transparent',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease',
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Quick Actions & Role Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Notification Bell */}
          {onOpenNotifications && (
            <button
              onClick={onOpenNotifications}
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '6px',
                borderRadius: 8,
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-glass)',
                color: '#e2e8f0',
                cursor: 'pointer',
              }}
              title="Notifications"
            >
              <Bell size={16} />
              {unreadNotificationsCount > 0 && (
                <span
                  style={{
                    position: 'absolute',
                    top: '-3px',
                    right: '-3px',
                    width: '14px',
                    height: '14px',
                    borderRadius: '50%',
                    background: '#ef4444',
                    color: '#fff',
                    fontSize: '9px',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {unreadNotificationsCount}
                </span>
              )}
            </button>
          )}

          {/* Public Receipt Verification Switch */}
          <button
            onClick={() => setCurrentTab('public_receipt')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 10px',
              borderRadius: 8,
              background: currentTab === 'public_receipt' ? 'rgba(0, 238, 255, 0.2)' : 'rgba(255, 255, 255, 0.05)',
              border: currentTab === 'public_receipt' ? '1px solid #00eeff' : '1px solid var(--border-glass)',
              color: currentTab === 'public_receipt' ? '#00eeff' : 'var(--text-secondary)',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
            title="Public Verification Gateway (No Auth)"
          >
            <QrCode size={13} />
            <span className="hidden md:inline">Public Verify</span>
          </button>

          {/* Sim Clock Button */}
          <button
            onClick={onOpenSimClock}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '5px 10px',
              borderRadius: 8,
              background: simClockOffsetDays > 0 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              border: simClockOffsetDays > 0 ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid var(--border-glass)',
              color: simClockOffsetDays > 0 ? '#fbbf24' : 'var(--text-secondary)',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <Clock size={13} />
            <span>Clock {simClockOffsetDays > 0 ? `+${simClockOffsetDays}d` : 'Live'}</span>
          </button>

          {/* AI Voice Call Trigger */}
          <button
            onClick={onTriggerVoiceDemo}
            className="ring-pulse"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '6px 12px',
              borderRadius: 8,
              background: 'linear-gradient(135deg, #3b0a6b 0%, #00eeff 100%)',
              border: '1px solid rgba(0, 238, 255, 0.6)',
              color: '#ffffff',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 0 16px rgba(0, 238, 255, 0.4)',
            }}
          >
            <PhoneCall size={13} />
            <span>AI Voice Call</span>
          </button>

          {/* Language Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '3px', background: 'rgba(255, 255, 255, 0.05)', padding: '3px 6px', borderRadius: 8, border: '1px solid var(--border-glass)' }}>
            <Globe size={13} color="var(--text-muted)" />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', fontSize: '11px', fontWeight: 500, outline: 'none', cursor: 'pointer' }}
            >
              <option value="en" style={{ background: '#0f172a' }}>EN</option>
              <option value="hi" style={{ background: '#0f172a' }}>हिंदी</option>
              <option value="ta" style={{ background: '#0f172a' }}>தமிழ்</option>
            </select>
          </div>

          {/* Role Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '3px', background: 'rgba(255, 255, 255, 0.05)', padding: '3px 6px', borderRadius: 8, border: '1px solid var(--border-glass)' }}>
            <User size={13} color="var(--text-muted)" />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as AppRole)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', fontSize: '11px', fontWeight: 500, outline: 'none', cursor: 'pointer' }}
            >
              <option value="institution" style={{ background: '#0f172a' }}>Institution</option>
              <option value="scrutiny_officer" style={{ background: '#0f172a' }}>Scrutiny Officer</option>
              <option value="competent_authority" style={{ background: '#0f172a' }}>Competent Authority</option>
              <option value="bureau_admin" style={{ background: '#0f172a' }}>Bureau Admin</option>
              <option value="auditor" style={{ background: '#0f172a' }}>Auditor</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
