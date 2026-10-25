import React, { useState } from 'react';
import { ShieldCheck, Copy, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { api } from '../lib/apiClient';
import { useAuth } from './AuthContext';

type Step = 'start' | 'confirm' | 'recovery-codes';

export const MfaEnrolmentWizard: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const { refresh } = useAuth();
  const [step, setStep] = useState<Step>('start');
  const [secret, setSecret] = useState('');
  const [provisioningUri, setProvisioningUri] = useState('');
  const [code, setCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const start = async () => {
    setBusy(true);
    setError(null);
    const { data, error: startError } = await api.POST('/v1/auth/mfa/enrol/start');
    setBusy(false);
    if (!data) {
      setError('Could not start enrolment');
      return;
    }
    setSecret(data.secret);
    setProvisioningUri(data.provisioning_uri);
    setStep('confirm');
  };

  const confirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const { data, error: confirmError } = await api.POST('/v1/auth/mfa/enrol/confirm', {
      body: { secret, totp_code: code },
    });
    setBusy(false);
    if (!data) {
      setError('That code did not match — check the time on your authenticator app and try again.');
      return;
    }
    setRecoveryCodes(data.recovery_codes);
    setStep('recovery-codes');
  };

  const finish = async () => {
    await refresh();
    onClose();
  };

  React.useEffect(() => {
    if (step === 'start') start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 60,
        padding: 16,
      }}
    >
      <div style={{ width: '100%', maxWidth: 440, padding: 28, background: 'var(--surface)', borderRadius: '24px', border: '1px solid var(--border)', boxShadow: '0 24px 48px rgba(0,0,0,0.16)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
          <ShieldCheck size={20} color="var(--azure)" />
          <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text1)', margin: 0 }}>
            Set up two-step verification
          </h3>
        </div>

        {error && (
          <div
            style={{
              display: 'flex',
              gap: 8,
              padding: '10px 12px',
              borderRadius: 8,
              background: 'var(--danger-container)',
              border: '1px solid var(--danger)',
              color: 'var(--on-danger-container)',
              fontSize: 12,
              marginBottom: 14,
            }}
          >
            <AlertTriangle size={14} />
            {error}
          </div>
        )}

        {step === 'confirm' && (
          <form onSubmit={confirm} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Add this account to your authenticator app (Google Authenticator, 1Password, etc.),
              either by scanning or by entering the key manually.
            </p>
            <div
              style={{
                padding: '10px 12px',
                borderRadius: 8,
                background: 'var(--field)',
                border: '1px solid var(--hairline)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 8,
              }}
            >
              <code style={{ fontSize: 12, color: 'var(--text1)', wordBreak: 'break-all' }}>{secret}</code>
              <button
                type="button"
                onClick={() => navigator.clipboard?.writeText(secret)}
                title="Copy key"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)' }}
              >
                <Copy size={14} />
              </button>
            </div>
            <p style={{ fontSize: 10, color: 'var(--text-muted)', wordBreak: 'break-all' }}>
              {provisioningUri}
            </p>
            <label style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              Enter the 6-digit code it shows now
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                required
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                style={{
                  display: 'block',
                  width: '100%',
                  marginTop: 4,
                  padding: '10px 12px',
                  borderRadius: 8,
                  background: 'var(--field)',
                  border: '1px solid var(--hairline)',
                  color: 'var(--text1)',
                  fontSize: 13,
                }}
              />
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" onClick={onClose} className="btn-secondary" style={{ flex: 1 }}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={busy} style={{ flex: 1 }}>
                {busy ? 'Verifying…' : 'Confirm'}
              </button>
            </div>
          </form>
        )}

        {step === 'recovery-codes' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--ok)' }}>
              <CheckCircle2 size={16} />
              <span style={{ fontSize: 13, fontWeight: 600 }}>Two-step verification enabled</span>
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Save these recovery codes somewhere safe. Each one can be used once if you lose
              access to your authenticator app. They are shown only this once.
            </p>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 6,
                padding: 12,
                borderRadius: 8,
                background: 'var(--field)',
                border: '1px solid var(--hairline)',
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                color: 'var(--text1)',
              }}
            >
              {recoveryCodes.map((c) => (
                <span key={c}>{c}</span>
              ))}
            </div>
            <button type="button" onClick={finish} className="btn-primary">
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
