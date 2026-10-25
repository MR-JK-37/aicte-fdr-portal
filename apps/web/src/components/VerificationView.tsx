import React, { useState } from 'react';
import {
  ShieldCheck,
  FileText,
  UploadCloud,
  AlertTriangle,
  Building,
  Download,
  SplitSquareVertical,
} from 'lucide-react';
import { Instrument } from '../types';
import { formatPaiseINR } from '@aicte-fdr/shared';

interface VerificationViewProps {
  instruments: Instrument[];
}

const NOT_WIRED_NOTE =
  'Not yet connected to the API. The backend already has statement import, bank-verification, and discrepancy endpoints (stream R4); this screen needs stream R3 to call them with real data — nothing here is simulated or invented.';

export const VerificationView: React.FC<VerificationViewProps> = ({ instruments }) => {
  const [activeTab, setActiveTab] = useState<'statement' | 'bank_reply' | 'diff' | 'letters'>(
    'statement'
  );
  const [selectedInstId, setSelectedInstId] = useState<string>(instruments[0]?.id || '');

  const selectedInst = instruments.find((i) => i.id === selectedInstId) || instruments[0];

  const tabs: { id: typeof activeTab; label: string }[] = [
    { id: 'statement', label: 'Bank Statement' },
    { id: 'bank_reply', label: 'Bank Confirmation' },
    { id: 'diff', label: 'Discrepancies' },
    { id: 'letters', label: 'Dispatch Letters' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '22px', fontWeight: 800, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShieldCheck size={24} color="var(--azure)" />
              Verification &amp; Statement Reconciliation
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text3)', marginTop: '4px' }}>
              Bank confirmation tracking and AICTE bank statement UTR matching. Evidence is shown as
              separate attributes (declared / document-extracted / bank-confirmed /
              ledger-reconciled) per record — never collapsed into one score.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '6px', background: 'var(--field)', padding: '4px', borderRadius: '12px', border: '1px solid var(--border)' }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: 'none',
                  background: activeTab === tab.id ? 'var(--surface)' : 'transparent',
                  color: activeTab === tab.id ? 'var(--text1)' : 'var(--text3)',
                  boxShadow: activeTab === tab.id ? 'var(--shadow-card)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {activeTab === 'statement' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '20px', padding: '24px', boxShadow: 'var(--shadow-card)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <UploadCloud size={18} color="var(--azure)" />
              Upload AICTE Statement
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.5 }}>
              Upload the official MT940/CAMT.053/CSV bank statement from AICTE's nodal account. The
              engine cross-matches UTR numbers, exact credits, and value dates against declared
              instruments.
            </p>
            <div style={{ border: '2px dashed var(--border)', borderRadius: '16px', padding: '32px 16px', textAlign: 'center', background: 'var(--field)' }}>
              <FileText size={32} color="var(--text3)" style={{ margin: '0 auto 10px auto' }} />
              <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text1)' }}>Temporarily unavailable</p>
              <p style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '4px' }}>{NOT_WIRED_NOTE}</p>
            </div>
          </div>

          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '20px', padding: '24px', boxShadow: 'var(--shadow-card)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={18} color="var(--azure)" />
              Statement Matching Queue
            </h3>
            <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: '12px', color: 'var(--text3)', border: '1px dashed var(--border)', borderRadius: '16px', background: 'var(--field)' }}>
              {NOT_WIRED_NOTE}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'bank_reply' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '20px', padding: '24px', boxShadow: 'var(--shadow-card)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building size={18} color="var(--azure)" />
              Upload Bank Official Confirmation
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.5 }}>
              When a bank branch replies to AICTE's verification request via official letter or
              domain-authenticated email, upload the response here to record a bank-confirmed
              evidence attribute.
            </p>
            {instruments.length > 0 ? (
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: '6px' }}>
                  Select Instrument
                </label>
                <select
                  value={selectedInstId}
                  onChange={(e) => setSelectedInstId(e.target.value)}
                  style={{ width: '100%', background: 'var(--field)', border: '1px solid var(--border)', borderRadius: '10px', padding: '10px', fontSize: '12px', color: 'var(--text1)' }}
                >
                  {instruments.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.instrument_number} - {i.institution_name}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <p style={{ fontSize: '12px', color: 'var(--text3)' }}>No instruments loaded yet.</p>
            )}
            <div style={{ border: '2px dashed var(--border)', borderRadius: '16px', padding: '24px', background: 'var(--field)', textAlign: 'center' }}>
              <UploadCloud size={28} color="var(--azure)" style={{ margin: '0 auto 8px auto' }} />
              <p style={{ fontSize: '11px', color: 'var(--text3)' }}>{NOT_WIRED_NOTE}</p>
            </div>
          </div>

          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '20px', padding: '24px', boxShadow: 'var(--shadow-card)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} color="var(--azure)" />
              Instruments Awaiting Bank Confirmation
            </h3>
            {instruments.length === 0 ? (
              <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: '12px', color: 'var(--text3)', border: '1px dashed var(--border)', borderRadius: '16px', background: 'var(--field)' }}>
                {NOT_WIRED_NOTE}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {instruments.map((inst) => (
                  <div
                    key={inst.id}
                    style={{ padding: '14px 18px', borderRadius: '14px', background: 'var(--field)', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}
                  >
                    <div>
                      <span style={{ fontWeight: 700, color: 'var(--text1)', fontSize: '13px' }}>
                        {inst.instrument_number}
                      </span>
                      <p style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '2px' }}>{inst.institution_name}</p>
                    </div>
                    <span style={{ background: '#E0E7FF', color: '#3730A3', padding: '3px 10px', borderRadius: '9999px', fontSize: '11px', fontWeight: 600 }}>
                      Awaiting Bank
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'diff' && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '20px', padding: '24px', boxShadow: 'var(--shadow-card)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <SplitSquareVertical size={18} color="#D97706" />
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)' }}>
              Declared vs Confirmed Side-by-Side Diff
            </h3>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>
            Discrepancies identified when comparing institution self-declared FDR details against
            bank branch confirmations or statement lines.
          </p>
          <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: '12px', color: 'var(--text3)', border: '1px dashed var(--border)', borderRadius: '16px', background: 'var(--field)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <AlertTriangle size={16} color="#D97706" />
            {NOT_WIRED_NOTE}
          </div>
        </div>
      )}

      {activeTab === 'letters' && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '20px', padding: '24px', boxShadow: 'var(--shadow-card)', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={18} color="var(--azure)" />
                AICTE Official Bank Verification Letter
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '2px' }}>
                Generate official request letters dispatched to bank branch managers under Section
                10(k) of the AICTE Act.
              </p>
            </div>
            {selectedInst && (
              <button
                onClick={() => window.print()}
                className="btn btn-secondary"
                style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Download size={14} /> Print / Save as PDF
              </button>
            )}
          </div>

          {!selectedInst ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: '12px', color: 'var(--text3)', border: '1px dashed var(--border)', borderRadius: '16px', background: 'var(--field)' }}>
              No instrument selected — {NOT_WIRED_NOTE}
            </div>
          ) : (
            <div style={{ padding: '32px', borderRadius: '16px', background: '#FFFFFF', color: '#0F172A', boxShadow: '0 4px 20px rgba(0,0,0,0.06)', fontFamily: 'serif', maxWidth: '720px', margin: '0 auto', border: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ textAlign: 'center', borderBottom: '1px solid #E2E8F0', paddingBottom: '16px' }}>
                <div style={{ fontSize: '13px', letterSpacing: '2px', textTransform: 'uppercase', fontFamily: 'sans-serif', fontWeight: 800, color: '#1E293B' }}>
                  ALL INDIA COUNCIL FOR TECHNICAL EDUCATION
                </div>
                <div style={{ fontSize: '10px', color: '#64748B', fontFamily: 'sans-serif', marginTop: '2px' }}>
                  (A Statutory Body of the Government of India)
                </div>
              </div>
              <div style={{ fontSize: '13px', lineHeight: 1.8, color: '#334155' }}>
                <p>
                  To,
                  <br />
                  <strong>The Branch Manager,</strong>
                  <br />
                  {selectedInst.bank_name}, {selectedInst.branch_ifsc}
                </p>
                <p style={{ paddingTop: '12px' }}>
                  <strong>Subject:</strong> Verification of Fixed Deposit Receipt No.{' '}
                  <u>{selectedInst.instrument_number}</u> pledged to AICTE.
                </p>
                <p>
                  The institution <strong>{selectedInst.institution_name}</strong> has submitted
                  Fixed Deposit Receipt No. <strong>{selectedInst.instrument_number}</strong> for
                  the sum of{' '}
                  <strong>{formatPaiseINR(selectedInst.amount)}</strong> towards
                  the mandatory Security Deposit required under the AICTE Approval Process
                  Handbook.
                </p>
                <p style={{ paddingTop: '20px' }}>
                  Yours faithfully,
                  <br />
                  <strong>(Authorised Signatory)</strong>
                  <br />
                  Finance &amp; Approvals Bureau, AICTE
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
