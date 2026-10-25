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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '24px', padding: '28px', boxShadow: 'var(--shadow-card)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: 40, height: 40, borderRadius: '12px', background: 'var(--primary-container)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <HelpCircle size={20} color="var(--azure)" />
          </div>
          <div>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '22px', fontWeight: 800, color: 'var(--text1)' }}>Help, Support &amp; DPDP Rights</h1>
            <p style={{ marginTop: '2px', fontSize: '13px', color: 'var(--text3)' }}>
              Statutory guidance, grievance redressal, and DPDP Act 2023 data rights portal (F-21, F-22)
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '24px', background: 'var(--field)', padding: '4px', borderRadius: '14px', border: '1px solid var(--border)', width: 'fit-content' }}>
          <button
            onClick={() => setActiveTab('faq')}
            style={{
              padding: '8px 16px',
              borderRadius: '10px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              border: 'none',
              background: activeTab === 'faq' ? 'var(--surface)' : 'transparent',
              color: activeTab === 'faq' ? 'var(--text1)' : 'var(--text3)',
              boxShadow: activeTab === 'faq' ? 'var(--shadow-card)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            APH Handbook &amp; FAQs
          </button>
          <button
            onClick={() => setActiveTab('tickets')}
            style={{
              padding: '8px 16px',
              borderRadius: '10px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              border: 'none',
              background: activeTab === 'tickets' ? 'var(--surface)' : 'transparent',
              color: activeTab === 'tickets' ? 'var(--text1)' : 'var(--text3)',
              boxShadow: activeTab === 'tickets' ? 'var(--shadow-card)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            Grievances &amp; Tickets ({tickets.length})
          </button>
          <button
            onClick={() => setActiveTab('dpdp')}
            style={{
              padding: '8px 16px',
              borderRadius: '10px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              border: 'none',
              background: activeTab === 'dpdp' ? 'var(--surface)' : 'transparent',
              color: activeTab === 'dpdp' ? 'var(--text1)' : 'var(--text3)',
              boxShadow: activeTab === 'dpdp' ? 'var(--shadow-card)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            DPDP Data Rights &amp; Retention
          </button>
        </div>
      </div>

      {toastMessage && (
        <div style={{ padding: '14px 18px', borderRadius: '14px', background: '#ECFDF5', border: '1px solid #A7F3D0', color: '#065F46', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={16} color="#059669" />
          {toastMessage}
        </div>
      )}

      {/* Tab 1: FAQ & Knowledge Base */}
      {activeTab === 'faq' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {faqs.map((faq, idx) => (
            <div key={idx} style={{ padding: '22px', borderRadius: '20px', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--shadow-card)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                <FileText size={18} color="var(--azure)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <h3 style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text1)' }}>{faq.q}</h3>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.6, paddingLeft: '28px' }}>{faq.a}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tab 2: Tickets & Grievance Submission */}
      {activeTab === 'tickets' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {/* Create Ticket Form */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '20px', padding: '24px', boxShadow: 'var(--shadow-card)', height: 'fit-content', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '14px', fontWeight: 700, color: 'var(--text1)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Submit Formal Grievance</h2>
            <form onSubmit={handleCreateTicket} style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '12px' }}>
              <div>
                <label style={{ color: 'var(--text2)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Subject</label>
                <input
                  type="text"
                  value={ticketSubject}
                  onChange={(e) => setTicketSubject(e.target.value)}
                  placeholder="Summary of issue or regulatory query..."
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '12px', background: 'var(--field)', border: '1px solid var(--border)', color: 'var(--text1)', fontSize: '12px' }}
                  required
                />
              </div>

              <div>
                <label style={{ color: 'var(--text2)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Category</label>
                <select
                  value={ticketCategory}
                  onChange={(e) => setTicketCategory(e.target.value as any)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '12px', background: 'var(--field)', border: '1px solid var(--border)', color: 'var(--text1)', fontSize: '12px' }}
                >
                  <option value="handbook_query">Handbook Interpretation (APH)</option>
                  <option value="deposit_discrepancy">FDR Discrepancy Contestation</option>
                  <option value="release_escalation">Release / Refund Delay</option>
                  <option value="technical_issue">Portal Technical Assistance</option>
                </select>
              </div>

              <div>
                <label style={{ color: 'var(--text2)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Priority</label>
                <select
                  value={ticketPriority}
                  onChange={(e) => setTicketPriority(e.target.value as any)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '12px', background: 'var(--field)', border: '1px solid var(--border)', color: 'var(--text1)', fontSize: '12px' }}
                >
                  <option value="low">Low (General Query)</option>
                  <option value="medium">Medium (Standard)</option>
                  <option value="high">High (Urgent Escalation)</option>
                  <option value="statutory">Statutory Deadline Bound</option>
                </select>
              </div>

              <button
                type="submit"
                style={{
                  width: '100%',
                  marginTop: '8px',
                  padding: '12px',
                  borderRadius: '9999px',
                  fontWeight: 700,
                  background: 'var(--ink)',
                  color: '#FFFFFF',
                  fontSize: '13px',
                  border: 'none',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(17, 24, 39, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                <Send size={14} /> Submit Grievance
              </button>
            </form>
          </div>

          {/* Tickets List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '14px', fontWeight: 700, color: 'var(--text1)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Active Casework &amp; Tickets</h2>
            {tickets.map((t) => (
              <div key={t.id} style={{ padding: '18px 20px', borderRadius: '18px', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: 'var(--shadow-card)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 700, color: 'var(--azure)' }}>{t.id}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', background: 'var(--field)', color: 'var(--text2)', border: '1px solid var(--border)' }}>
                      {t.priority}
                    </span>
                    <span style={{ padding: '2px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', background: 'var(--primary-container)', color: 'var(--azure)' }}>
                      {t.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <h3 style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text1)' }}>{t.subject}</h3>
                <div style={{ fontSize: '11px', color: 'var(--text3)', display: 'flex', alignItems: 'center', gap: '16px' }}>
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Statutory Retention Schedule Table */}
          <div style={{ background: 'var(--surface)', borderRadius: '20px', border: '1px solid var(--border)', overflow: 'hidden', boxShadow: 'var(--shadow-card)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', background: 'var(--field)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Lock size={16} color="var(--azure)" />
              <h2 style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text1)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                DPDP Act 2023 Statutory Data Retention Schedules
              </h2>
            </div>
            <div style={{ padding: '20px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                <div style={{ padding: '16px', borderRadius: '14px', background: 'var(--field)', border: '1px solid var(--border)' }}>
                  <div style={{ fontWeight: 700, color: 'var(--text1)', fontSize: '13px' }}>Active Deposits</div>
                  <div style={{ color: 'var(--azure)', fontFamily: 'var(--font-mono)', marginTop: '4px', fontWeight: 800, fontSize: '14px' }}>7 Years post-discharge</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>Regulatory financial compliance</div>
                </div>
                <div style={{ padding: '16px', borderRadius: '14px', background: 'var(--field)', border: '1px solid var(--border)' }}>
                  <div style={{ fontWeight: 700, color: 'var(--text1)', fontSize: '13px' }}>Cryptographic Audit Logs</div>
                  <div style={{ color: '#059669', fontFamily: 'var(--font-mono)', marginTop: '4px', fontWeight: 800, fontSize: '14px' }}>Indefinite (WORM)</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>Ed25519 tamper-evident ledger</div>
                </div>
                <div style={{ padding: '16px', borderRadius: '14px', background: 'var(--field)', border: '1px solid var(--border)' }}>
                  <div style={{ fontWeight: 700, color: 'var(--text1)', fontSize: '13px' }}>Bank Statements</div>
                  <div style={{ color: '#7C3AED', fontFamily: 'var(--font-mono)', marginTop: '4px', fontWeight: 800, fontSize: '14px' }}>10 Years</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>Banking reconciliation audits</div>
                </div>
                <div style={{ padding: '16px', borderRadius: '14px', background: 'var(--field)', border: '1px solid var(--border)' }}>
                  <div style={{ fontWeight: 700, color: 'var(--text1)', fontSize: '13px' }}>Malicious Quarantine</div>
                  <div style={{ color: '#DC2626', fontFamily: 'var(--font-mono)', marginTop: '4px', fontWeight: 800, fontSize: '14px' }}>30 Days</div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>Automatic purge post-forensics</div>
                </div>
              </div>
            </div>
          </div>

          {/* Data Principal Rights Request Tracker */}
          <div style={{ background: 'var(--surface)', borderRadius: '20px', border: '1px solid var(--border)', overflow: 'hidden', boxShadow: 'var(--shadow-card)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', background: 'var(--field)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Shield size={16} color="var(--azure)" />
                <h2 style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text1)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Data Principal Rights Tracker (Section 11, 12, 13)
                </h2>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>Statutory Response Window: 30 Days</span>
            </div>

            <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {dpdpRequests.map((req) => (
                <div key={req.id} style={{ padding: '14px 18px', borderRadius: '14px', background: 'var(--field)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', fontSize: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--azure)' }}>{req.id}</span>
                      <span style={{ padding: '2px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', background: 'var(--surface)', color: 'var(--text2)', border: '1px solid var(--border)' }}>
                        {req.requestType.replace('_', ' ')}
                      </span>
                    </div>
                    <div style={{ marginTop: '4px', color: 'var(--text1)', fontWeight: 600 }}>{req.subjectName}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>Submitted: {req.submittedAt}</div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <span style={{ padding: '3px 10px', borderRadius: '9999px', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', background: req.status === 'processed' ? '#ECFDF5' : 'var(--primary-container)', color: req.status === 'processed' ? '#059669' : 'var(--azure)' }}>
                      {req.status.replace('_', ' ')}
                    </span>
                    <div style={{ marginTop: '4px', fontSize: '11px', color: 'var(--text3)' }}>
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
