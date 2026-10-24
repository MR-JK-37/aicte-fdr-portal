import React, { useState } from 'react';
import { Settings, Server, RefreshCw, AlertOctagon, CheckCircle2, ShieldCheck, Play, Activity } from 'lucide-react';
import { ConnectorHealth } from '../types';

export const AdminConsoleView: React.FC = () => {
  const [connectors, setConnectors] = useState<ConnectorHealth[]>([
    {
      id: 'conn_core_bank',
      name: 'Scheduled Commercial Banks Direct API Gateway',
      type: 'core_banking',
      status: 'healthy',
      latencyMs: 142,
      lastChecked: '2026-10-24 13:10 IST',
      details: 'SFMS/ISO 20022 message adapter active with mutual TLS',
    },
    {
      id: 'conn_pfms',
      name: 'Public Financial Management System (PFMS)',
      type: 'pfms',
      status: 'healthy',
      latencyMs: 230,
      lastChecked: '2026-10-24 13:12 IST',
      details: 'Treasury payout settlement reconciliation connector',
    },
    {
      id: 'conn_digilocker',
      name: 'DigiLocker Institutional Document Verification',
      type: 'digilocker',
      status: 'healthy',
      latencyMs: 310,
      lastChecked: '2026-10-24 13:15 IST',
      details: 'Trust deed & authorized signatory credential verification',
    },
    {
      id: 'conn_fcm',
      name: 'FCM HTTP v1 Android Push Pipeline',
      type: 'push_fcm',
      status: 'healthy',
      latencyMs: 85,
      lastChecked: '2026-10-24 13:20 IST',
      details: 'Google OAuth2 token auto-refreshed, zero canary leaks',
    },
    {
      id: 'conn_apns',
      name: 'Apple Push Notification Service (APNs)',
      type: 'push_apns',
      status: 'healthy',
      latencyMs: 95,
      lastChecked: '2026-10-24 13:20 IST',
      details: 'ES256 JWT authenticated HTTP/2 token tunnel',
    },
  ]);

  const [dlqItems, setDlqItems] = useState([
    {
      id: 'dlq-4019',
      recipientId: 'user-apex-01',
      channel: 'push_android',
      errorReason: 'FCM 400 BadDeviceToken (revocation recorded)',
      createdAt: '2026-10-24 07:12 IST',
      retryCount: 3,
      payloadPreview: '{"category":"deadline","title":"AICTE FDR Portal — Action Needed"}',
    },
    {
      id: 'dlq-4020',
      recipientId: 'user-delhi-02',
      channel: 'email',
      errorReason: 'Mail server connection timeout (504 Gateway Timeout)',
      createdAt: '2026-10-24 09:45 IST',
      retryCount: 3,
      payloadPreview: '{"category":"critical_workflow","title":"AICTE FDR Portal — Action Needed"}',
    },
  ]);

  const [replayingId, setReplayingId] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const handleReplayDlq = (id: string) => {
    setReplayingId(id);
    setTimeout(() => {
      setDlqItems((prev) => prev.filter((item) => item.id !== id));
      setReplayingId(null);
      setToast(`DLQ Item ${id} re-enqueued to transactional outbox.`);
      setTimeout(() => setToast(null), 4000);
    }, 800);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-purple-950/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                <Settings size={22} />
              </span>
              <h1 className="text-2xl font-bold tracking-tight text-white">System Admin & Connector Registry</h1>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Integrations monitoring, background scheduler leases, and dead-letter queue (DLQ) controls (F-19)
            </p>
          </div>
        </div>

        {/* System Diagnostics Health Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mt-6">
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400 uppercase">Scheduler Lease</div>
            <div className="mt-1 font-mono text-sm font-bold text-emerald-300 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              ACTIVE (LEASE_01)
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Heartbeat: 4s ago</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400 uppercase">Audit Chain Status</div>
            <div className="mt-1 font-mono text-sm font-bold text-cyan-300 flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-cyan-400" />
              VERIFIED (0 Tamper)
            </div>
            <div className="text-[10px] text-slate-500 mt-1">71 Chained Blocks</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400 uppercase">SSE Realtime Hub</div>
            <div className="mt-1 font-mono text-sm font-bold text-emerald-300 flex items-center gap-1.5">
              <Activity size={14} className="text-emerald-400" />
              ONLINE (15s Heartbeat)
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Catch-up Replay Active</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400 uppercase">Dead-Letter Queue</div>
            <div className="mt-1 font-mono text-sm font-bold text-amber-300 flex items-center gap-1.5">
              <AlertOctagon size={14} className="text-amber-400" />
              {dlqItems.length} Held Notices
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Admin Replay Available</div>
          </div>
        </div>
      </div>

      {toast && (
        <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 size={14} />
          {toast}
        </div>
      )}

      {/* Connector Registry */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server size={16} className="text-cyan-400" />
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              Integration & Connector Registry Health
            </h2>
          </div>
          <span className="text-[11px] text-slate-400">All Gateway Endpoints Active</span>
        </div>

        <div className="p-4 space-y-3">
          {connectors.map((c) => (
            <div
              key={c.id}
              className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white text-sm">{c.name}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-950 text-emerald-300 border border-emerald-800">
                    {c.status}
                  </span>
                </div>
                <p className="mt-1 text-slate-400 text-xs">{c.details}</p>
              </div>

              <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px] shrink-0">
                <span>Latency: <strong className="text-cyan-300">{c.latencyMs} ms</strong></span>
                <span>Checked: {c.lastChecked}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dead-Letter Queue (DLQ) Viewer & Replay */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertOctagon size={16} className="text-amber-400" />
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              Dead-Letter Queue (DLQ) Inspector & Manual Replay
            </h2>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">{dlqItems.length} Held Items</span>
        </div>

        {dlqItems.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            <CheckCircle2 size={24} className="mx-auto mb-2 text-emerald-400" />
            DLQ is clear. All domain events and notifications delivered or acknowledged.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-950/40">
                  <th className="py-3 px-4">DLQ ID</th>
                  <th className="py-3 px-4">Channel</th>
                  <th className="py-3 px-4">Error Reason</th>
                  <th className="py-3 px-4">Payload Preview</th>
                  <th className="py-3 px-4 text-center">Retries</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {dlqItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-900/60 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-cyan-300">{item.id}</td>
                    <td className="py-3 px-4 font-mono uppercase text-slate-300">{item.channel}</td>
                    <td className="py-3 px-4 text-red-300 font-medium">{item.errorReason}</td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400 truncate max-w-xs">
                      {item.payloadPreview}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-slate-400">{item.retryCount}</td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleReplayDlq(item.id)}
                        disabled={replayingId === item.id}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-cyan-950 text-cyan-300 border border-slate-700 hover:border-cyan-500/50 text-[11px] font-semibold transition-colors flex items-center gap-1 mx-auto disabled:opacity-50"
                      >
                        {replayingId === item.id ? (
                          <RefreshCw size={11} className="animate-spin" />
                        ) : (
                          <Play size={11} />
                        )}
                        Replay
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
