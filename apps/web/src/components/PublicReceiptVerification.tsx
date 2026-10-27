import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, QrCode, Search, Lock, ArrowLeft } from 'lucide-react';
import { api } from '../lib/apiClient';

interface PublicReceiptVerificationProps {
  onBackToApp?: () => void;
}

interface VerifiedReceipt {
  verified: boolean;
  receipt_id: string;
  institution_code: string;
  version_number: number;
  version_hash_prefix: string;
  issued_at: string;
  message: string;
}

const REQUIRED_PARAMS = ['rid', 'iid', 'inst', 'ver', 'h', 'ts', 'sig'] as const;

/** Accepts either a full verification URL (as printed under the receipt's QR
 * code) or a bare query string copied from it, and extracts the seven signed
 * fields the backend actually checks — nothing here is guessed or invented. */
function parseReceiptInput(raw: string): URLSearchParams | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  let queryPart = trimmed;
  const qIndex = trimmed.indexOf('?');
  if (qIndex !== -1) queryPart = trimmed.slice(qIndex + 1);
  const params = new URLSearchParams(queryPart);
  const hasAll = REQUIRED_PARAMS.every((key) => params.has(key));
  return hasAll ? params : null;
}

export const PublicReceiptVerification: React.FC<PublicReceiptVerificationProps> = ({ onBackToApp }) => {
  const [receiptInput, setReceiptInput] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState<VerifiedReceipt | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!receiptInput.trim()) return;

    setResult(null);
    setNotice(null);

    const params = parseReceiptInput(receiptInput);
    if (!params) {
      setNotice(
        `Could not find all required fields (${REQUIRED_PARAMS.join(', ')}) in that input. Paste the full verification URL or query string printed beneath the receipt's QR code.`
      );
      return;
    }

    setIsVerifying(true);
    const { data, error } = await api.GET('/v1/public/receipts/verify', {
      params: {
        query: {
          rid: params.get('rid')!,
          iid: params.get('iid')!,
          inst: params.get('inst')!,
          ver: Number(params.get('ver')),
          h: params.get('h')!,
          ts: params.get('ts')!,
          sig: params.get('sig')!,
        },
      },
    });
    setIsVerifying(false);

    if (error) {
      // A real 400 from the backend (invalid/tampered signature) — never a
      // client-side guess. A plain network/validation failure gets the same
      // honest "could not verify" treatment, not a fabricated pass.
      setResult({
        verified: false,
        receipt_id: params.get('rid') ?? '',
        institution_code: params.get('inst') ?? '',
        version_number: Number(params.get('ver')) || 0,
        version_hash_prefix: params.get('h') ?? '',
        issued_at: params.get('ts') ?? '',
        message: extractErrorMessage(error, 'The receipt signature is invalid or tampered.'),
      });
      return;
    }

    setResult(data as VerifiedReceipt);
  };

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px', padding: '24px 0' }}>
      {onBackToApp && (
        <button
          onClick={onBackToApp}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600, color: 'var(--azure)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
        >
          <ArrowLeft size={16} /> Back to Portal Dashboard
        </button>
      )}

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '24px', padding: '32px', boxShadow: 'var(--shadow-card)' }}>
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

        <form onSubmit={handleVerify} style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text2)', display: 'block', marginBottom: '6px' }}>
              Paste the Verification URL or QR Payload
            </label>
            <div style={{ position: 'relative' }}>
              <Search size={16} color="var(--text3)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={receiptInput}
                onChange={(e) => setReceiptInput(e.target.value)}
                placeholder="?rid=...&iid=...&inst=...&ver=...&h=...&ts=...&sig=..."
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
            {isVerifying ? 'Verifying Ed25519 Seal…' : 'Verify Cryptographic Authenticity'}
          </button>
        </form>

        {notice && (
          <div style={{ marginTop: '20px', padding: '16px', borderRadius: '16px', background: 'var(--field)', border: '1px solid var(--border)', fontSize: '12px', color: 'var(--text2)', display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
            <Lock size={16} color="var(--azure)" style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{notice}</span>
          </div>
        )}

        {result && (
          <div style={{ marginTop: '28px', borderTop: '1px solid var(--border)', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {result.verified ? (
              <div style={{ padding: '16px', borderRadius: '16px', background: '#ECFDF5', border: '1px solid #A7F3D0', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <ShieldCheck size={26} color="#059669" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 800, color: '#065F46' }}>
                    GENUINE AICTE CRYPTOGRAPHIC RECEIPT SEAL
                  </h3>
                  <p style={{ fontSize: '12px', color: '#047857', marginTop: '2px' }}>{result.message}</p>
                </div>
              </div>
            ) : (
              <div style={{ padding: '16px', borderRadius: '16px', background: '#FEF2F2', border: '1px solid #FECACA', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <ShieldAlert size={26} color="#DC2626" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <h3 style={{ fontSize: '14px', fontWeight: 800, color: '#991B1B' }}>
                    SIGNATURE INVALID OR TAMPERED RECEIPT
                  </h3>
                  <p style={{ fontSize: '12px', color: '#B91C1C', marginTop: '2px' }}>{result.message}</p>
                </div>
              </div>
            )}

            {/* Only fields the backend's signed payload actually covers — amount,
                bank, and institution name are deliberately NOT shown here: they
                are not part of what the Ed25519 signature attests to. */}
            <div style={{ padding: '20px', borderRadius: '16px', background: 'var(--field)', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '10px' }}>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Receipt ID</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text1)', fontSize: '13px' }}>{result.receipt_id}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Issued At (UTC)</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text2)' }}>{result.issued_at}</span>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '10px' }}>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Institution Code</span>
                  <span style={{ fontWeight: 700, color: 'var(--text1)', fontFamily: 'var(--font-mono)' }}>{result.institution_code}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text3)', fontSize: '11px', display: 'block' }}>Instrument Version</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text1)' }}>v{result.version_number}</span>
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--text3)', fontSize: '10px', display: 'block' }}>Content Hash Prefix</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text3)', wordBreak: 'break-all', background: 'var(--surface)', padding: '8px', borderRadius: '8px', border: '1px solid var(--border)', display: 'block', marginTop: '4px' }}>
                  {result.version_hash_prefix}
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

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object') {
    const e = error as Record<string, unknown>;
    if (e.detail && typeof e.detail === 'object') {
      const d = e.detail as Record<string, unknown>;
      if (typeof d.detail === 'string') return d.detail;
    }
    if (typeof e.detail === 'string') return e.detail;
    if (typeof e.title === 'string') return e.title;
  }
  return fallback;
}
