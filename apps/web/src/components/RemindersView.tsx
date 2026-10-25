import React from 'react';
import { Bell, Clock, Mail, ShieldAlert, Calendar } from 'lucide-react';
import { Instrument } from '../types';
import { Kosh } from '../design-system/Kosh';

interface RemindersViewProps {
  instruments: Instrument[];
}

export const RemindersView: React.FC<RemindersViewProps> = ({ instruments }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div
        className="card"
        style={{
          padding: '24px 28px',
          background: 'linear-gradient(135deg, var(--hero-from), var(--hero-to) 70%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              borderRadius: '999px',
              background: 'rgba(255, 255, 255, 0.7)',
              color: 'var(--azure)',
              fontSize: '12px',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '10px',
            }}
          >
            <Calendar size={14} />
            Maturity Escalation Surveillance
          </span>
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '28px',
              fontWeight: 800,
              color: 'var(--text1)',
              margin: '0 0 6px',
            }}
          >
            Maturity Ladder &amp; Reminders Inbox
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text2)', margin: 0, fontWeight: 500 }}>
            Automated statutory escalation ladder for approaching-maturity FDRs. Zero voice/telephony channel — in-app, push, and official email only.
          </p>
        </div>
      </div>

      {/* Honest reminder-schedule banner (D-10): preserves test match */}
      <div
        className="card"
        style={{
          padding: '20px 24px',
          background: 'var(--warn-container)',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          border: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={18} color="var(--on-warn-container)" />
          <h3 style={{ margin: 0, fontSize: '13px', fontWeight: 800, color: 'var(--on-warn-container)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            No approved reminder schedule
          </h3>
        </div>
        <p style={{ margin: 0, fontSize: '13px', color: 'var(--on-warn-container)', lineHeight: '20px', fontWeight: 500 }}>
          Reminder windows, escalation steps, and dispatch channels are config (D-10 in{' '}
          <code style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>docs/OPEN_DECISIONS.md</code>), not a hard-coded ladder — the
          backend already has a DB-leased scheduler and reminder ladder (
          <code style={{ fontFamily: 'var(--font-mono)' }}>app/reminders/scheduler.py</code>) and refuses to invent a
          schedule when none is approved. This screen has no reminder data to show until (a) a schedule is approved and (b) stream R4 exposes{' '}
          <code style={{ fontFamily: 'var(--font-mono)' }}>GET /v1/reminder-schedules</code> /{' '}
          <code style={{ fontFamily: 'var(--font-mono)' }}>GET /v1/reminders</code> for the UI to call.
        </p>
      </div>

      {/* Active Reminders Card */}
      <div className="card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <Mail size={18} color="var(--azure)" />
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: 'var(--text1)', fontFamily: 'var(--font-display)' }}>
            Active Reminders
          </h3>
        </div>

        {instruments.length === 0 ? (
          <div
            style={{
              padding: '36px 20px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '10px',
              color: 'var(--text3)',
            }}
          >
            <Kosh pose="calm" size={72} />
            <b style={{ fontSize: '14px', color: 'var(--text1)' }}>Nothing here yet</b>
            <p style={{ margin: 0, fontSize: '13px', maxWidth: '380px' }}>
              Reminders will appear once a schedule is approved and the API is wired (stream R3/R4).
            </p>
          </div>
        ) : (
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text3)' }}>
            No approved reminder schedule is active for the current tenant records.
          </p>
        )}
      </div>
    </div>
  );
};
