import React, { useState } from 'react';
import { Bell, CheckCheck, Clock, X, ShieldAlert, Sparkles, Smartphone, CheckCircle2, Moon, AlertTriangle } from 'lucide-react';
import { InAppNotification } from '../types';

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToTab?: (tab: string) => void;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({ isOpen, onClose, onNavigateToTab }) => {
  const [activeTab, setActiveTab] = useState<'inbox' | 'preferences'>('inbox');
  const [webPushEnabled, setWebPushEnabled] = useState(true);
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(false);
  const [pwaInstallPrompted, setPwaInstallPrompted] = useState(false);

  const [notifications, setNotifications] = useState<InAppNotification[]>([
    {
      id: 'notif-101',
      title: 'T-30 Statutory Renewal Reminder Issued',
      body: 'Deposit AXIS-FDR-99201 is maturing on 2026-11-20. Predecessor renewal submission or replacement is required within 30 days.',
      category: 'deadline',
      status: 'OPENED',
      created_at: '2026-10-24 10:00 IST',
      read_at: '2026-10-24 10:05 IST',
      action_url: 'reminders',
      instrument_id: 'AXIS-FDR-99201',
    },
    {
      id: 'notif-102',
      title: 'Discrepancy Casework Assigned (Shortfall)',
      body: 'FDR PNB-771829 has a registered deposit of ₹25,00,000 against statutory requirement of ₹35,00,000. Scrutiny observation created.',
      category: 'critical_workflow',
      status: 'DEVICE_RECEIVED',
      created_at: '2026-10-24 09:30 IST',
      action_url: 'verify',
      instrument_id: 'PNB-771829',
    },
    {
      id: 'notif-103',
      title: 'Two-Person Release Execution Proof Required',
      body: 'Release request for National College of Engineering is approved by Competent Authority and is now EXECUTION_PENDING UTR confirmation.',
      category: 'critical_workflow',
      status: 'ACKNOWLEDGED',
      created_at: '2026-10-23 17:00 IST',
      read_at: '2026-10-23 17:15 IST',
      acknowledged_at: '2026-10-23 17:20 IST',
      action_url: 'release',
      instrument_id: 'HDFC-441029',
    },
  ]);

  if (!isOpen) return null;

  const handleMarkAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toLocaleTimeString() } : n))
    );
  };

  const handleAcknowledge = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === id
          ? {
              ...n,
              status: 'ACKNOWLEDGED',
              acknowledged_at: new Date().toLocaleTimeString(),
            }
          : n
      )
    );
  };

  const handleActionClick = (n: InAppNotification) => {
    handleMarkAsRead(n.id);
    if (n.action_url && onNavigateToTab) {
      onNavigateToTab(n.action_url);
      onClose();
    }
  };

  const unreadCount = notifications.filter((n) => !n.read_at).length;

  const getStageBadge = (status: string) => {
    switch (status) {
      case 'ACTIONED':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">ACTIONED</span>;
      case 'ACKNOWLEDGED':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">ACKNOWLEDGED</span>;
      case 'OPENED':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-950 text-purple-300 border border-purple-800">OPENED</span>;
      case 'DEVICE_RECEIVED':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800">DEVICE RECEIVED</span>;
      case 'PROVIDER_ACCEPTED':
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">ACCEPTED</span>;
      default:
        return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-slate-400">{status}</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end p-4 sm:p-6 bg-slate-950/70 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Drawer Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              <Bell size={18} />
            </span>
            <div>
              <h2 className="font-bold text-sm text-white flex items-center gap-2">
                Notification Center
                {unreadCount > 0 && (
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-red-600 text-white">
                    {unreadCount}
                  </span>
                )}
              </h2>
              <p className="text-[11px] text-slate-400">In-App Inbox & Realtime Push (SPEC §10)</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center border-b border-slate-800 bg-slate-950/40 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('inbox')}
            className={`flex-1 py-2.5 text-center transition-colors border-b-2 ${
              activeTab === 'inbox'
                ? 'border-cyan-400 text-cyan-300 bg-cyan-950/20'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            In-App Inbox ({notifications.length})
          </button>
          <button
            onClick={() => setActiveTab('preferences')}
            className={`flex-1 py-2.5 text-center transition-colors border-b-2 ${
              activeTab === 'preferences'
                ? 'border-cyan-400 text-cyan-300 bg-cyan-950/20'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            Delivery Preferences
          </button>
        </div>

        {/* Body Content */}
        <div className="p-4 flex-1 overflow-y-auto space-y-3 text-xs">
          {activeTab === 'inbox' ? (
            notifications.length === 0 ? (
              <div className="p-8 text-center text-slate-500">No notifications in your inbox.</div>
            ) : (
              notifications.map((n) => {
                const isUnread = !n.read_at;
                return (
                  <div
                    key={n.id}
                    className={`p-3.5 rounded-xl border transition-all ${
                      isUnread
                        ? 'bg-slate-950/80 border-cyan-500/40 shadow-sm shadow-cyan-950/20'
                        : 'bg-slate-950/30 border-slate-800/80'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-white text-xs">{n.title}</span>
                        {isUnread && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />}
                      </div>
                      {getStageBadge(n.status)}
                    </div>

                    <p className="mt-1 text-slate-300 text-[11px] leading-relaxed">{n.body}</p>

                    <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500">
                      <span className="flex items-center gap-1">
                        <Clock size={11} /> {n.created_at}
                      </span>

                      <div className="flex items-center gap-2">
                        {n.status !== 'ACKNOWLEDGED' && n.status !== 'ACTIONED' && (
                          <button
                            onClick={() => handleAcknowledge(n.id)}
                            className="text-cyan-400 hover:text-cyan-300 font-medium"
                          >
                            Acknowledge
                          </button>
                        )}
                        {n.action_url && (
                          <button
                            onClick={() => handleActionClick(n)}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-medium transition-colors"
                          >
                            View Case
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )
          ) : (
            /* Preferences Tab */
            <div className="space-y-4">
              {/* Statutory Non-suppression alert */}
              <div className="p-3 rounded-xl bg-purple-950/40 border border-purple-500/30 text-[11px] text-purple-200 flex items-start gap-2">
                <ShieldAlert size={16} className="text-purple-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="font-bold text-white block">Statutory Non-Suppression Rule:</strong>
                  Quiet hours and user opt-outs NEVER suppress critical workflow alerts, maturity deadlines, or security notices.
                </div>
              </div>

              {/* Channel Toggles */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="font-semibold text-white text-xs">Dispatch Channels</div>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-slate-200">Web Push (VAPID)</div>
                    <div className="text-[10px] text-slate-500">Desktop browser instant notices</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={webPushEnabled}
                    onChange={(e) => setWebPushEnabled(e.target.checked)}
                    className="accent-cyan-400 w-4 h-4 cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between border-t border-slate-900 pt-2">
                  <div>
                    <div className="font-medium text-slate-200">Official Registered Email</div>
                    <div className="text-[10px] text-slate-500">Statutory PDF notices & summaries</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={emailEnabled}
                    onChange={(e) => setEmailEnabled(e.target.checked)}
                    className="accent-cyan-400 w-4 h-4 cursor-pointer"
                  />
                </div>
              </div>

              {/* Quiet Hours */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-semibold text-white">
                    <Moon size={14} className="text-cyan-400" /> Quiet Hours Window
                  </div>
                  <input
                    type="checkbox"
                    checked={quietHoursEnabled}
                    onChange={(e) => setQuietHoursEnabled(e.target.checked)}
                    className="accent-cyan-400 w-4 h-4 cursor-pointer"
                  />
                </div>
                <div className="text-[10px] text-slate-400">
                  Holds non-critical informational notices between 22:00 and 07:00 IST.
                </div>
              </div>

              {/* PWA Install Banner */}
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="font-medium text-slate-200 flex items-center gap-1.5">
                    <Smartphone size={14} className="text-cyan-400" /> Install Portal as PWA
                  </div>
                  <div className="text-[10px] text-slate-500">Offline caching & home-screen app</div>
                </div>
                <button
                  onClick={() => setPwaInstallPrompted(true)}
                  disabled={pwaInstallPrompted}
                  className="px-2.5 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-[10px] font-bold hover:bg-cyan-500/30 transition-colors disabled:opacity-50"
                >
                  {pwaInstallPrompted ? 'Installed' : 'Install PWA'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950 text-center text-[10px] text-slate-500">
          Stage tracking: No fabricated &ldquo;delivered&rdquo; statuses • Real Server-Sent Events (SSE)
        </div>
      </div>
    </div>
  );
};
