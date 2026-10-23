import React from 'react';
import { Shield, Clock, User, Globe, PhoneCall, Sparkles } from 'lucide-react';
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
}) => {
  const tabs = [
    { id: 'dashboard', label: 'KPI Dashboard' },
    { id: 'submit', label: 'Submit FDR (L1)' },
    { id: 'verify', label: 'Bank Verification (L2/L3)' },
    { id: 'reminders', label: 'Reminder Ladder' },
    { id: 'release', label: 'Release Authorization' },
    { id: 'copilot', label: 'AI Copilot & SQL' },
    { id: 'audit', label: 'Audit Chain' },
  ];

  return (
    <header className="glass-panel" style={{ borderRadius: '0 0 20px 20px', borderTop: 'none', padding: '14px 28px', position: 'sticky', top: 0, zIndex: 40, backdropFilter: 'blur(24px)', borderBottom: '1px solid rgba(0, 238, 255, 0.25)', boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8), 0 0 25px rgba(59, 10, 107, 0.4)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        {/* Logo and Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: 42, height: 42, borderRadius: 12, background: 'linear-gradient(135deg, #3b0a6b, #00eeff)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 20px rgba(0, 238, 255, 0.45)' }}>
            <Shield size={24} color="#fff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontFamily: 'var(--font-serif)', fontWeight: 700, fontSize: '20px', letterSpacing: '-0.02em', background: 'linear-gradient(135deg, #ffffff 30%, #ede4f9 70%, #00eeff 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                AICTE FDR Portal
              </span>
              <span style={{ fontSize: '10px', background: 'rgba(59, 10, 107, 0.6)', color: '#00eeff', border: '1px solid rgba(0, 238, 255, 0.4)', padding: '2px 8px', borderRadius: 6, fontWeight: 700, letterSpacing: '0.05em' }}>
                ZERO-COST SPEC
              </span>
            </div>
            <div style={{ fontSize: '11px', color: '#c4b5fd', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Regulation Bureau • Security Deposit Management
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(0, 0, 0, 0.3)', padding: '4px', borderRadius: 12, border: '1px solid var(--border-glass)' }}>
          {tabs.map((tab) => {
            const active = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 8,
                  fontSize: '13px',
                  fontWeight: active ? 600 : 500,
                  color: active ? '#ffffff' : 'var(--text-secondary)',
                  background: active ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(37, 99, 235, 0.25))' : 'transparent',
                  border: active ? '1px solid rgba(6, 182, 212, 0.4)' : '1px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Quick Actions & Role Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Sim Clock Button */}
          <button
            onClick={onOpenSimClock}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: 8,
              background: simClockOffsetDays > 0 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              border: simClockOffsetDays > 0 ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid var(--border-glass)',
              color: simClockOffsetDays > 0 ? '#fbbf24' : 'var(--text-secondary)',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <Clock size={14} />
            <span>Clock {simClockOffsetDays > 0 ? `+${simClockOffsetDays}d` : 'Live'}</span>
          </button>

          {/* AI Voice Call Trigger */}
          <button
            onClick={onTriggerVoiceDemo}
            className="ring-pulse"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '7px 14px',
              borderRadius: 10,
              background: 'linear-gradient(135deg, #3b0a6b 0%, #00eeff 100%)',
              border: '1px solid rgba(0, 238, 255, 0.6)',
              color: '#ffffff',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 0 20px rgba(0, 238, 255, 0.4)',
            }}
          >
            <PhoneCall size={14} />
            <span>AI Voice Call</span>
          </button>

          {/* Language Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255, 255, 255, 0.05)', padding: '4px 8px', borderRadius: 8, border: '1px solid var(--border-glass)' }}>
            <Globe size={14} color="var(--text-muted)" />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', fontSize: '12px', fontWeight: 500, outline: 'none', cursor: 'pointer' }}
            >
              <option value="en" style={{ background: '#0f172a' }}>English</option>
              <option value="hi" style={{ background: '#0f172a' }}>हिंदी (Hindi)</option>
              <option value="ta" style={{ background: '#0f172a' }}>தமிழ் (Tamil)</option>
            </select>
          </div>

          {/* Role Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255, 255, 255, 0.05)', padding: '4px 8px', borderRadius: 8, border: '1px solid var(--border-glass)' }}>
            <User size={14} color="var(--text-muted)" />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as AppRole)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', fontSize: '12px', fontWeight: 500, outline: 'none', cursor: 'pointer' }}
            >
              <option value="institution" style={{ background: '#0f172a' }}>Role: Institution</option>
              <option value="scrutiny_officer" style={{ background: '#0f172a' }}>Role: Scrutiny Officer</option>
              <option value="competent_authority" style={{ background: '#0f172a' }}>Role: Competent Authority</option>
              <option value="bureau_admin" style={{ background: '#0f172a' }}>Role: Bureau Admin</option>
              <option value="auditor" style={{ background: '#0f172a' }}>Role: Auditor</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
