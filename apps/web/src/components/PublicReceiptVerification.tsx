import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, QrCode, Search, CheckCircle2, Lock, ArrowLeft, ExternalLink } from 'lucide-react';
import { PublicReceiptPayload } from '../types';
import { formatPaiseINR } from '@aicte-fdr/shared';

interface PublicReceiptVerificationProps {
  onBackToApp?: () => void;
}

export const PublicReceiptVerification: React.FC<PublicReceiptVerificationProps> = ({ onBackToApp }) => {
  const [receiptInput, setReceiptInput] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifiedPayload, setVerifiedPayload] = useState<PublicReceiptPayload | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    if (!receiptInput.trim()) return;

    // The real endpoint (GET /v1/public/receipts/verify) is unauthenticated and already
    // exists on the backend, but needs the full QR-encoded query (receipt id, instrument id,
    // institution code, version, hash, timestamp, Ed25519 signature) and a proxy/CORS path
    // this dev server does not have yet (stream R3). This screen never fabricates a
    // verification result — it says so honestly instead.
    setIsVerifying(true);
    setVerifiedPayload(null);
    setTimeout(() => {
      setIsVerifying(false);
      setNotice(
        'Not yet connected to the API. The real verification endpoint exists and needs no login, but this screen is not wired to it yet — no result is fabricated.'
      );
    }, 300);
  };

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px', padding: '24px 0' }}>
      {/* Back button if hosted inside portal */}
      {onBackToApp && (
        <button
          onClick={onBackToApp}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600, color: 'var(--azure)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
        >
          <ArrowLeft size={16} /> Back to Portal Dashboard
        </button>
      )}

      {/* Main Card */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '24px', padding: '32px', boxShadow: 'var(--shadow-card)' }}>
        {/* Government Watermark Header */}
        <div style={{ textAlign: 'center', borderBottom: '1px solid var(--border)', paddingBottom: '24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: 56, height: 56, borderRadius: '16px', background: 'var(--primary-container)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <QrCode size={28} color="var(--azure)" />
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: 800, color: 'var(--text1)' }}>
            All India Council for Technical Education
          </h1>
          <p style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700 }}>
            Public Receipt Verification Service (F-20)
          </p>
          <div style={{ display: 'inline-block', padding: '4px 12px', borderRadius: '9999px', fontSize: '11px', fontFamily: 'var(--font-mono)', background: 'var(--field)', color: 'var(--text2)', border: '1px solid var(--border)', marginTop: '4px' }}>
            Rate-Limited Statutory Verification Gateway • No Login Required
          </div>
        </div>

        {/* Verification Input Form */}
        <form onSubmit={handleVerify} style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text2)', display: 'block', marginBottom: '6px' }}>
              Enter Receipt Number or Scanned QR Payload
            </label>
            <div style={{ position: 'relative' }}>
              <Search size={16} color="var(--text3)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={receiptInput}
                onChange={(e) => setReceiptInput(e.target.value)}
                placeholder="Paste the scanned QR payload"
                style={{ width: '100%', paddingLeft: '40px', paddingRight: '14px', paddingTop: '12px', paddingBottom: '12px', borderRadius: '14px', background: 'var(--field)', border: '1px solid var(--border)', color: 'var(--text1)', fontFamily: 'var(--font-mono)', fontSize: '12px', outline: 'none' }}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isVerifying}
            style={{
              width: '100%',
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
              opacity: isVerifying ? 0.6 : 1,
            }}
          >
            {isVerifying ? 'Verifying Ed25519 Seal...' : 'Verify Cryptographic Authenticity'}
          </button>
        </form>

        {notice && (
          <div style={{ marginTop: '20px', padding: '16px', borderRadius: '16px', background: 'var(--field)', border: '1px solid var(--border)', fontSize: '12px', color: 'var(--text2)', display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
            <Lock size={16} color="var(--azure)" style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{notice}</span>
          </div>
        )}

        {/* Verification Result Output */}
        {verifiedPayload && (
          <div style={{ marginTop: '28px', borderTop: '1px solid var(--border)', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {verifiedPayload.isSignatureValid ? (
              <div style={{ padding: '16px', borderRadius: '16px', background: '#ECFDF5', border: '1px solid #A7F3D0', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <ShieldCheck size={26} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 800, color: '#065F46' }}>
                    GENUINE AICTE CRYPTOGRAPHIC RECEIPT SEAL
                  </h3>
                  <p style={{ fontSize: '12px', color: '#047857', marginTop: '2px' }}>
                    The Ed25519 digital signature of this deposit receipt matches the authorized AICTE root key.
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ padding: '16px', borderRadius: '16px', background: '#FEF2F2', border: '1px solid #FECACA', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <ShieldAlert size={26} color="#DC2626" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 800, color: '#991B1B' }}>
                    SIGNATURE INVALID OR TAMPERED RECEIPT
                  </h3>
                  <p style={{ fontSize: '12px', color: '#B91C1C', marginTop: '2px' }}>
                    This receipt payload could not be verified against the official AICTE certificate authority.
                  </p>
                </div>
              </div>
            )}

            {/* Receipt Details Grid */}
            <div style={{ padding: '20px', borderRadius: '16px', background: 'var(--field)', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '10px' }}>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Receipt ID</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text1)', fontSize: '13px' }}>{verifiedPayload.receiptNumber}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Certified Date (UTC)</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text2)' }}>{verifiedPayload.timestampUtc}</span>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '10px' }}>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Institution Name</span>
                  <span style={{ fontWeight: 700, color: 'var(--text1)' }}>{verifiedPayload.institutionName}</span>
                  <span style={{ fontSize: '10px', color: 'var(--azure)', fontFamily: 'var(--font-mono)', display: 'block', marginTop: '2px' }}>
                    AICTE Code: {verifiedPayload.institutionAicteCode}
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Deposit Amount</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--text1)', fontSize: '14px' }}>
                    {formatPaiseINR(verifiedPayload.amountPaise)}
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--text3)', display: 'block', marginTop: '2px' }}>Held under AICTE Joint Custody</span>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '10px' }}>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Bank Name</span>
                  <span style={{ color: 'var(--text2)' }}>{verifiedPayload.bankName}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Masked Instrument Number</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text2)' }}>{verifiedPayload.instrumentNumberMasked}</span>
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--text3)', fontSize: '10px', display: 'block' }}>Ed25519 Digital Seal</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text3)', wordBreak: 'break-all', background: 'var(--surface)', padding: '8px', borderRadius: '8px', border: '1px solid var(--border)', display: 'block', marginTop: '4px' }}>
                  {verifiedPayload.ed25519Signature}
                </span>
              </div>
            </div>
          </div>
        )}

        <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--border)', textAlign: 'center', fontSize: '11px', color: 'var(--text3)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
          <Lock size={12} />
          <span>Statutory compliance under AICTE Act Sec. 10(k). Privacy protected under DPDP Act 2023.</span>
        </div>
      </div>
    </div>
  );
};
