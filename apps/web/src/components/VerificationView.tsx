import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  FileText,
  UploadCloud,
  AlertTriangle,
  Building,
  Download,
  SplitSquareVertical,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import { Instrument } from '../types';
import { formatPaiseINR } from '@aicte-fdr/shared';
import { api } from '../lib/apiClient';

interface VerificationViewProps {
  instruments: Instrument[];
}

interface StatementBatch {
  id: string;
  source_filename: string;
  format: string;
  total_lines: number;
  matched_lines: number;
  unmatched_lines: number;
  quarantined_lines: number;
  exception_count: number;
  created_at: string;
}

interface BankConfirmationRequest {
  id: string;
  instrument_id: string;
  bank_name: string;
  ifsc: string | null;
  tracking_number: string;
  status: string;
  requested_at: string;
  responded_at: string | null;
  decision: string | null;
}

interface Discrepancy {
  id: string;
  instrument_id: string;
  field: string;
  declared_value: string | null;
  extracted_value: string | null;
  severity: string;
  status: string;
}

const cardStyle: React.CSSProperties = {
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  borderRadius: '20px',
  padding: '24px',
  boxShadow: 'var(--shadow-card)',
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
};

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
              ledger-reconciled) per record, never collapsed into one score.
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

      {activeTab === 'statement' && <StatementTab />}
      {activeTab === 'bank_reply' && (
        <BankReplyTab
          instruments={instruments}
          selectedInstId={selectedInstId}
          setSelectedInstId={setSelectedInstId}
        />
      )}
      {activeTab === 'diff' && (
        <DiscrepancyTab
          instruments={instruments}
          selectedInstId={selectedInstId}
          setSelectedInstId={setSelectedInstId}
        />
      )}

      {activeTab === 'letters' && (
        <div style={cardStyle}>
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
              No instrument selected yet. Pick one from the Bank Confirmation tab.
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

// --- Bank Statement tab -----------------------------------------------

function StatementTab() {
  const [batches, setBatches] = useState<StatementBatch[] | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBatches = async () => {
    const { data, error: err } = await api.GET('/v1/statements/batches');
    if (err) {
      setError(extractErrorMessage(err, 'Could not load statement batches.'));
      return;
    }
    setBatches((data as unknown as StatementBatch[]) ?? []);
  };

  useEffect(() => {
    loadBatches();
  }, []);

  const handleUpload = async (file: File) => {
    setError(null);
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    const { error: err } = await api.POST('/v1/statements/import', {
      body: formData as unknown as { file: string },
      bodySerializer: (body) => body as unknown as BodyInit,
    });
    setUploading(false);
    if (err) {
      setError(extractErrorMessage(err, 'Statement import failed (not a recognised MT940/CAMT.053/CSV format, or you lack bureau-finance permission).'));
      return;
    }
    await loadBatches();
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
      <div style={cardStyle}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <UploadCloud size={18} color="var(--azure)" />
          Upload AICTE Statement
        </h3>
        <p style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.5 }}>
          Upload the official MT940/CAMT.053/CSV bank statement from AICTE's nodal account. The
          engine cross-matches UTR numbers, exact credits, and value dates against declared
          ONLINE_SD instruments; legacy FDR scans are never auto-reconciled this way.
        </p>
        <label
          style={{
            border: '2px dashed var(--border)',
            borderRadius: '16px',
            padding: '32px 16px',
            textAlign: 'center',
            background: 'var(--field)',
            cursor: uploading ? 'wait' : 'pointer',
            display: 'block',
          }}
        >
          {uploading ? (
            <Loader2 size={32} className="spin" color="var(--azure)" style={{ margin: '0 auto 10px auto' }} />
          ) : (
            <FileText size={32} color="var(--text3)" style={{ margin: '0 auto 10px auto' }} />
          )}
          <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text1)' }}>
            {uploading ? 'Importing & reconciling…' : 'Choose a statement file (MT940 / CAMT.053 / CSV)'}
          </p>
          <input
            type="file"
            accept=".csv,.txt,.xml,.sta,.mt940"
            style={{ display: 'none' }}
            disabled={uploading}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleUpload(f);
              e.target.value = '';
            }}
          />
        </label>
        {error && (
          <div style={{ display: 'flex', gap: '8px', fontSize: '12px', color: '#991B1B', background: '#FEF2F2', padding: '10px 12px', borderRadius: '10px' }}>
            <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: '1px' }} /> {error}
          </div>
        )}
      </div>

      <div style={cardStyle}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={18} color="var(--azure)" />
          Statement Matching Queue
        </h3>
        {batches === null ? (
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>Loading…</p>
        ) : batches.length === 0 ? (
          <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: '12px', color: 'var(--text3)', border: '1px dashed var(--border)', borderRadius: '16px', background: 'var(--field)' }}>
            No statement has been imported yet.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {batches.map((b) => (
              <div key={b.id} style={{ padding: '14px 16px', borderRadius: '14px', background: 'var(--field)', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
                  <strong style={{ fontSize: '13px', color: 'var(--text1)' }}>{b.source_filename}</strong>
                  <span style={{ fontSize: '11px', color: 'var(--text3)' }}>{new Date(b.created_at).toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', gap: '12px', marginTop: '6px', flexWrap: 'wrap', fontSize: '11px' }}>
                  <span style={{ color: 'var(--text2)' }}>{b.total_lines} lines</span>
                  <span style={{ color: '#15803D', fontWeight: 700 }}>{b.matched_lines} matched</span>
                  <span style={{ color: 'var(--text3)' }}>{b.unmatched_lines} unmatched</span>
                  {b.quarantined_lines > 0 && <span style={{ color: '#B91C1C', fontWeight: 700 }}>{b.quarantined_lines} quarantined</span>}
                  {b.exception_count > 0 && <span style={{ color: '#D97706', fontWeight: 700 }}>{b.exception_count} exceptions</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// --- Bank Confirmation tab ---------------------------------------------

function BankReplyTab({
  instruments,
  selectedInstId,
  setSelectedInstId,
}: {
  instruments: Instrument[];
  selectedInstId: string;
  setSelectedInstId: (id: string) => void;
}) {
  const [requests, setRequests] = useState<BankConfirmationRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const selectedInst = instruments.find((i) => i.id === selectedInstId) || instruments[0];

  const loadRequests = async () => {
    const { data, error: err } = await api.GET('/v1/verification/bank-requests');
    if (err) {
      setError(extractErrorMessage(err, 'Could not load bank confirmation requests.'));
      return;
    }
    setRequests((data as unknown as BankConfirmationRequest[]) ?? []);
  };

  useEffect(() => {
    loadRequests();
  }, []);

  const handleRequestConfirmation = async () => {
    if (!selectedInst) return;
    setError(null);
    setCreating(true);
    const { error: err } = await api.POST('/v1/verification/bank-requests', {
      body: {
        instrument_id: selectedInst.id,
        bank_name: selectedInst.bank_name,
        ifsc: selectedInst.branch_ifsc,
      },
    });
    setCreating(false);
    if (err) {
      setError(extractErrorMessage(err, 'Could not issue a bank confirmation request (bureau role required).'));
      return;
    }
    await loadRequests();
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
      <div style={cardStyle}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Building size={18} color="var(--azure)" />
          Issue Bank Confirmation Request
        </h3>
        <p style={{ fontSize: '12px', color: 'var(--text3)', lineHeight: 1.5 }}>
          Opens an official tracked request to the instrument's bank branch. A separate authorised
          decision (accept / reject / inconclusive) is required later; issuing the request never
          confirms evidence by itself.
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
        <button
          type="button"
          onClick={handleRequestConfirmation}
          disabled={!selectedInst || creating}
          style={{
            padding: '10px 20px',
            borderRadius: '9999px',
            background: selectedInst ? 'var(--ink)' : '#CBD5E1',
            color: '#FFFFFF',
            fontSize: '13px',
            fontWeight: 700,
            border: 'none',
            cursor: selectedInst ? 'pointer' : 'not-allowed',
            alignSelf: 'flex-start',
          }}
        >
          {creating ? 'Issuing…' : 'Request Confirmation'}
        </button>
        {error && (
          <div style={{ display: 'flex', gap: '8px', fontSize: '12px', color: '#991B1B', background: '#FEF2F2', padding: '10px 12px', borderRadius: '10px' }}>
            <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: '1px' }} /> {error}
          </div>
        )}
      </div>

      <div style={cardStyle}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={18} color="var(--azure)" />
          Bank Confirmation Requests
        </h3>
        {requests === null ? (
          <p style={{ fontSize: '12px', color: 'var(--text3)' }}>Loading…</p>
        ) : requests.length === 0 ? (
          <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: '12px', color: 'var(--text3)', border: '1px dashed var(--border)', borderRadius: '16px', background: 'var(--field)' }}>
            No bank confirmation request has been issued yet.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {requests.map((r) => {
              const inst = instruments.find((i) => i.id === r.instrument_id);
              return (
                <div key={r.id} style={{ padding: '14px 18px', borderRadius: '14px', background: 'var(--field)', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <div>
                    <span style={{ fontWeight: 700, color: 'var(--text1)', fontSize: '13px' }}>
                      {inst ? inst.instrument_number : r.instrument_id}
                    </span>
                    <p style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '2px' }}>
                      {r.bank_name} · {r.tracking_number}
                    </p>
                  </div>
                  <span
                    style={{
                      background: r.status === 'ACCEPTED' ? '#DCFCE7' : r.status === 'REJECTED' ? '#FEE2E2' : '#E0E7FF',
                      color: r.status === 'ACCEPTED' ? '#166534' : r.status === 'REJECTED' ? '#991B1B' : '#3730A3',
                      padding: '3px 10px',
                      borderRadius: '9999px',
                      fontSize: '11px',
                      fontWeight: 700,
                    }}
                  >
                    {r.status.replace(/_/g, ' ')}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// --- Discrepancies tab ---------------------------------------------

function DiscrepancyTab({
  instruments,
  selectedInstId,
  setSelectedInstId,
}: {
  instruments: Instrument[];
  selectedInstId: string;
  setSelectedInstId: (id: string) => void;
}) {
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const selectedInst = instruments.find((i) => i.id === selectedInstId) || instruments[0];

  const load = async (instrumentId: string) => {
    setDiscrepancies(null);
    const { data, error: err } = await api.GET('/v1/instruments/{instrument_id}/discrepancies', {
      params: { path: { instrument_id: instrumentId } },
    });
    if (err) {
      setError(extractErrorMessage(err, 'Could not evaluate discrepancies for this instrument.'));
      setDiscrepancies([]);
      return;
    }
    setDiscrepancies((data as unknown as Discrepancy[]) ?? []);
  };

  useEffect(() => {
    if (selectedInst) load(selectedInst.id);
  }, [selectedInst?.id]);

  const handleGenerateObservation = async (discrepancyId: string) => {
    if (!selectedInst) return;
    setBusyId(discrepancyId);
    const { error: err } = await api.POST(
      '/v1/instruments/{instrument_id}/discrepancies/{discrepancy_id}/generate-observation',
      { params: { path: { instrument_id: selectedInst.id, discrepancy_id: discrepancyId } } }
    );
    setBusyId(null);
    if (err) {
      setError(extractErrorMessage(err, 'Could not generate a scrutiny observation (bureau role required).'));
      return;
    }
    await load(selectedInst.id);
  };

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <SplitSquareVertical size={18} color="#D97706" />
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)' }}>
            Declared vs Confirmed Side-by-Side Diff
          </h3>
        </div>
        {instruments.length > 0 && (
          <select
            value={selectedInstId}
            onChange={(e) => setSelectedInstId(e.target.value)}
            style={{ background: 'var(--field)', border: '1px solid var(--border)', borderRadius: '10px', padding: '8px 10px', fontSize: '12px', color: 'var(--text1)' }}
          >
            {instruments.map((i) => (
              <option key={i.id} value={i.id}>
                {i.instrument_number}
              </option>
            ))}
          </select>
        )}
      </div>
      <p style={{ fontSize: '12px', color: 'var(--text3)' }}>
        Discrepancies identified when comparing institution self-declared FDR details against
        document-extracted (OCR) or bank-confirmed values. Re-evaluated live on every visit;
        never auto-rejects the instrument.
      </p>

      {error && (
        <div style={{ display: 'flex', gap: '8px', fontSize: '12px', color: '#991B1B', background: '#FEF2F2', padding: '10px 12px', borderRadius: '10px' }}>
          <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: '1px' }} /> {error}
        </div>
      )}

      {!selectedInst ? (
        <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: '12px', color: 'var(--text3)', border: '1px dashed var(--border)', borderRadius: '16px', background: 'var(--field)' }}>
          No instrument selected yet.
        </div>
      ) : discrepancies === null ? (
        <p style={{ fontSize: '12px', color: 'var(--text3)' }}>Evaluating…</p>
      ) : discrepancies.length === 0 ? (
        <div style={{ padding: '32px 16px', textAlign: 'center', fontSize: '12px', color: 'var(--text3)', border: '1px dashed var(--border)', borderRadius: '16px', background: 'var(--field)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <CheckCircle2 size={16} color="#15803D" /> No discrepancies found between declared and extracted values for {selectedInst.instrument_number}.
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ textAlign: 'left', color: 'var(--text3)', fontSize: '11px', textTransform: 'uppercase' }}>
              <th style={{ paddingBottom: '8px' }}>Field</th>
              <th style={{ paddingBottom: '8px' }}>Declared</th>
              <th style={{ paddingBottom: '8px' }}>Extracted</th>
              <th style={{ paddingBottom: '8px' }}>Severity</th>
              <th style={{ paddingBottom: '8px' }}>Status</th>
              <th style={{ paddingBottom: '8px' }} />
            </tr>
          </thead>
          <tbody>
            {discrepancies.map((d) => (
              <tr key={d.id} style={{ borderTop: '1px solid var(--border)' }}>
                <td style={{ padding: '10px 0', fontWeight: 700, color: 'var(--text1)' }}>{d.field}</td>
                <td style={{ padding: '10px 0', color: 'var(--text2)' }}>{d.declared_value ?? '—'}</td>
                <td style={{ padding: '10px 0', color: 'var(--text2)' }}>{d.extracted_value ?? '—'}</td>
                <td style={{ padding: '10px 0' }}>
                  <span style={{ color: d.severity === 'HIGH' ? '#B91C1C' : d.severity === 'MEDIUM' ? '#D97706' : 'var(--text3)', fontWeight: 700 }}>
                    {d.severity}
                  </span>
                </td>
                <td style={{ padding: '10px 0', color: 'var(--text2)' }}>{d.status}</td>
                <td style={{ padding: '10px 0' }}>
                  {d.status === 'OPEN' && (
                    <button
                      type="button"
                      onClick={() => handleGenerateObservation(d.id)}
                      disabled={busyId === d.id}
                      style={{
                        fontSize: '11px',
                        fontWeight: 700,
                        padding: '4px 10px',
                        borderRadius: '9999px',
                        border: '1px solid var(--border)',
                        background: 'var(--surface)',
                        color: 'var(--text1)',
                        cursor: busyId === d.id ? 'wait' : 'pointer',
                      }}
                    >
                      {busyId === d.id ? '…' : 'Generate observation'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object') {
    const e = error as Record<string, unknown>;
    if (typeof e.detail === 'string') return e.detail;
    if (typeof e.title === 'string') return e.title;
  }
  return fallback;
}
