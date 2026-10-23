import React, { useState } from 'react';
import {
  Bell,
  Clock,
  PhoneCall,
  Mail,
  Smartphone,
  ShieldAlert,
  CheckCircle2,
  Calendar,
  AlertTriangle,
  ChevronRight,
  Send,
  PauseCircle,
  Eye,
  Filter,
  Volume2,
  Moon
} from 'lucide-react';
import { Instrument, ReminderItem } from '../types';

interface RemindersViewProps {
  instruments: Instrument[];
  onTriggerVoiceCall: (instrument: Instrument) => void;
  onAddAuditEntry: (action: string, entityId: string, details: any) => void;
  onAdvanceClock: (days: number) => void;
}

export const RemindersView: React.FC<RemindersViewProps> = ({
  instruments,
  onTriggerVoiceCall,
  onAddAuditEntry,
  onAdvanceClock,
}) => {
  const [filter, setFilter] = useState<'all' | 'pending' | 'urgent' | 'acknowledged'>('all');

  // Simulated reminders tied to maturity ladder
  const [reminders, setReminders] = useState<ReminderItem[]>([
    {
      id: 'rem-1',
      instrument_number: 'AXIS-FDR-99201',
      institution_name: 'Delhi Global Technical Campus',
      window: 'T-30',
      scheduled_for: '2026-10-24 10:00 IST',
      ladder_step: 3,
      current_channel: 'Voice Bot Call + In-App',
      status: 'pending',
    },
    {
      id: 'rem-2',
      instrument_number: 'SBI-881920',
      institution_name: 'Apex Institute of Technology',
      window: 'T-7',
      scheduled_for: '2026-10-23 15:30 IST',
      ladder_step: 4,
      current_channel: 'Voice Bot + High Priority Email',
      status: 'pending',
    },
    {
      id: 'rem-3',
      instrument_number: 'HDFC-441029',
      institution_name: 'National College of Engineering',
      window: 'T-60',
      scheduled_for: '2026-11-15 11:00 IST',
      ladder_step: 2,
      current_channel: 'In-App + Push Notification',
      status: 'sent',
    },
    {
      id: 'rem-4',
      instrument_number: 'PNB-771829',
      institution_name: 'St. Mary’s Polytechnic College',
      window: 'T-0',
      scheduled_for: '2026-10-20 09:00 IST',
      ladder_step: 5,
      current_channel: 'Escalated: Regional Officer Alert',
      status: 'pending',
    },
    {
      id: 'rem-5',
      instrument_number: 'CAN-119283',
      institution_name: 'Shree Sai Institute of Tech',
      window: 'T-90',
      scheduled_for: '2026-12-01 10:00 IST',
      ladder_step: 1,
      current_channel: 'In-App Advisory',
      status: 'acknowledged',
      acknowledged_at: '2026-10-21 16:42 IST',
    },
  ]);

  const handleAcknowledge = (remId: string) => {
    setReminders((prev) =>
      prev.map((r) =>
        r.id === remId
          ? {
              ...r,
              status: 'acknowledged',
              acknowledged_at: new Date().toISOString(),
            }
          : r
      )
    );
    onAddAuditEntry('REMINDER_ACKNOWLEDGED_WEB', remId, {
      channel: 'web_portal',
      timestamp: new Date().toISOString(),
    });
  };

  const handleSnooze = (remId: string, days: number) => {
    alert(`Reminder ${remId} snoozed for ${days} days.`);
    onAddAuditEntry('REMINDER_SNOOZED', remId, {
      snoozed_days: days,
      reason: 'Institution requested renewal processing grace period',
    });
  };

  const filteredReminders = reminders.filter((r) => {
    if (filter === 'pending') return r.status === 'pending';
    if (filter === 'urgent') return r.window === 'T-7' || r.window === 'T-0';
    if (filter === 'acknowledged') return r.status === 'acknowledged';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Bell className="w-7 h-7 text-indigo-400" />
            Maturity Ladder & Reminders Inbox
          </h2>
          <p className="text-sm text-slate-400">
            Problem Statement Scenario 4: Automated escalation ladder (T-90 $\rightarrow$ T-60 $\rightarrow$ T-30 $\rightarrow$ T-7 $\rightarrow$ T-0 $\rightarrow$ Bureau Escalation).
          </p>
        </div>

        {/* Quiet hours banner */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 text-xs text-slate-300">
          <Moon className="w-4 h-4 text-amber-400" />
          <span>
            Quiet Hours Policy: <strong>20:00–08:00 IST</strong> (Telephony calls held; In-App/Email active)
          </span>
        </div>
      </div>

      {/* Maturity Ladder Visual Progress Bar */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-400" />
            Statutory Escalation Ladder (T-Minus Schedule)
          </h3>
          <span className="text-xs text-slate-400">Engine: Celery Beat 15-min cycle</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-700/60 relative overflow-hidden">
            <div className="text-[10px] uppercase font-bold text-slate-400">Step 1</div>
            <div className="text-lg font-bold text-emerald-400">T - 90 Days</div>
            <div className="text-[11px] text-slate-300 mt-1">In-App Advisory</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Gentle early reminder to initiate bank renewal</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-700/60">
            <div className="text-[10px] uppercase font-bold text-slate-400">Step 2</div>
            <div className="text-lg font-bold text-emerald-400">T - 60 Days</div>
            <div className="text-[11px] text-slate-300 mt-1">Push + Email</div>
            <div className="text-[10px] text-slate-500 mt-0.5">FCM Mobile push & automated email advisory</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-indigo-500/40 bg-indigo-950/20">
            <div className="text-[10px] uppercase font-bold text-indigo-400">Step 3</div>
            <div className="text-lg font-bold text-indigo-300">T - 30 Days</div>
            <div className="text-[11px] text-indigo-200 mt-1 font-medium">In-App AI Call</div>
            <div className="text-[10px] text-indigo-300/70 mt-0.5">Interactive Pipecat Voice Agent call (en/hi/ta)</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-amber-500/40 bg-amber-950/20">
            <div className="text-[10px] uppercase font-bold text-amber-400">Step 4</div>
            <div className="text-lg font-bold text-amber-300">T - 7 Days</div>
            <div className="text-[11px] text-amber-200 mt-1 font-medium">Daily Outbound</div>
            <div className="text-[10px] text-amber-300/70 mt-0.5">Flagged PSTN/WhatsApp + Director alert</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-rose-500/40 bg-rose-950/20">
            <div className="text-[10px] uppercase font-bold text-rose-400">Step 5</div>
            <div className="text-lg font-bold text-rose-300">T - 0 (Maturity)</div>
            <div className="text-[11px] text-rose-200 mt-1 font-medium">Expiry Alert</div>
            <div className="text-[10px] text-rose-300/70 mt-0.5">Automated bank renewal verification check</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-purple-500/40 bg-purple-950/20">
            <div className="text-[10px] uppercase font-bold text-purple-400">Step 6</div>
            <div className="text-lg font-bold text-purple-300">T + 15 Overdue</div>
            <div className="text-[11px] text-purple-200 mt-1 font-medium">Bureau Escalation</div>
            <div className="text-[10px] text-purple-300/70 mt-0.5">Show-cause notice & EOA hold initiation</div>
          </div>
        </div>

        {/* Sim clock acceleration triggers */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800 text-xs">
          <span className="text-slate-400">Simulate Ladder Advance:</span>
          <button
            onClick={() => onAdvanceClock(30)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            +30 Days (Trigger T-30 Calls)
          </button>
          <button
            onClick={() => onAdvanceClock(60)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            +60 Days (T-60)
          </button>
          <button
            onClick={() => onAdvanceClock(83)}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            +83 Days (Trigger T-7 Urgent)
          </button>
          <button
            onClick={() => onAdvanceClock(300)}
            className="px-2.5 py-1 rounded bg-rose-950/50 hover:bg-rose-900/50 text-rose-300 border border-rose-800/60 transition"
          >
            +300 Days (Maturity & Escalation Ladder)
          </button>
        </div>
      </div>

      {/* Reminders Inbox Table */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Mail className="w-5 h-5 text-indigo-400" />
              Active Reminders & Automated Outreach Queue
            </h3>
            <span className="badge badge-l2">{reminders.length} Active</span>
          </div>

          <div className="flex items-center gap-1.5 p-1 bg-slate-900 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded-lg ${filter === 'all' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('urgent')}
              className={`px-3 py-1 rounded-lg ${filter === 'urgent' ? 'bg-amber-600 text-white' : 'text-slate-400'}`}
            >
              Urgent (T-7 / T-0)
            </button>
            <button
              onClick={() => setFilter('acknowledged')}
              className={`px-3 py-1 rounded-lg ${filter === 'acknowledged' ? 'bg-emerald-600 text-white' : 'text-slate-400'}`}
            >
              Acknowledged
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {filteredReminders.map((rem) => {
            const inst = instruments.find((i) => i.instrument_number === rem.instrument_number) || instruments[0];

            return (
              <div
                key={rem.id}
                className="p-4 rounded-xl bg-slate-900/70 border border-slate-700/60 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-600 transition-all"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-100 text-sm">{rem.instrument_number}</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        rem.window === 'T-0'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          : rem.window === 'T-7'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          : rem.window === 'T-30'
                          ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                          : 'bg-slate-700/50 text-slate-300'
                      }`}
                    >
                      {rem.window}
                    </span>
                    <span className="text-xs text-slate-400">• {rem.institution_name}</span>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1 text-slate-300">
                      <Clock className="w-3.5 h-3.5 text-slate-500" /> {rem.scheduled_for}
                    </span>
                    <span className="flex items-center gap-1 text-indigo-300">
                      <Volume2 className="w-3.5 h-3.5" /> Channel: {rem.current_channel}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-wrap items-center gap-2">
                  {rem.status !== 'acknowledged' ? (
                    <>
                      <button
                        onClick={() => onTriggerVoiceCall(inst)}
                        className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 shadow-md shadow-indigo-500/20"
                      >
                        <PhoneCall className="w-3.5 h-3.5 animate-pulse" />
                        AI Voice Call
                      </button>

                      <button
                        onClick={() => handleSnooze(rem.id, 7)}
                        className="btn-secondary text-xs px-2.5 py-1.5 text-slate-300 hover:text-white flex items-center gap-1"
                      >
                        <PauseCircle className="w-3.5 h-3.5" />
                        Snooze 7d
                      </button>

                      <button
                        onClick={() => handleAcknowledge(rem.id)}
                        className="btn-secondary text-xs px-3 py-1.5 text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Acknowledge
                      </button>
                    </>
                  ) : (
                    <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Acknowledged</span>
                      <span className="text-[10px] text-slate-500">({rem.acknowledged_at?.slice(0, 10)})</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
