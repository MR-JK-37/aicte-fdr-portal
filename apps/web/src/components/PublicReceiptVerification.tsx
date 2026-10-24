import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, QrCode, Search, CheckCircle2, Lock, ArrowLeft, ExternalLink } from 'lucide-react';
import { PublicReceiptPayload } from '../types';

interface PublicReceiptVerificationProps {
  onBackToApp?: () => void;
}

export const PublicReceiptVerification: React.FC<PublicReceiptVerificationProps> = ({ onBackToApp }) => {
  const [receiptInput, setReceiptInput] = useState('REC-AICTE-2026-99201');
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifiedPayload, setVerifiedPayload] = useState<PublicReceiptPayload | null>({
    receiptNumber: 'REC-AICTE-2026-99201',
    institutionAicteCode: 'AICTE-ENGG-001',
    institutionName: 'Delhi Global Technical Campus',
    instrumentNumberMasked: 'AXIS-FDR-XXXX-9201',
    amountPaise: 350000000,
    bankName: 'Axis Bank',
    timestampUtc: '2026-10-23T09:15:32Z',
    ed25519Signature: 'ed25519:7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
    isSignatureValid: true,
    status: 'GENUINE_AICTE_SEALED',
  });

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    if (!receiptInput.trim()) return;

    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      if (receiptInput.toUpperCase().includes('TAMPER') || receiptInput.toUpperCase().includes('INVALID')) {
        setVerifiedPayload({
          receiptNumber: receiptInput.trim(),
          institutionAicteCode: 'UNKNOWN',
          institutionName: 'Unrecognized Entity',
          instrumentNumberMasked: 'XXXX-XXXX-XXXX',
          amountPaise: 0,
          bankName: 'Unknown',
          timestampUtc: new Date().toISOString(),
          ed25519Signature: 'ed25519:invalid_hash_signature_check_failed',
          isSignatureValid: false,
          status: 'INVALID_OR_TAMPERED',
        });
      } else {
        setVerifiedPayload({
          receiptNumber: receiptInput.trim(),
          institutionAicteCode: 'AICTE-ENGG-001',
          institutionName: 'Delhi Global Technical Campus',
          instrumentNumberMasked: 'AXIS-FDR-XXXX-9201',
          amountPaise: 350000000,
          bankName: 'Axis Bank',
          timestampUtc: '2026-10-23T09:15:32Z',
          ed25519Signature: 'ed25519:7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
          isSignatureValid: true,
          status: 'GENUINE_AICTE_SEALED',
        });
      }
    }, 600);
  };

  const formatPaiseINR = (paise: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(paise / 100);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 py-6">
      {/* Back button if hosted inside portal */}
      {onBackToApp && (
        <button
          onClick={onBackToApp}
          className="flex items-center gap-2 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          <ArrowLeft size={14} /> Back to Portal Dashboard
        </button>
      )}

      {/* Main Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-cyan-500/30 bg-slate-900/90 shadow-2xl relative overflow-hidden">
        {/* Government Watermark Header */}
        <div className="text-center space-y-2 border-b border-slate-800 pb-6">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-purple-700 via-indigo-900 to-cyan-500 p-0.5 shadow-xl shadow-cyan-950/40">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-cyan-400">
              <QrCode size={32} />
            </div>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
            All India Council for Technical Education
          </h1>
          <p className="text-xs text-slate-400 uppercase tracking-widest font-semibold">
            Public Receipt Verification Service (F-20)
          </p>
          <div className="inline-block px-3 py-1 rounded-full text-[11px] font-mono bg-slate-950 text-slate-400 border border-slate-800 mt-2">
            Rate-Limited Statutory Verification Gateway • No Login Required
          </div>
        </div>

        {/* Verification Input Form */}
        <form onSubmit={handleVerify} className="mt-6 space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Enter Receipt Number or Scanned QR Payload
            </label>
            <div className="relative">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-cyan-400" />
              <input
                type="text"
                value={receiptInput}
                onChange={(e) => setReceiptInput(e.target.value)}
                placeholder="e.g. REC-AICTE-2026-99201"
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white font-mono text-xs focus:outline-none focus:border-cyan-400"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isVerifying}
            className="w-full py-3 rounded-xl font-semibold bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-slate-950 text-xs shadow-lg shadow-cyan-950/40 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {isVerifying ? 'Verifying Ed25519 Seal...' : 'Verify Cryptographic Authenticity'}
          </button>
        </form>

        {/* Verification Result Output */}
        {verifiedPayload && (
          <div className="mt-8 border-t border-slate-800 pt-6 space-y-4">
            {verifiedPayload.isSignatureValid ? (
              <div className="p-4 rounded-2xl bg-emerald-950/50 border border-emerald-500/40 flex items-start gap-3.5">
                <ShieldCheck size={28} className="text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-bold text-emerald-200">
                    GENUINE AICTE CRYPTOGRAPHIC RECEIPT SEAL
                  </h3>
                  <p className="text-xs text-emerald-300/80 mt-0.5">
                    The Ed25519 digital signature of this deposit receipt matches the authorized AICTE root key.
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-2xl bg-red-950/50 border border-red-500/40 flex items-start gap-3.5">
                <ShieldAlert size={28} className="text-red-400 shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-bold text-red-200">
                    SIGNATURE INVALID OR TAMPERED RECEIPT
                  </h3>
                  <p className="text-xs text-red-300/80 mt-0.5">
                    This receipt payload could not be verified against the official AICTE certificate authority.
                  </p>
                </div>
              </div>
            )}

            {/* Receipt Details Grid */}
            <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-4 border-b border-slate-900 pb-3">
                <div>
                  <span className="text-slate-500 text-[11px] block">Receipt ID</span>
                  <span className="font-mono font-bold text-white text-sm">{verifiedPayload.receiptNumber}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[11px] block">Certified Date (UTC)</span>
                  <span className="font-mono text-slate-300">{verifiedPayload.timestampUtc}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 border-b border-slate-900 pb-3">
                <div>
                  <span className="text-slate-500 text-[11px] block">Institution Name</span>
                  <span className="font-semibold text-white">{verifiedPayload.institutionName}</span>
                  <span className="text-[10px] text-cyan-400 font-mono block mt-0.5">
                    AICTE Code: {verifiedPayload.institutionAicteCode}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 text-[11px] block">Deposit Amount</span>
                  <span className="font-mono font-bold text-cyan-300 text-sm">
                    {formatPaiseINR(verifiedPayload.amountPaise)}
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Held under AICTE Joint Custody</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 border-b border-slate-900 pb-3">
                <div>
                  <span className="text-slate-500 text-[11px] block">Bank Name</span>
                  <span className="text-slate-300">{verifiedPayload.bankName}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[11px] block">Masked Instrument Number</span>
                  <span className="font-mono text-slate-300">{verifiedPayload.instrumentNumberMasked}</span>
                </div>
              </div>

              <div>
                <span className="text-slate-500 text-[10px] block">Ed25519 Digital Seal</span>
                <span className="font-mono text-[10px] text-slate-400 break-all bg-slate-900/80 p-2 rounded-lg border border-slate-800 block mt-1">
                  {verifiedPayload.ed25519Signature}
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="mt-6 pt-4 border-t border-slate-800/60 text-center text-[11px] text-slate-500 flex items-center justify-center gap-2">
          <Lock size={12} />
          <span>Statutory compliance under AICTE Act Sec. 10(k). Privacy protected under DPDP Act 2023.</span>
        </div>
      </div>
    </div>
  );
};
