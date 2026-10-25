import React, { useState } from 'react';
import { Bell, CheckCheck, Clock, X, ShieldAlert, Sparkles, Smartphone, CheckCircle2, Moon, AlertTriangle } from 'lucide-react';
import { InAppNotification } from '../types';
import { Kosh } from '../design-system/Kosh';

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToTab?: (tab: string) => void;
}

type FilterChip = 'All' | 'Reminders' | 'Observations' | 'Decisions';

export const NotificationCenter: React.FC<NotificationCenterProps> = ({ isOpen, onClose, onNavigateToTab }) => {
  const [selectedFilter, setSelectedFilter] = useState<FilterChip>('All');
  const [activeTab, setActiveTab] = useState<'inbox' | 'preferences'>('inbox');
  const [webPushEnabled, setWebPushEnabled] = useState(true);
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(false);

  // No fabricated inbox items — honest empty state
  const [notifications, setNotifications] = useState<InAppNotification[]>([]);

  if (!isOpen) return null;

  const filtered = notifications.filter((n) => {
    if (selectedFilter === 'All') return true;
    if (selectedFilter === 'Reminders') return n.category === 'deadline';
    if (selectedFilter === 'Observations') return n.category === 'critical_workflow';
    if (selectedFilter === 'Decisions') return n.category === 'security_account';
    return true;
  });

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 90,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'flex-end',
        padding: '20px',
        background: 'rgba(15, 23, 42, 0.4)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        boxSizing: 'border-box',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '460px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--surface)',
          borderRadius: '28px',
          boxShadow: 'var(--shadow-floating)',
          padding: 0,
          overflow: 'hidden',
          border: 'none',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--hairline)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'var(--primary-container)',
                display: 'grid',
                placeItems: 'center',
                color: 'var(--primary)',
              }}
            >
              <Bell size={18} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: 'var(--text1)', fontFamily: 'var(--font-display)' }}>
                Notifications
              </h3>
              <p style={{ margin: 0, fontSize: '11px', color: 'var(--text3)', fontWeight: 600 }}>
                In-App Inbox ({notifications.length}) & Realtime Feed
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)', padding: 4 }}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* View Switcher: Inbox / Preferences */}
        <div style={{ padding: '12px 20px 0', display: 'flex', gap: '8px' }}>
          <div className="segmented" style={{ width: '100%' }}>
            <button
              type="button"
              className={activeTab === 'inbox' ? 'is-active' : ''}
              aria-selected={activeTab === 'inbox'}
              onClick={() => setActiveTab('inbox')}
            >
              Inbox
            </button>
            <button
              type="button"
              className={activeTab === 'preferences' ? 'is-active' : ''}
              aria-selected={activeTab === 'preferences'}
              onClick={() => setActiveTab('preferences')}
            >
              Preferences
            </button>
          </div>
        </div>

        {activeTab === 'inbox' ? (
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflowY: 'auto' }}>
            {/* Filter Chips matching Screen 7 in ui-refrence.png */}
            <div style={{ padding: '14px 20px 8px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {(['All', 'Reminders', 'Observations', 'Decisions'] as FilterChip[]).map((chip) => {
                const isActive = selectedFilter === chip;
                return (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => setSelectedFilter(chip)}
                    className={`chip ${isActive ? 'is-active' : ''}`}
                    style={{
                      fontSize: '12px',
                      fontWeight: 700,
                      padding: '6px 14px',
                      borderRadius: '999px',
                      border: 'none',
                      cursor: 'pointer',
                      background: isActive ? 'var(--primary-container)' : 'var(--field)',
                      color: isActive ? 'var(--primary)' : 'var(--text2)',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {chip}
                  </button>
                );
              })}
            </div>

            {/* Empty State matching Screen 7 in ui-refrence.png */}
            {filtered.length === 0 ? (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  padding: '48px 28px',
                  gap: '12px',
                }}
              >
                <div style={{ filter: 'drop-shadow(0 10px 20px rgba(59, 120, 216, 0.22))' }}>
                  <Kosh pose="calm" size={92} />
                </div>
                <h4 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: 'var(--text1)', fontFamily: 'var(--font-display)' }}>
                  Nothing here yet
                </h4>
                <p style={{ margin: 0, fontSize: '13px', color: 'var(--text3)', lineHeight: '19px', maxWidth: '300px', fontWeight: 500 }}>
                  Reminders, observations and decisions will appear here as soon as they happen.
                </p>
              </div>
            ) : (
              <div style={{ padding: '12px 20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {filtered.map((n) => (
                  <div
                    key={n.id}
                    className="card"
                    style={{
                      padding: '12px 14px',
                      background: 'var(--surface-muted)',
                      borderRadius: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text1)' }}>{n.title}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text3)' }}>{n.created_at}</span>
                    </div>
                    <p style={{ margin: 0, fontSize: '12px', color: 'var(--text2)' }}>{n.body}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* Preferences Panel */
          <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto' }}>
            <div className="card" style={{ padding: '14px', background: 'var(--surface-muted)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <b style={{ display: 'block', fontSize: '13px', color: 'var(--text1)' }}>Web Push Notifications</b>
                <small style={{ color: 'var(--text3)' }}>Instant alerts on desktop and mobile browser</small>
              </div>
              <input
                type="checkbox"
                checked={webPushEnabled}
                onChange={(e) => setWebPushEnabled(e.target.checked)}
                style={{ width: 18, height: 18, accentColor: 'var(--azure)' }}
              />
            </div>

            <div className="card" style={{ padding: '14px', background: 'var(--surface-muted)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <b style={{ display: 'block', fontSize: '13px', color: 'var(--text1)' }}>Official Email Digest</b>
                <small style={{ color: 'var(--text3)' }}>Daily escalation summary and audit notices</small>
              </div>
              <input
                type="checkbox"
                checked={emailEnabled}
                onChange={(e) => setEmailEnabled(e.target.checked)}
                style={{ width: 18, height: 18, accentColor: 'var(--azure)' }}
              />
            </div>

            <div className="card" style={{ padding: '14px', background: 'var(--surface-muted)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <b style={{ display: 'block', fontSize: '13px', color: 'var(--text1)' }}>Statutory Quiet Hours</b>
                <small style={{ color: 'var(--text3)' }}>Suppress non-critical alerts 20:00 – 08:00</small>
              </div>
              <input
                type="checkbox"
                checked={quietHoursEnabled}
                onChange={(e) => setQuietHoursEnabled(e.target.checked)}
                style={{ width: 18, height: 18, accentColor: 'var(--azure)' }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
