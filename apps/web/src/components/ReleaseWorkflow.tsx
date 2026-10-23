import React, { useState } from 'react';
import {
  KeyRound,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileCheck,
  ShieldAlert,
  ArrowRight,
  Download,
  Building,
  UserCheck,
  QrCode,
  Lock,
  Printer
} from 'lucide-react';
import { Instrument, AppRole, ReleaseChecklist } from '../types';

interface ReleaseWorkflowProps {
  instruments: Instrument[];
  userRole: AppRole;
  onAddAuditEntry: (action: string, entityId: string, details: any) => void;
}

export const ReleaseWorkflow: React.FC<ReleaseWorkflowProps> = ({
  instruments,
  userRole,
  onAddAuditEntry,
}) => {
  const [selectedInstId, setSelectedInstId] = useState<string>(instruments[0]?.id || '');
  const [makerNotes, setMakerNotes] = useState('');
  const [makerSubmitted, setMakerSubmitted] = useState(false);
  const [checkerApproved, setCheckerApproved] = useState(false);
  const [finalSigned, setFinalSigned] = useState(false);

  const selectedInst = instruments.find((i) => i.id === selectedInstId) || instruments[0];

  // Dynamic eligibility checklist based on instrument selected
  const checklist: ReleaseChecklist = {
    term_served: selectedInst.id === 'inst-1', // Delhi Global has served full 8-year term
    term_citation: 'APH Clause 6.46(a): Mandatory 8-year lock-in period for Engineering & Tech institutions.',
    no_open_discrepancies: selectedInst.id !== 'inst-2', // Apex has an open discrepancy
    discrepancy_citation: 'APH Clause 6.46(b): Zero open verification discrepancies or lien defects required.',
    no_pending_scrutiny: true,
    scrutiny_citation: 'APH Clause 6.46(c): All annual compliances cleared by Scrutiny Committee.',
    no_unpaid_penalties: selectedInst.id !== 'inst-4', // St. Mary has a shortfall/penalty
    penalty_citation: 'APH Clause 6.46(d): No outstanding shortfall penalties or show-cause proceedings.',
    eligible: selectedInst.id === 'inst-1',
  };

  const handleMakerSubmit = () => {
    setMakerSubmitted(true);
    onAddAuditEntry('RELEASE_MAKER_RECOMMENDATION_SUBMITTED', selectedInst.id, {
      officer_role: 'scrutiny_officer',
      notes: makerNotes || 'All 4 statutory checklist conditions verified against bank records.',
      eligible: checklist.eligible,
    });
  };

  const handleCheckerApprove = () => {
    setCheckerApproved(true);
    onAddAuditEntry('RELEASE_CHECKER_APPROVAL_RECORDED', selectedInst.id, {
      officer_role: 'regional_officer',
      decision: 'APPROVED',
      bank_mandate_verified: true,
    });
  };

  const handleFinalSign = () => {
    setFinalSigned(true);
    onAddAuditEntry('RELEASE_CERTIFICATE_ISSUED_CRYPTOGRAPHIC', selectedInst.id, {
      competent_authority: 'Member Secretary, AICTE',
      certificate_serial: 'AICTE-REL-2026-9921',
      qr_hash: 'sha256:d8a92b9182c81928374a81b291029384756c8b91a',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <KeyRound className="w-7 h-7 text-emerald-400" />
            Security Deposit Release & Dual Maker-Checker Workflow
          </h2>
          <p className="text-sm text-slate-400">
            Problem Statement Scenario 6: Statutory APH clause 6.46 verification, maker-checker authorization segregation, and cryptographic QR certificate release.
          </p>
        </div>

        {/* Current user role banner */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 text-xs">
          <span className="text-slate-400">Acting as Role:</span>
          <span className="badge badge-l2 capitalize font-semibold">{userRole.replace('_', ' ')}</span>
        </div>
      </div>

      {/* Select Instrument to Process */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Select FDR for Release Assessment:
            </label>
            <select
              value={selectedInstId}
              onChange={(e) => {
                setSelectedInstId(e.target.value);
                setMakerSubmitted(false);
                setCheckerApproved(false);
                setFinalSigned(false);
              }}
              className="bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-200 min-w-[320px]"
            >
              {instruments.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.instrument_number} — {i.institution_name} (₹{(i.amount / 100).toLocaleString('en-IN')})
                </option>
              ))}
            </select>
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-400 block">Overall Eligibility Result:</span>
            <span
              className={`text-sm font-bold inline-flex items-center gap-1.5 mt-0.5 ${
                checklist.eligible ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {checklist.eligible ? (
                <>
                  <CheckCircle2 className="w-4 h-4" /> Eligible for Release
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4" /> Non-Compliant / Ineligible
                </>
              )}
            </span>
          </div>
        </div>

        {/* Automated Compliance Checklist (APH Clause Citations) */}
        <div className="pt-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-indigo-400" />
            Automated Statutory Eligibility Checklist (AICTE APH 2026-27)
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {/* Condition 1 */}
            <div
              className={`p-3.5 rounded-xl border flex items-start gap-3 ${
                checklist.term_served
                  ? 'bg-emerald-950/20 border-emerald-500/40'
                  : 'bg-rose-950/20 border-rose-500/40'
              }`}
            >
              {checklist.term_served ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-0.5">
                <span className="font-semibold text-slate-200">1. Term Completion (8/10 Years)</span>
                <p className="text-[11px] text-slate-400 leading-tight">{checklist.term_citation}</p>
                <span className={`text-[10px] font-bold ${checklist.term_served ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {checklist.term_served ? 'COMPLIANT: 8 years 2 months completed' : 'FAIL: Lock-in tenure not completed'}
                </span>
              </div>
            </div>

            {/* Condition 2 */}
            <div
              className={`p-3.5 rounded-xl border flex items-start gap-3 ${
                checklist.no_open_discrepancies
                  ? 'bg-emerald-950/20 border-emerald-500/40'
                  : 'bg-rose-950/20 border-rose-500/40'
              }`}
            >
              {checklist.no_open_discrepancies ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-0.5">
                <span className="font-semibold text-slate-200">2. Zero Open Discrepancies</span>
                <p className="text-[11px] text-slate-400 leading-tight">{checklist.discrepancy_citation}</p>
                <span className={`text-[10px] font-bold ${checklist.no_open_discrepancies ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {checklist.no_open_discrepancies ? 'CLEARED: No active discrepancies' : 'DEFECT: Unresolved bank discrepancy exists'}
                </span>
              </div>
            </div>

            {/* Condition 3 */}
            <div
              className={`p-3.5 rounded-xl border flex items-start gap-3 ${
                checklist.no_pending_scrutiny
                  ? 'bg-emerald-950/20 border-emerald-500/40'
                  : 'bg-rose-950/20 border-rose-500/40'
              }`}
            >
              {checklist.no_pending_scrutiny ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-0.5">
                <span className="font-semibold text-slate-200">3. Scrutiny Clearance</span>
                <p className="text-[11px] text-slate-400 leading-tight">{checklist.scrutiny_citation}</p>
                <span className={`text-[10px] font-bold ${checklist.no_pending_scrutiny ? 'text-emerald-400' : 'text-rose-400'}`}>
                  CLEARED: No pending EOA or regional queries
                </span>
              </div>
            </div>

            {/* Condition 4 */}
            <div
              className={`p-3.5 rounded-xl border flex items-start gap-3 ${
                checklist.no_unpaid_penalties
                  ? 'bg-emerald-950/20 border-emerald-500/40'
                  : 'bg-rose-950/20 border-rose-500/40'
              }`}
            >
              {checklist.no_unpaid_penalties ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-0.5">
                <span className="font-semibold text-slate-200">4. Financial Dues & Penalties</span>
                <p className="text-[11px] text-slate-400 leading-tight">{checklist.penalty_citation}</p>
                <span className={`text-[10px] font-bold ${checklist.no_unpaid_penalties ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {checklist.no_unpaid_penalties ? 'CLEARED: Zero outstanding penalties' : 'HOLD: Unpaid penalty / shortfall'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3-Tier Maker-Checker Authorization Pipeline */}
      <div className="glass-card p-6 space-y-6">
        <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <UserCheck className="w-5 h-5 text-indigo-400" />
          Segregation of Duties: Maker-Checker Dual-Authorization Pipeline
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Tier 1: Maker (Scrutiny Officer) */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-700/60 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">Step 1 • Maker</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${makerSubmitted ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                {makerSubmitted ? 'Submitted' : 'Pending'}
              </span>
            </div>

            <div>
              <h4 className="text-sm font-bold text-slate-200">Scrutiny Officer Review</h4>
              <p className="text-xs text-slate-400 mt-0.5">Reviews checklist, audits bank letters, files recommendation</p>
            </div>

            <textarea
              disabled={makerSubmitted}
              value={makerNotes}
              onChange={(e) => setMakerNotes(e.target.value)}
              placeholder="Enter scrutiny observations & recommendation..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 min-h-[60px]"
            />

            <button
              disabled={makerSubmitted || !checklist.eligible}
              onClick={handleMakerSubmit}
              className="btn-primary w-full py-2 text-xs flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" />
              {makerSubmitted ? 'Submitted to Checker' : 'Recommend for Release'}
            </button>
          </div>

          {/* Tier 2: Checker (Regional Officer) */}
          <div className={`p-4 rounded-xl border space-y-3 transition-all ${makerSubmitted ? 'bg-slate-900/80 border-slate-700/60' : 'bg-slate-950/40 border-slate-800/40 opacity-60'}`}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">Step 2 • Checker</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${checkerApproved ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                {checkerApproved ? 'Approved' : 'Awaiting Maker'}
              </span>
            </div>

            <div>
              <h4 className="text-sm font-bold text-slate-200">Regional Officer Verification</h4>
              <p className="text-xs text-slate-400 mt-0.5">Validates institution bank mandate & prevents single-point compromise</p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950 text-[11px] text-slate-300 space-y-1">
              <div>Bank Branch: <strong>{selectedInst.bank_name}</strong></div>
              <div>IFSC Code: <strong>{selectedInst.branch_ifsc}</strong></div>
              <div>Refund Mandate: Verified via PFMS</div>
            </div>

            <button
              disabled={!makerSubmitted || checkerApproved}
              onClick={handleCheckerApprove}
              className="btn-secondary w-full py-2 text-xs flex items-center justify-center gap-1.5 text-emerald-400 hover:text-emerald-300 border-emerald-500/40 disabled:opacity-40"
            >
              <UserCheck className="w-4 h-4" />
              {checkerApproved ? 'Checker Approved' : 'Dual-Authorize Approval'}
            </button>
          </div>

          {/* Tier 3: Signer (Competent Authority / Member Secretary) */}
          <div className={`p-4 rounded-xl border space-y-3 transition-all ${checkerApproved ? 'bg-slate-900/80 border-slate-700/60' : 'bg-slate-950/40 border-slate-800/40 opacity-60'}`}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">Step 3 • Sign-Off</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${finalSigned ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                {finalSigned ? 'Certificate Issued' : 'Pending Sign-Off'}
              </span>
            </div>

            <div>
              <h4 className="text-sm font-bold text-slate-200">Competent Authority Order</h4>
              <p className="text-xs text-slate-400 mt-0.5">Cryptographic signature and automated QR release issuance</p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950 text-[11px] text-slate-300 space-y-1">
              <div>Signatory: <strong>Member Secretary, AICTE</strong></div>
              <div>Security: <strong>SHA-256 Chain + Keycloak OIDC</strong></div>
            </div>

            <button
              disabled={!checkerApproved || finalSigned}
              onClick={handleFinalSign}
              className="btn-primary w-full py-2 text-xs flex items-center justify-center gap-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-40"
            >
              <KeyRound className="w-4 h-4" />
              {finalSigned ? 'Signed & Dispatched' : 'Sign & Issue QR Certificate'}
            </button>
          </div>
        </div>
      </div>

      {/* Release Certificate Preview (when signed) */}
      {finalSigned && (
        <div className="glass-card p-6 space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <QrCode className="w-5 h-5 text-emerald-400" />
              Cryptographic AICTE Release Certificate & Bank Mandate
            </h3>
            <button
              onClick={() => window.print()}
              className="btn-secondary text-xs flex items-center gap-1.5"
            >
              <Printer className="w-4 h-4" /> Print / Save PDF
            </button>
          </div>

          <div className="p-8 rounded-xl bg-white text-slate-900 shadow-2xl font-serif space-y-6 max-w-2xl mx-auto border-4 border-double border-indigo-900">
            <div className="text-center border-b pb-4 border-slate-300">
              <div className="text-xs tracking-widest font-bold uppercase font-sans text-indigo-950">
                ALL INDIA COUNCIL FOR TECHNICAL EDUCATION
              </div>
              <div className="text-[10px] text-slate-600 font-sans">
                Statutory Body, Ministry of Education, Government of India
              </div>
              <h2 className="text-lg font-bold font-sans text-slate-900 mt-2 tracking-wide uppercase">
                Certificate of Security Deposit Release
              </h2>
              <div className="text-[11px] font-sans text-slate-500 font-mono">
                Serial No: AICTE/REL/2026/OCT/09921
              </div>
            </div>

            <div className="text-xs leading-relaxed font-sans text-slate-800 space-y-3">
              <p>
                This is to certify that the institution <strong>{selectedInst.institution_name}</strong> has successfully completed its mandatory lock-in tenure under AICTE Approval Process Handbook Clause 6.46 without any outstanding discrepancies, penal obligations, or regulatory violations.
              </p>

              <div className="p-3 bg-slate-50 rounded border border-slate-200 grid grid-cols-2 gap-2 text-[11px]">
                <div><strong>Instrument No:</strong> {selectedInst.instrument_number}</div>
                <div><strong>Principal Sum:</strong> ₹{(selectedInst.amount / 100).toLocaleString('en-IN')}</div>
                <div><strong>Issuing Bank:</strong> {selectedInst.bank_name}</div>
                <div><strong>IFSC:</strong> {selectedInst.branch_ifsc}</div>
              </div>

              <p>
                The lien marked in favor of the <strong>Member Secretary, AICTE</strong> on the above-mentioned deposit stands <strong>OFFICIALLY DISCHARGED AND RELEASED</strong>. The issuing bank is authorized to credit proceeds to the verified account of the trust.
              </p>
            </div>

            {/* QR code and digital signature block */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-200 font-sans text-xs">
              <div className="flex items-center gap-3">
                <div className="w-16 h-16 bg-slate-100 border border-slate-300 rounded flex items-center justify-center p-1">
                  <QrCode className="w-14 h-14 text-indigo-950" />
                </div>
                <div className="text-[10px] text-slate-500 space-y-0.5">
                  <div className="font-bold text-slate-700">Digital Verification QR</div>
                  <div className="font-mono text-[9px] text-indigo-900 truncate max-w-[160px]">
                    sha256:d8a92b9182c81928374a...
                  </div>
                  <div>Verify at: aicte-india.org/verify</div>
                </div>
              </div>

              <div className="text-right space-y-1">
                <div className="font-serif italic font-bold text-sm text-indigo-950">Digitally Signed</div>
                <div className="font-bold text-xs text-slate-800">Member Secretary</div>
                <div className="text-[10px] text-slate-500">All India Council for Technical Education</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
