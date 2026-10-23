import React, { useState } from 'react';
import {
  ShieldCheck,
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Download,
  Building,
  RefreshCw,
  Search,
  ExternalLink,
  SplitSquareVertical,
  Check,
  X
} from 'lucide-react';
import { Instrument, Discrepancy, EvidenceLevel } from '../types';

interface VerificationViewProps {
  instruments: Instrument[];
  onPromoteEvidence: (id: string, newLevel: EvidenceLevel) => void;
  onAddAuditEntry: (action: string, entityId: string, details: any) => void;
}

export const VerificationView: React.FC<VerificationViewProps> = ({
  instruments,
  onPromoteEvidence,
  onAddAuditEntry,
}) => {
  const [activeTab, setActiveTab] = useState<'statement' | 'bank_reply' | 'diff' | 'letters'>('statement');
  const [selectedInstId, setSelectedInstId] = useState<string>(instruments[0]?.id || '');
  const [csvUploaded, setCsvUploaded] = useState(false);
  const [reconciling, setReconciling] = useState(false);
  const [reconciledCount, setReconciledCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');

  // Sample discrepancies for diff view
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[]>([
    {
      id: 'disc-1',
      instrument_id: instruments[1]?.id || 'inst-2',
      institution_name: 'Apex Institute of Technology',
      field_name: 'joint_account_holder',
      declared_value: 'Jointly with Member Secretary, AICTE',
      confirmed_value: 'Single account: Apex Educational Trust',
      severity: 'critical',
      status: 'open',
    },
    {
      id: 'disc-2',
      instrument_id: instruments[2]?.id || 'inst-3',
      institution_name: 'National College of Engineering',
      field_name: 'lien_marked',
      declared_value: 'Lien marked in favor of AICTE',
      confirmed_value: 'No lien registered on bank ledger',
      severity: 'critical',
      status: 'open',
    },
    {
      id: 'disc-3',
      instrument_id: instruments[0]?.id || 'inst-1',
      institution_name: 'Delhi Global Technical Campus',
      field_name: 'amount',
      declared_value: '₹35,00,000',
      confirmed_value: '₹35,00,000',
      severity: 'low',
      status: 'resolved',
    },
  ]);

  const selectedInst = instruments.find((i) => i.id === selectedInstId) || instruments[0];

  const handleSimulateCsvUpload = () => {
    setReconciling(true);
    setTimeout(() => {
      setCsvUploaded(true);
      setReconciling(false);
      setReconciledCount(4);
      // Promote matching instruments to L3
      instruments.forEach((inst) => {
        if (inst.utr_number) {
          onPromoteEvidence(inst.id, 'L3');
        }
      });
      onAddAuditEntry('STATEMENT_RECONCILIATION_COMPLETED', 'AICTE-BOI-STMT-2026', {
        matched_records: 4,
        unmatched_records: 1,
        total_credited_paise: 1600000000,
        evidence_promoted_to: 'L3',
      });
    }, 1200);
  };

  const handleResolveDiscrepancy = (id: string, action: 'resolved' | 'overridden') => {
    setDiscrepancies((prev) =>
      prev.map((d) => (d.id === id ? { ...d, status: action } : d))
    );
    onAddAuditEntry('DISCREPANCY_ACTION', id, {
      new_status: action,
      officer_notes: 'Verified with Bank Branch Manager via official email.',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-7 h-7 text-emerald-400" />
            Verification & Statement Reconciliation
          </h2>
          <p className="text-sm text-slate-400">
            Problem Statement Scenario 3: Bank confirmation tracking (L2) & AICTE bank statement UTR matching (L3 Gold Standard).
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900/80 rounded-xl border border-slate-700/60 text-xs">
          <button
            onClick={() => setActiveTab('statement')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'statement'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Bank Statement (L3)
          </button>
          <button
            onClick={() => setActiveTab('bank_reply')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'bank_reply'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Bank Confirmation (L2)
          </button>
          <button
            onClick={() => setActiveTab('diff')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'diff'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Discrepancies Diff ({discrepancies.filter((d) => d.status === 'open').length})
          </button>
          <button
            onClick={() => setActiveTab('letters')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              activeTab === 'letters'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Dispatch Letters
          </button>
        </div>
      </div>

      {/* Tab 1: AICTE Bank Statement CSV Reconciliation (L3) */}
      {activeTab === 'statement' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 glass-card p-6 space-y-4">
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-emerald-400" />
              Upload AICTE Statement CSV
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Upload the official bank statement CSV received from AICTE’s nodal account (Bank of India / SBI). The engine cross-matches <strong>UTR numbers</strong>, exact credits, and value dates to promote FDR records to <strong>L3 (Gold Standard)</strong>.
            </p>

            <div className="border-2 border-dashed border-slate-700/80 hover:border-emerald-500/50 rounded-xl p-6 text-center space-y-3 bg-slate-950/40 transition-colors">
              <FileText className="w-10 h-10 text-slate-500 mx-auto" />
              <div>
                <p className="text-xs font-medium text-slate-200">
                  {csvUploaded ? 'AICTE_NODAL_STATEMENT_OCT2026.csv' : 'Drag & drop or click to upload CSV'}
                </p>
                <p className="text-[10px] text-slate-500 mt-1">
                  Format: Txn Date, Value Date, Description/UTR, Debit, Credit, Balance
                </p>
              </div>

              <button
                disabled={reconciling}
                onClick={handleSimulateCsvUpload}
                className="btn-primary w-full py-2 text-xs flex items-center justify-center gap-2"
              >
                {reconciling ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Parsing & Matching UTRs...
                  </>
                ) : csvUploaded ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                    Re-upload Statement
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4" />
                    Simulate Statement Ingestion
                  </>
                )}
              </button>
            </div>

            {csvUploaded && (
              <div className="p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-500/30 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Reconciliation Success
                  </span>
                  <span className="badge badge-l3">L3 Certified</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                  <div>Matched UTRs: <strong className="text-emerald-400">{reconciledCount}</strong></div>
                  <div>Unmatched: <strong className="text-amber-400">1</strong></div>
                  <div>Amount Reconciled: <strong className="text-slate-100">₹1.60 Cr</strong></div>
                  <div>Confidence: <strong className="text-emerald-400">100%</strong></div>
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-2 glass-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-400" />
                Live Bank Statement Matching Queue
              </h3>
              <span className="text-xs text-slate-400">AICTE Current A/c No: 002110100049281</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-700/60 text-slate-400">
                    <th className="pb-3 font-semibold">UTR Reference</th>
                    <th className="pb-3 font-semibold">Institution / Bank</th>
                    <th className="pb-3 font-semibold">Credit Amount</th>
                    <th className="pb-3 font-semibold">Date</th>
                    <th className="pb-3 font-semibold">Match Status</th>
                    <th className="pb-3 font-semibold text-right">Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  <tr className="hover:bg-slate-800/30">
                    <td className="py-3 font-mono text-[11px] text-indigo-300">UTIB00029481902</td>
                    <td className="py-3">
                      <div className="font-medium text-slate-200">Delhi Global Technical Campus</div>
                      <div className="text-[10px] text-slate-400">Axis Bank • FDR #AXIS-FDR-99201</div>
                    </td>
                    <td className="py-3 font-medium text-slate-100">₹35,00,000</td>
                    <td className="py-3 text-slate-400">12 Oct 2026</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Exact UTR & Amount Match
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <span className="badge badge-l3">L3 Confirmed</span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-800/30">
                    <td className="py-3 font-mono text-[11px] text-indigo-300">SBIN00918273645</td>
                    <td className="py-3">
                      <div className="font-medium text-slate-200">Apex Institute of Technology</div>
                      <div className="text-[10px] text-slate-400">State Bank of India • FDR #SBI-881920</div>
                    </td>
                    <td className="py-3 font-medium text-slate-100">₹50,00,000</td>
                    <td className="py-3 text-slate-400">15 Oct 2026</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Exact UTR & Amount Match
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <span className="badge badge-l3">L3 Confirmed</span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-800/30">
                    <td className="py-3 font-mono text-[11px] text-indigo-300">HDFC99281726354</td>
                    <td className="py-3">
                      <div className="font-medium text-slate-200">National College of Engineering</div>
                      <div className="text-[10px] text-slate-400">HDFC Bank • FDR #HDFC-441029</div>
                    </td>
                    <td className="py-3 font-medium text-slate-100">₹40,00,000</td>
                    <td className="py-3 text-slate-400">18 Oct 2026</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Auto-Reconciled
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <span className="badge badge-l3">L3 Confirmed</span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-800/30 bg-amber-950/10">
                    <td className="py-3 font-mono text-[11px] text-amber-300">PUNB00192837465</td>
                    <td className="py-3">
                      <div className="font-medium text-slate-200">St. Mary’s Polytechnic College</div>
                      <div className="text-[10px] text-slate-400">Punjab National Bank • FDR #PNB-771829</div>
                    </td>
                    <td className="py-3 font-medium text-amber-300">₹25,00,000 (Expected ₹35L)</td>
                    <td className="py-3 text-slate-400">20 Oct 2026</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-1 text-[11px] text-amber-400 font-medium">
                        <AlertTriangle className="w-3.5 h-3.5" /> Shortfall of ₹10,00,000
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <span className="badge badge-l1">L1 Only</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Bank Confirmation Letter Tracking (L2) */}
      {activeTab === 'bank_reply' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 glass-card p-6 space-y-4">
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Building className="w-5 h-5 text-indigo-400" />
              Upload Bank Official Confirmation
            </h3>
            <p className="text-xs text-slate-400">
              When a bank branch replies to AICTE’s verification request via official letter or domain-authenticated email, upload the response here to upgrade the instrument to <strong>L2 (Bank Confirmed)</strong>.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Select Instrument</label>
                <select
                  value={selectedInstId}
                  onChange={(e) => setSelectedInstId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-200"
                >
                  {instruments.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.instrument_number} - {i.institution_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Bank Branch Ref / Dispatch No.</label>
                <input
                  type="text"
                  placeholder="e.g. SBI/NDLS/CRED/2026/8812"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div className="border border-slate-700/70 rounded-xl p-4 bg-slate-950/40 text-center space-y-2">
                <UploadCloud className="w-7 h-7 text-indigo-400 mx-auto" />
                <p className="text-xs text-slate-300 font-medium">Upload Bank Reply Letter / Signed Form</p>
                <p className="text-[10px] text-slate-500">PDF, JPG, PNG with branch seal and signatory verification</p>
              </div>

              <button
                onClick={() => {
                  onPromoteEvidence(selectedInst.id, 'L2');
                  onAddAuditEntry('BANK_CONFIRMATION_VERIFIED', selectedInst.id, {
                    instrument_number: selectedInst.instrument_number,
                    bank_branch: selectedInst.bank_name,
                    new_evidence_level: 'L2',
                  });
                  alert(`Promoted ${selectedInst.instrument_number} to Level 2 (L2 Bank Confirmed)!`);
                }}
                className="btn-primary w-full py-2 text-xs flex items-center justify-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4" />
                Validate & Promote to L2
              </button>
            </div>
          </div>

          <div className="lg:col-span-2 glass-card p-6 space-y-4">
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-400" />
              Instruments Awaiting L2 Bank Confirmation
            </h3>

            <div className="space-y-3">
              {instruments.map((inst) => (
                <div
                  key={inst.id}
                  className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60 flex flex-col md:flex-row md:items-center justify-between gap-3 hover:border-slate-600 transition-all"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-100 text-sm">{inst.instrument_number}</span>
                      <span className={`badge ${inst.evidence_level === 'L3' ? 'badge-l3' : inst.evidence_level === 'L2' ? 'badge-l2' : 'badge-l1'}`}>
                        {inst.evidence_level}
                      </span>
                      <span className="text-[11px] text-slate-400">({inst.bank_name})</span>
                    </div>
                    <p className="text-xs text-slate-300">{inst.institution_name}</p>
                    <p className="text-[11px] text-slate-400">
                      Amount: <strong>₹{(inst.amount / 100).toLocaleString('en-IN')}</strong> • Maturity: {inst.maturity_date}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {inst.evidence_level === 'L1' ? (
                      <button
                        onClick={() => {
                          onPromoteEvidence(inst.id, 'L2');
                          onAddAuditEntry('BANK_CONFIRMATION_RECEIVED', inst.id, {
                            instrument_number: inst.instrument_number,
                            evidence_level: 'L2',
                          });
                        }}
                        className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5"
                      >
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        Simulate L2 Reply
                      </button>
                    ) : (
                      <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4" /> Verified
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Declared vs Confirmed Diff View (Discrepancies) */}
      {activeTab === 'diff' && (
        <div className="glass-card p-6 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <SplitSquareVertical className="w-5 h-5 text-amber-400" />
                Declared vs Confirmed Side-by-Side Diff
              </h3>
              <p className="text-xs text-slate-400">
                Discrepancies identified when comparing institution self-declared FDR details against bank branch confirmations.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
                {discrepancies.filter((d) => d.status === 'open').length} Open Action Required
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {discrepancies.map((disc) => (
              <div
                key={disc.id}
                className={`p-4 rounded-xl border transition-all ${
                  disc.status === 'open'
                    ? 'bg-rose-950/20 border-rose-500/40'
                    : 'bg-slate-900/40 border-slate-700/40 opacity-70'
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className={`w-4 h-4 ${disc.status === 'open' ? 'text-rose-400' : 'text-slate-500'}`} />
                    <span className="font-semibold text-slate-200 text-sm">{disc.institution_name}</span>
                    <span className="text-xs text-slate-400">Field: <strong className="text-indigo-300">{disc.field_name}</strong></span>
                  </div>
                  <span
                    className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full ${
                      disc.status === 'open'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    }`}
                  >
                    {disc.status}
                  </span>
                </div>

                {/* Diff Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 rounded-lg bg-slate-950/60 border border-slate-800 mb-3 text-xs">
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-0.5">Declared by Institution:</span>
                    <div className="font-mono text-rose-300 bg-rose-950/30 p-2 rounded border border-rose-800/40">
                      - {disc.declared_value}
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-slate-400 block mb-0.5">Confirmed by Bank / Statement:</span>
                    <div className="font-mono text-emerald-300 bg-emerald-950/30 p-2 rounded border border-emerald-800/40">
                      + {disc.confirmed_value}
                    </div>
                  </div>
                </div>

                {disc.status === 'open' && (
                  <div className="flex items-center justify-end gap-2 text-xs">
                    <button
                      onClick={() => handleResolveDiscrepancy(disc.id, 'overridden')}
                      className="btn-secondary py-1 px-3 text-slate-300 hover:text-white"
                    >
                      Override with Justification
                    </button>
                    <button
                      onClick={() => handleResolveDiscrepancy(disc.id, 'resolved')}
                      className="btn-primary py-1 px-3 flex items-center gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" />
                      Mark Resolved
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Dispatch Letters Generator */}
      {activeTab === 'letters' && (
        <div className="glass-card p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-400" />
                AICTE Official Bank Verification Letter Generator
              </h3>
              <p className="text-xs text-slate-400">
                Generate official request letters dispatched to Bank Branch Managers under Section 10(k) of the AICTE Act.
              </p>
            </div>
            <button
              onClick={() => window.print()}
              className="btn-secondary text-xs flex items-center gap-1.5"
            >
              <Download className="w-4 h-4" /> Print / Save as PDF
            </button>
          </div>

          {/* Letter preview */}
          <div className="p-8 rounded-xl bg-white text-slate-900 shadow-2xl font-serif space-y-6 max-w-3xl mx-auto border border-slate-300">
            {/* AICTE Header */}
            <div className="text-center border-b pb-4 border-slate-300 space-y-1">
              <div className="text-xs tracking-widest uppercase font-sans font-bold text-slate-700">
                ALL INDIA COUNCIL FOR TECHNICAL EDUCATION
              </div>
              <div className="text-[10px] text-slate-500 font-sans">
                (A Statutory Body of the Government of India) • Nelson Mandela Marg, Vasant Kunj, New Delhi - 110070
              </div>
              <div className="text-xs font-bold font-sans text-indigo-900 mt-2">
                FINANCIAL INSTRUMENT VERIFICATION DIVISION
              </div>
            </div>

            <div className="flex justify-between text-xs font-sans text-slate-700">
              <div>
                <strong>Ref No:</strong> AICTE/FDR-VERIF/2026/OCT/0491<br />
                <strong>Date:</strong> 23 October 2026
              </div>
              <div className="text-right">
                <strong>CONFIDENTIAL</strong><br />
                Urgent Response Requested
              </div>
            </div>

            <div className="text-xs leading-relaxed space-y-2 text-slate-800">
              <p>To,<br />
              <strong>The Branch Manager,</strong><br />
              {selectedInst.bank_name}, {selectedInst.branch_ifsc}
              </p>

              <p className="pt-2">
                <strong>Subject:</strong> Verification of Fixed Deposit Receipt No. <u>{selectedInst.instrument_number}</u> pledged to AICTE.
              </p>

              <p>Sir/Madam,</p>

              <p>
                The institution <strong>{selectedInst.institution_name}</strong> has submitted Fixed Deposit Receipt No. <strong>{selectedInst.instrument_number}</strong> for the sum of <strong>₹{(selectedInst.amount / 100).toLocaleString('en-IN')}</strong> in joint name with AICTE towards the mandatory Security Deposit required under the AICTE Approval Process Handbook.
              </p>

              <p>
                Kindly verify your branch records and confirm the following particulars on your official letterhead:
              </p>

              <ol className="list-decimal pl-6 space-y-1 text-xs">
                <li>Whether the FDR is genuinely issued by your branch and free from prior lien or encumbrance.</li>
                <li>Whether the FDR is marked with lien in favor of <strong>Member Secretary, AICTE</strong>.</li>
                <li>Whether auto-renewal instructions upon maturity have been recorded on bank systems.</li>
                <li>Whether any premature withdrawal or loan against deposit has been granted without AICTE consent.</li>
              </ol>

              <p className="pt-4">
                Yours faithfully,<br />
                <br />
                <strong>(Authorised Signatory)</strong><br />
                Finance & Approvals Bureau, AICTE
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
