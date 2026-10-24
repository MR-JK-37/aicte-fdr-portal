import React, { useState } from 'react';
import { HelpCircle, Shield, FileText, Send, CheckCircle2, AlertCircle, Clock, ChevronRight, Lock } from 'lucide-react';
import { SupportTicket, DPDPRightsRequest } from '../types';

export const HelpAndRightsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'faq' | 'tickets' | 'dpdp'>('faq');
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketCategory, setTicketCategory] = useState<SupportTicket['category']>('handbook_query');
  const [ticketPriority, setTicketPriority] = useState<SupportTicket['priority']>('medium');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const [tickets, setTickets] = useState<SupportTicket[]>([
    {
      id: 'TICK-9021',
      subject: 'Clarification regarding Table 1.4 security deposit norms for integrated campus',
      category: 'handbook_query',
      priority: 'medium',
      status: 'under_scrutiny',
      createdAt: '2026-10-23 11:20 IST',
      updatedAt: '2026-10-24 09:30 IST',
    },
    {
      id: 'TICK-9022',
      subject: 'Discrepancy in joint account holder name on renewal FDR with branch',
      category: 'deposit_discrepancy',
      priority: 'high',
      status: 'open',
      createdAt: '2026-10-24 08:15 IST',
      updatedAt: '2026-10-24 08:15 IST',
    },
  ]);

  const [dpdpRequests, setDpdpRequests] = useState<DPDPRightsRequest[]>([
    {
      id: 'DPDP-2026-001',
      requestType: 'access_data',
      subjectName: 'Chairman / Authorized Signatory (Apex Institute)',
      status: 'processed',
      submittedAt: '2026-10-18 14:00 IST',
      statutoryDaysRemaining: 0,
    },
    {
      id: 'DPDP-2026-002',
      requestType: 'rectify_record',
      subjectName: 'Principal (Delhi Global Technical Campus)',
      status: 'under_review',
      submittedAt: '2026-10-22 10:30 IST',
      statutoryDaysRemaining: 26,
    },
  ]);

  const faqs = [
    {
      q: 'What are the statutory security deposit requirements under APH Table 1.4?',
      a: 'Security deposits must be submitted via Fixed Deposit Receipt (FDR) or Bank Guarantee pledged jointly in the name of the Regional Officer, AICTE and the applicant Trust/Society for a minimum statutory tenure of 8 to 10 years depending on the program approval category.',
    },
    {
      q: 'Why was my FDR marked with a Discrepancy?',
      a: 'A discrepancy is automatically flagged if the scanned OCR values differ from the direct branch confirmation (L2) or the bank statement reconciliation (L3), such as single account holder instead of joint holding, shortfall in paise value, or IFSC branch mismatch.',
    },
    {
      q: 'What is the Clause 6.46 release checklist procedure?',
      a: 'Clause 6.46 requires verification that the term has been served, zero open discrepancies exist, no unpaid penalties remain, and multi-cell clearances (PGRC, Vigilance, Legal, Regional Office) are satisfied prior to Competent Authority authorization and dual-person execution proof verification.',
    },
    {
      q: 'How does the portal adhere to the Digital Personal Data Protection (DPDP) Act 2023?',
      a: 'The portal enforces purpose limitation, role-based scope isolation, WORM cryptographic audit logs, lock-screen notification privacy (no PII on lock screens), and provides data principals statutory rights to data access, rectification, and grievance redressal.',
    },
  ];

  const handleCreateTicket = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketSubject.trim()) return;

    const newTicket: SupportTicket = {
      id: `TICK-${Math.floor(Math.random() * 9000) + 1000}`,
      subject: ticketSubject.trim(),
      category: ticketCategory,
      priority: ticketPriority,
      status: 'open',
      createdAt: new Date().toLocaleString('en-IN', { hour12: false }) + ' IST',
      updatedAt: new Date().toLocaleString('en-IN', { hour12: false }) + ' IST',
    };

    setTickets((prev) => [newTicket, ...prev]);
    setTicketSubject('');
    setToastMessage(`Support ticket ${newTicket.id} submitted to AICTE Helpdesk.`);
    setTimeout(() => setToastMessage(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-purple-950/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                <HelpCircle size={22} />
              </span>
              <h1 className="text-2xl font-bold tracking-tight text-white">Help, Support & DPDP Rights</h1>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Statutory guidance, grievance redressal, and DPDP Act 2023 data rights portal (F-21, F-22)
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 mt-6 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab('faq')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'faq'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            APH Handbook & FAQs
          </button>
          <button
            onClick={() => setActiveTab('tickets')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'tickets'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Grievances & Tickets ({tickets.length})
          </button>
          <button
            onClick={() => setActiveTab('dpdp')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'dpdp'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            DPDP Data Rights & Retention
          </button>
        </div>
      </div>

      {toastMessage && (
        <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 size={14} />
          {toastMessage}
        </div>
      )}

      {/* Tab 1: FAQ & Knowledge Base */}
      {activeTab === 'faq' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {faqs.map((faq, idx) => (
            <div key={idx} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
              <div className="flex items-start gap-2.5">
                <FileText size={18} className="text-cyan-400 shrink-0 mt-0.5" />
                <h3 className="font-semibold text-sm text-white">{faq.q}</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed pl-7">{faq.a}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tab 2: Tickets & Grievance Submission */}
      {activeTab === 'tickets' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Create Ticket Form */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4 bg-slate-900/50 h-fit">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Submit Formal Grievance</h2>
            <form onSubmit={handleCreateTicket} className="space-y-4 text-xs">
              <div>
                <label className="text-slate-400 font-semibold block mb-1">Subject</label>
                <input
                  type="text"
                  value={ticketSubject}
                  onChange={(e) => setTicketSubject(e.target.value)}
                  placeholder="Summary of issue or regulatory query..."
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white focus:outline-none focus:border-cyan-400 text-xs"
                  required
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Category</label>
                <select
                  value={ticketCategory}
                  onChange={(e) => setTicketCategory(e.target.value as any)}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white focus:outline-none focus:border-cyan-400 text-xs"
                >
                  <option value="handbook_query">Handbook Interpretation (APH)</option>
                  <option value="deposit_discrepancy">FDR Discrepancy Contestation</option>
                  <option value="release_escalation">Release / Refund Delay</option>
                  <option value="technical_issue">Portal Technical Assistance</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Priority</label>
                <select
                  value={ticketPriority}
                  onChange={(e) => setTicketPriority(e.target.value as any)}
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white focus:outline-none focus:border-cyan-400 text-xs"
                >
                  <option value="low">Low (General Query)</option>
                  <option value="medium">Medium (Standard)</option>
                  <option value="high">High (Urgent Escalation)</option>
                  <option value="statutory">Statutory Deadline Bound</option>
                </select>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-xl font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 flex items-center justify-center gap-2 transition-colors"
              >
                <Send size={14} /> Submit Grievance
              </button>
            </form>
          </div>

          {/* Tickets List */}
          <div className="lg:col-span-2 space-y-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Active Casework & Tickets</h2>
            {tickets.map((t) => (
              <div key={t.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-cyan-300">{t.id}</span>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-300 border border-slate-700">
                      {t.priority}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan-950 text-cyan-300 border border-cyan-800">
                      {t.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <h3 className="font-semibold text-sm text-white">{t.subject}</h3>
                <div className="text-[11px] text-slate-500 flex items-center gap-4">
                  <span>Created: {t.createdAt}</span>
                  <span>Updated: {t.updatedAt}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: DPDP Rights & Retention */}
      {activeTab === 'dpdp' && (
        <div className="space-y-6">
          {/* Statutory Retention Schedule Table */}
          <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center gap-2">
              <Lock size={16} className="text-cyan-400" />
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                DPDP Act 2023 Statutory Data Retention Schedules
              </h2>
            </div>
            <div className="p-4 space-y-3 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="font-semibold text-white">Active Deposits</div>
                  <div className="text-cyan-400 font-mono mt-1 font-bold">7 Years post-discharge</div>
                  <div className="text-[11px] text-slate-400 mt-1">Regulatory financial compliance</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="font-semibold text-white">Cryptographic Audit Logs</div>
                  <div className="text-emerald-400 font-mono mt-1 font-bold">Indefinite (WORM)</div>
                  <div className="text-[11px] text-slate-400 mt-1">Ed25519 tamper-evident ledger</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="font-semibold text-white">Bank Statements</div>
                  <div className="text-purple-400 font-mono mt-1 font-bold">10 Years</div>
                  <div className="text-[11px] text-slate-400 mt-1">Banking reconciliation audits</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="font-semibold text-white">Malicious Quarantine</div>
                  <div className="text-red-400 font-mono mt-1 font-bold">30 Days</div>
                  <div className="text-[11px] text-slate-400 mt-1">Automatic purge post-forensics</div>
                </div>
              </div>
            </div>
          </div>

          {/* Data Principal Rights Request Tracker */}
          <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield size={16} className="text-cyan-400" />
                <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                  Data Principal Rights Tracker (Section 11, 12, 13)
                </h2>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">Statutory Response Window: 30 Days</span>
            </div>

            <div className="p-4 space-y-3">
              {dpdpRequests.map((req) => (
                <div key={req.id} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-cyan-300">{req.id}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-300">
                        {req.requestType.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="mt-1 text-slate-300 font-medium">{req.subjectName}</div>
                    <div className="text-[11px] text-slate-500">Submitted: {req.submittedAt}</div>
                  </div>

                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan-950 text-cyan-300 border border-cyan-800">
                      {req.status.replace('_', ' ')}
                    </span>
                    <div className="mt-1 text-[11px] text-slate-400">
                      {req.statutoryDaysRemaining > 0 ? `${req.statutoryDaysRemaining} days remaining` : 'Completed'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
