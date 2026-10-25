import React, { createContext, useCallback, useContext, useRef, useState } from 'react';
import { ShieldAlert, AlertTriangle } from 'lucide-react';
import { api } from '../lib/apiClient';

type Resolver = (ok: boolean) => void;

interface StepUpContextValue {
  /** Opens the step-up sheet and resolves true once a real TOTP code is verified,
   * false if the user cancels. Every sensitive action (release decisions, role
   * grants, connector config — AUTH_ROLES_MATRIX.md §2.2(3)) awaits this before
   * calling its real endpoint; the server enforces it independently regardless. */
  requestStepUp: () => Promise<boolean>;
}

const StepUpContext = createContext<StepUpContextValue | null>(null);

export const StepUpProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const resolverRef = useRef<Resolver | null>(null);

  const requestStepUp = useCallback(() => {
    setOpen(true);
    setCode('');
    setError(null);
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
    });
  }, []);

  const close = (ok: boolean) => {
    setOpen(false);
    resolverRef.current?.(ok);
    resolverRef.current = null;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const { data } = await api.POST('/v1/auth/step-up', { body: { otp_code: code } });
    setBusy(false);
    if (!data) {
      setError('Invalid code — re-enter the current code from your authenticator app.');
      return;
    }
    close(true);
  };

  return (
    <StepUpContext.Provider value={{ requestStepUp }}>
      {children}
      {open && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 70,
            padding: 16,
          }}
        >
          <div style={{ width: '100%', maxWidth: 360, padding: 28, background: 'var(--surface)', borderRadius: '24px', border: '1px solid var(--border)', boxShadow: '0 20px 40px rgba(0,0,0,0.15)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <ShieldAlert size={20} color="var(--warn)" />
              <h3 style={{ fontSize: 16, fontWeight: 800, color: 'var(--text1)', margin: 0, fontFamily: 'var(--font-display)' }}>
                Confirm it's you
              </h3>
            </div>
            <p style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 14 }}>
              This action needs a fresh verification code.
            </p>
            {error && (
              <div
                style={{
                  display: 'flex',
                  gap: 8,
                  padding: '10px 12px',
                  borderRadius: 10,
                  background: '#FEF2F2',
                  border: '1px solid #FECACA',
                  color: '#991B1B',
                  fontSize: 12,
                  marginBottom: 12,
                }}
              >
                <AlertTriangle size={15} />
                {error}
              </div>
            )}
            <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                autoFocus
                required
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                style={{
                  padding: '12px',
                  borderRadius: 12,
                  background: 'var(--field)',
                  border: '1px solid var(--border)',
                  color: 'var(--text1)',
                  fontSize: 16,
                  letterSpacing: 4,
                  textAlign: 'center',
                  outline: 'none',
                }}
              />
              <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                <button
                  type="button"
                  onClick={() => close(false)}
                  style={{
                    flex: 1,
                    padding: '10px',
                    borderRadius: '9999px',
                    border: '1px solid var(--border)',
                    background: 'var(--field)',
                    color: 'var(--text2)',
                    fontSize: 13,
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={busy}
                  style={{
                    flex: 1,
                    padding: '10px',
                    borderRadius: '9999px',
                    border: 'none',
                    background: 'var(--ink)',
                    color: '#FFFFFF',
                    fontSize: 13,
                    fontWeight: 700,
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(17, 24, 39, 0.2)',
                  }}
                >
                  {busy ? 'Verifying…' : 'Verify'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </StepUpContext.Provider>
  );
};

export function useStepUp(): StepUpContextValue {
  const ctx = useContext(StepUpContext);
  if (!ctx) throw new Error('useStepUp must be used inside StepUpProvider');
  return ctx;
}
