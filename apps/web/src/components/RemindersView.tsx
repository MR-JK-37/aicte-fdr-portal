import React, { useEffect, useState } from 'react';
import { Bell, Mail, ShieldAlert, Calendar, Activity } from 'lucide-react';
import { Instrument } from '../types';
import { Kosh } from '../design-system/Kosh';
import { api } from '../lib/apiClient';

interface RemindersViewProps {
  instruments: Instrument[];
}

interface ReminderRow {
  id: string;
  instrument_id: string;
  target_date: string | null;
  window: string;
  status: string;
  channel: string;
  ladder_step: number;
  acknowledged_at: string | null;
  created_at: string | null;
}

interface SchedulerStatus {
  scheduler_active: boolean;
  active_schedule_version: number | null;
  has_approved_schedule: boolean;
  status_alert: string | null;
  last_run_at: string | null;
  last_run_status: string | null;
}

export const RemindersView: React.FC<RemindersViewProps> = ({ instruments }) => {
  const [reminders, setReminders] = useState<ReminderRow[] | null>(null);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [remindersRes, statusRes] = await Promise.all([
        api.GET('/v1/reminders', { params: { query: { limit: 50 } } }),
        api.GET('/v1/scheduler/status'),
      ]);
      if (cancelled) return;
      if (remindersRes.error || statusRes.error) {
        setLoadError('Could not load reminder data from the API.');
        return;
      }
      setReminders((remindersRes.data as unknown as ReminderRow[]) ?? []);
      setSchedulerStatus((statusRes.data as SchedulerStatus) ?? null);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const instrumentById = new Map(instruments.map((i) => [i.id, i]));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div
        className="card"
        style={{
          padding: '24px 28px',
          background: 'var(--hero-from)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <Calendar size={22} color="var(--azure)" />
            <h2
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '28px',
                fontWeight: 800,
                color: 'var(--text1)',
                margin: 0,
              }}
            >
              Maturity Ladder &amp; Reminders Inbox
            </h2>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text2)', margin: 0, fontWeight: 500 }}>
            Automated statutory escalation ladder for approaching-maturity FDRs. Zero voice/telephony channel: in-app, push, and official email only.
          </p>
        </div>
      </div>

      {/* Scheduler status — always honest about approval state, never hides that it's running */}
      {schedulerStatus && (
        <div
          className="card"
          style={{
            padding: '20px 24px',
            background: schedulerStatus.has_approved_schedule ? 'var(--surface)' : 'var(--warn-container)',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            border: schedulerStatus.has_approved_schedule ? '1px solid var(--border)' : 'none',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {schedulerStatus.has_approved_schedule ? (
              <Activity size={18} color="var(--azure)" />
            ) : (
              <ShieldAlert size={18} color="var(--on-warn-container)" />
            )}
            <h3
              style={{
                margin: 0,
                fontSize: '13px',
                fontWeight: 800,
                color: schedulerStatus.has_approved_schedule ? 'var(--text1)' : 'var(--on-warn-container)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              {schedulerStatus.has_approved_schedule
                ? `Approved schedule v${schedulerStatus.active_schedule_version} active`
                : 'No approved reminder schedule'}
            </h3>
          </div>
          <p
            style={{
              margin: 0,
              fontSize: '13px',
              color: schedulerStatus.has_approved_schedule ? 'var(--text2)' : 'var(--on-warn-container)',
              lineHeight: '20px',
              fontWeight: 500,
            }}
          >
            {schedulerStatus.has_approved_schedule ? (
              'Reminder windows and escalation steps below come from this approved policy version.'
            ) : (
              <>
                Reminder windows, escalation steps, and dispatch channels are config (D-10 in{' '}
                <code style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>docs/OPEN_DECISIONS.md</code>). No
                AICTE policy owner has approved a schedule yet, so any reminders below were generated under the
                system's conservative dev/staging default (T-90/T-60/T-30/T-7/T-0 days before maturity), not an
                official notice. The scheduler never invents an approval; it only ever marks rows with the provenance
                they actually have.
              </>
            )}
          </p>
          <p style={{ margin: 0, fontSize: '12px', color: 'var(--text3)' }}>
            Scheduler heartbeat:{' '}
            {schedulerStatus.last_run_at
              ? `last ran ${new Date(schedulerStatus.last_run_at).toLocaleString()} (${schedulerStatus.last_run_status})`
              : 'no run recorded yet'}
          </p>
        </div>
      )}

      {loadError && (
        <div className="card" style={{ padding: '16px 20px', background: 'var(--warn-container)', color: 'var(--on-warn-container)', fontSize: '13px' }}>
          {loadError}
        </div>
      )}

      {/* Active Reminders Card */}
      <div className="card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <Mail size={18} color="var(--azure)" />
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: 'var(--text1)', fontFamily: 'var(--font-display)' }}>
            Active Reminders
          </h3>
        </div>

        {reminders === null ? (
          <p style={{ fontSize: '13px', color: 'var(--text3)' }}>Loading reminders…</p>
        ) : reminders.length === 0 ? (
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
              No instrument in your scope is currently within a reminder window (T-90 days or closer to maturity).
            </p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--text3)', fontSize: '11px', textTransform: 'uppercase' }}>
                <th style={{ paddingBottom: '8px' }}>Instrument</th>
                <th style={{ paddingBottom: '8px' }}>Window</th>
                <th style={{ paddingBottom: '8px' }}>Target date</th>
                <th style={{ paddingBottom: '8px' }}>Channel</th>
                <th style={{ paddingBottom: '8px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {reminders.map((r) => {
                const instrument = instrumentById.get(r.instrument_id);
                return (
                  <tr key={r.id} style={{ borderTop: '1px solid var(--border)' }}>
                    <td style={{ padding: '10px 0', fontWeight: 700, color: 'var(--text1)' }}>
                      {instrument ? instrument.instrument_number : r.instrument_id}
                    </td>
                    <td style={{ padding: '10px 0', color: 'var(--text2)' }}>{r.window}</td>
                    <td style={{ padding: '10px 0', color: 'var(--text2)' }}>
                      {r.target_date ? new Date(r.target_date).toLocaleDateString() : '—'}
                    </td>
                    <td style={{ padding: '10px 0', color: 'var(--text2)' }}>{r.channel}</td>
                    <td style={{ padding: '10px 0' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '2px 10px',
                          borderRadius: '999px',
                          background: 'var(--field)',
                          color: 'var(--text2)',
                          fontWeight: 700,
                          fontSize: '11px',
                        }}
                      >
                        <Bell size={11} /> {r.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
