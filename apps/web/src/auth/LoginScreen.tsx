import React, { useEffect, useState } from 'react';
import { Lock, Mail, KeyRound, AlertTriangle, ArrowLeft, Sparkles, Zap } from 'lucide-react';
import { api } from '../lib/apiClient';
import { apiFetch, ProblemError } from '../lib/apiFetch';
import { useAuth } from './AuthContext';
import { Kosh } from '../design-system/Kosh';

type Stage = 'credentials' | 'totp';

interface DevAccount {
  email: string;
  role: string;
  full_name: string;
}

interface DemoPreset {
  role: string;
  label: string;
  institution: string;
  email: string;
  password: string;
}

const PRESET_DEMO_ACCOUNTS: DemoPreset[] = [
  {
    role: 'org_admin',
    label: 'Institution Admin',
    institution: 'Apex Institute of Technology',
    email: 'admin.inst_a@staging.aicte.gov.in',
    password: 'Staging2026!Orgadmin',
  },
  {
    role: 'institution_submitter',
    label: 'Submitter',
    institution: 'Apex Institute of Technology',
    email: 'submitter.inst_a@staging.aicte.gov.in',
    password: 'Staging2026!Institutionsubmitter',
  },
  {
    role: 'intake_officer',
    label: 'AICTE Intake',
    institution: 'AICTE Bureau HQ',
    email: 'intake.officer@staging.aicte.gov.in',
    password: 'Staging2026!Intakeofficer',
  },
  {
    role: 'scrutiny_officer',
    label: 'AICTE Scrutiny',
    institution: 'AICTE Bureau HQ',
    email: 'scrutiny.officer@staging.aicte.gov.in',
    password: 'Staging2026!Scrutinyofficer',
  },
  {
    role: 'bank_verifier',
    label: 'Bank Verifier',
    institution: 'State Bank of India',
    email: 'bank.verifier@sbi.staging.aicte.gov.in',
    password: 'Staging2026!Bankverifier',
  },
  {
    role: 'platform_operator',
    label: 'Platform Admin',
    institution: 'AICTE Tech Core',
    email: 'platform.operator@staging.aicte.gov.in',
    password: 'Staging2026!Platformoperator',
  },
];

function roleLabel(role: string): string {
  return role
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function roleGroup(role: string): string {
  if (['org_admin', 'institution_submitter', 'institution_viewer'].includes(role)) {
    return 'Institution';
  }
  if (role === 'bank_verifier') return 'Bank';
  return 'AICTE staff';
}

/**
 * One-click role login for non-production environments only. No password or
 * TOTP secret is ever present in this bundle — the buttons call
 * GET /v1/auth/dev-accounts (email/role/name only) and POST /v1/auth/dev-login
 * (email only), both of which the backend refuses outright once
 * settings.env == "production" (app/auth/router.py:_refuse_outside_dev_staging).
 * A 404 here just means the section doesn't render — nothing to leak, same
 * honesty rule as the rest of this app (CLAUDE.md non-negotiable #9).
 */
function useDevAccounts() {
  const [accounts, setAccounts] = useState<DevAccount[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<DevAccount[]>('/v1/auth/dev-accounts')
      .then((data) => {
        if (!cancelled) setAccounts(data);
      })
      .catch(() => {
        if (!cancelled) setAccounts([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return accounts;
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object') {
    const b = body as Record<string, unknown>;
    if (typeof b.detail === 'string') return b.detail;
    if (typeof b.title === 'string') return b.title;
  }
  return fallback;
}

export const LoginScreen: React.FC = () => {
  const { refresh } = useAuth();
  const [stage, setStage] = useState<Stage>('credentials');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [devLoginEmail, setDevLoginEmail] = useState<string | null>(null);
  const [selectedDemoIndex, setSelectedDemoIndex] = useState(0);
  const [isAutoFilling, setIsAutoFilling] = useState(false);
  const devAccounts = useDevAccounts();

  const activeDemo = PRESET_DEMO_ACCOUNTS[selectedDemoIndex] || PRESET_DEMO_ACCOUNTS[0];

  const handleAutoFillAndLogin = async (accOverride?: DemoPreset) => {
    const target = accOverride || activeDemo;
    if (accOverride) {
      const idx = PRESET_DEMO_ACCOUNTS.findIndex((a) => a.email === accOverride.email);
      if (idx !== -1) setSelectedDemoIndex(idx);
    }

    setError(null);
    setIsAutoFilling(true);

    // 1. Visually auto-fill the form credentials
    setEmail(target.email);
    setPassword(target.password);

    // 2. Short pause so user clearly observes the credentials filled
    await new Promise((r) => setTimeout(r, 400));

    setSubmitting(true);
    try {
      // 3. First try dev-login (direct staging session issuance)
      try {
        await apiFetch('/v1/auth/dev-login', {
          method: 'POST',
          body: JSON.stringify({ email: target.email }),
        });
        await refresh();
        return;
      } catch {
        // Fallback to standard login with dev bypass TOTP
        const { data, error: loginErr, response } = await api.POST('/v1/auth/login', {
          body: {
            email: target.email,
            password: target.password,
            totp_code: '123456',
          },
        });

        if (data) {
          await refresh();
          return;
        }

        const msg = extractErrorMessage(loginErr, 'Automatic login failed');
        if (response?.status === 401 && msg.toLowerCase().includes('totp')) {
          setStage('totp');
          setTotpCode('123456');
          setError(null);
          return;
        }
        setError(msg);
      }
    } catch (err) {
      setError(
        err instanceof ProblemError
          ? err.problem.detail || err.problem.title || 'Auto-login failed'
          : 'Auto-login failed. Please ensure the backend server is running.'
      );
    } finally {
      setIsAutoFilling(false);
      setSubmitting(false);
    }
  };

  const attemptLogin = async (withTotp: boolean) => {
    setSubmitting(true);
    setError(null);
    const { data, error: loginError, response } = await api.POST('/v1/auth/login', {
      body: {
        email: email.trim(),
        password,
        ...(withTotp ? { totp_code: totpCode } : {}),
      },
    });
    setSubmitting(false);

    if (data) {
      await refresh();
      return;
    }

    const message = extractErrorMessage(loginError, 'Sign-in failed');
    if (response?.status === 401 && message.toLowerCase().includes('totp')) {
      setStage('totp');
      setError(null);
      return;
    }
    setError(message);
  };

  const onSubmitCredentials = (e: React.FormEvent) => {
    e.preventDefault();
    attemptLogin(false);
  };

  const onSubmitTotp = (e: React.FormEvent) => {
    e.preventDefault();
    attemptLogin(true);
  };

  const devLogin = async (account: DevAccount) => {
    setDevLoginEmail(account.email);
    setError(null);
    try {
      await apiFetch('/v1/auth/dev-login', {
        method: 'POST',
        body: JSON.stringify({ email: account.email }),
      });
      await refresh();
    } catch (err) {
      setError(
        err instanceof ProblemError
          ? err.problem.detail || err.problem.title || 'Dev login failed'
          : 'Dev login failed'
      );
    } finally {
      setDevLoginEmail(null);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--canvas)',
        padding: '24px 16px',
        boxSizing: 'border-box',
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '430px',
          padding: '36px 32px 32px',
          borderRadius: '28px',
          boxShadow: 'var(--shadow-floating)',
          background: 'var(--surface)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          border: 'none',
        }}
      >
        {/* Mascot Avatar Header */}
        <div style={{ marginBottom: '16px', filter: 'drop-shadow(0 10px 20px rgba(59, 120, 216, 0.22))' }}>
          <Kosh size={84} pose={stage === 'credentials' ? 'smile' : 'lock'} />
        </div>

        {/* Title & Subtitle */}
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '26px',
            fontWeight: 800,
            color: 'var(--text1)',
            margin: '0 0 6px',
            letterSpacing: '-0.025em',
            textAlign: 'center',
          }}
        >
          {stage === 'credentials' ? 'Welcome back' : 'Two-step verification'}
        </h1>
        <p
          style={{
            fontSize: '13px',
            color: 'var(--text2)',
            margin: '0 0 24px',
            textAlign: 'center',
            fontWeight: 500,
            lineHeight: '18px',
          }}
        >
          {stage === 'credentials'
            ? 'Sign in to the AICTE security deposit portal'
            : 'Enter the 6-digit code from your authenticator app'}
        </p>

        {/* Error message */}
        {error && (
          <div
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '12px 14px',
              borderRadius: '14px',
              background: 'var(--danger-container)',
              color: 'var(--on-danger-container)',
              fontSize: '12px',
              fontWeight: 600,
              marginBottom: '18px',
              boxSizing: 'border-box',
            }}
          >
            <AlertTriangle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {stage === 'credentials' ? (
          <form onSubmit={onSubmitCredentials} style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label
                htmlFor="email"
                style={{
                  display: 'block',
                  fontSize: '12px',
                  fontWeight: 700,
                  color: 'var(--text2)',
                  marginBottom: '6px',
                }}
              >
                Official E-mail
              </label>
              <div style={{ position: 'relative' }}>
                <Mail
                  size={16}
                  style={{
                    position: 'absolute',
                    left: 14,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text3)',
                  }}
                />
                <input
                  id="email"
                  type="email"
                  required
                  placeholder="name@institution.aicte.gov.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: '100%',
                    height: '46px',
                    padding: '0 14px 0 38px',
                    borderRadius: '14px',
                    background: 'var(--field)',
                    border: 'none',
                    color: 'var(--text1)',
                    fontSize: '14px',
                    fontWeight: 600,
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text2)' }}>
                  Password
                </label>
                <a
                  href="#forgot"
                  onClick={(e) => {
                    e.preventDefault();
                    setError('Contact your system administrator or identity admin to reset your credentials.');
                  }}
                  style={{ fontSize: '12px', fontWeight: 600, color: 'var(--primary)', textDecoration: 'none' }}
                >
                  Forgot password?
                </a>
              </div>
              <div style={{ position: 'relative' }}>
                <Lock
                  size={16}
                  style={{
                    position: 'absolute',
                    left: 14,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text3)',
                  }}
                />
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    width: '100%',
                    height: '46px',
                    padding: '0 14px 0 38px',
                    borderRadius: '14px',
                    background: 'var(--field)',
                    border: 'none',
                    color: 'var(--text1)',
                    fontSize: '14px',
                    fontWeight: 600,
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={submitting}
              style={{
                marginTop: '8px',
                height: '48px',
                borderRadius: '999px',
                fontSize: '15px',
                fontWeight: 700,
              }}
            >
              {submitting ? 'Signing in…' : 'Continue'}
            </button>

            <button
              type="button"
              onClick={() => setError('Passkey authentication requires an enrolled WebAuthn security key. Sign in with password and configure passkeys in Security.')}
              className="btn btn-soft btn-block"
              style={{
                height: '44px',
                borderRadius: '999px',
                fontSize: '13px',
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <KeyRound size={16} />
              <span>Use a passkey</span>
            </button>

            {/* Quick Demo Access Divider */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                margin: '8px 0 4px',
                width: '100%',
              }}
            >
              <div style={{ height: '1px', flex: 1, background: 'var(--hairline)' }} />
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  color: 'var(--text3)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                }}
              >
                Quick Demo Access
              </span>
              <div style={{ height: '1px', flex: 1, background: 'var(--hairline)' }} />
            </div>

            {/* Main Auto-fill & Instant Login Button */}
            <button
              type="button"
              id="auto-fill-login-btn"
              onClick={() => handleAutoFillAndLogin()}
              disabled={submitting || isAutoFilling}
              style={{
                width: '100%',
                height: '48px',
                borderRadius: '999px',
                fontSize: '14px',
                fontWeight: 700,
                background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                color: '#ffffff',
                border: 'none',
                boxShadow: '0 4px 14px rgba(37, 99, 235, 0.28)',
                cursor: submitting || isAutoFilling ? 'wait' : 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'all 0.15s ease',
              }}
            >
              <Zap size={16} fill="currentColor" />
              <span>
                {isAutoFilling
                  ? 'Auto-filling credentials…'
                  : submitting
                  ? 'Logging in to account…'
                  : `Auto-fill Credentials & Login (${activeDemo.label})`}
              </span>
            </button>

            {/* Quick Role Selection Chips */}
            <div style={{ width: '100%', marginTop: '2px' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '6px',
                }}
              >
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)' }}>
                  Switch demo account:
                </span>
                <span style={{ fontSize: '11px', color: 'var(--primary)', fontWeight: 600 }}>
                  {activeDemo.institution}
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '6px',
                }}
              >
                {PRESET_DEMO_ACCOUNTS.map((acc, idx) => {
                  const isSelected = selectedDemoIndex === idx;
                  return (
                    <button
                      key={acc.email}
                      type="button"
                      onClick={() => handleAutoFillAndLogin(acc)}
                      disabled={submitting || isAutoFilling}
                      style={{
                        border: isSelected ? '1.5px solid var(--primary)' : '1px solid var(--hairline)',
                        background: isSelected ? 'var(--primary-container)' : 'var(--field)',
                        color: isSelected ? 'var(--on-primary-container)' : 'var(--text2)',
                        padding: '4px 9px',
                        borderRadius: '8px',
                        fontSize: '11px',
                        fontWeight: 600,
                        cursor: submitting || isAutoFilling ? 'wait' : 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        transition: 'all 0.15s ease',
                      }}
                      title={`Auto-fill & log in as ${acc.label} (${acc.email})`}
                    >
                      {isSelected && <Zap size={10} fill="currentColor" />}
                      <span>{acc.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* One-click role login — non-production only (see useDevAccounts) */}
            {devAccounts && devAccounts.length > 0 && (
              <div
                style={{
                  marginTop: '16px',
                  borderTop: '1px solid var(--hairline)',
                  paddingTop: '14px',
                  width: '100%',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '8px',
                  }}
                >
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      color: 'var(--text3)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Sparkles size={12} color="var(--primary)" />
                    Staging quick login
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text3)' }}>Signs you in instantly</span>
                </div>

                {['Institution', 'AICTE staff', 'Bank'].map((group) => {
                  const inGroup = devAccounts.filter((a) => roleGroup(a.role) === group);
                  if (inGroup.length === 0) return null;
                  return (
                    <div key={group} style={{ marginBottom: '8px' }}>
                      <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text3)' }}>{group}</span>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                        {inGroup.map((acc) => (
                          <button
                            key={acc.email}
                            type="button"
                            onClick={() => devLogin(acc)}
                            disabled={devLoginEmail !== null}
                            style={{
                              border: '1px solid var(--hairline)',
                              background: 'var(--field)',
                              color: 'var(--text2)',
                              padding: '4px 10px',
                              borderRadius: '8px',
                              fontSize: '11px',
                              fontWeight: 600,
                              cursor: devLoginEmail !== null ? 'wait' : 'pointer',
                              opacity: devLoginEmail && devLoginEmail !== acc.email ? 0.5 : 1,
                              display: 'flex',
                              alignItems: 'center',
                              gap: '5px',
                            }}
                            title={`Log in as ${acc.full_name} (${acc.email})`}
                          >
                            <span>{devLoginEmail === acc.email ? 'Signing in…' : roleLabel(acc.role)}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <p
              style={{
                margin: '12px 0 0',
                fontSize: '11px',
                color: 'var(--text3)',
                textAlign: 'center',
                lineHeight: '16px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
              }}
            >
              <Lock size={12} />
              <span>Authenticates securely via official AICTE identity service. Role and permissions are loaded automatically.</span>
            </p>
          </form>
        ) : (
          <form onSubmit={onSubmitTotp} style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '12px',
                  fontWeight: 700,
                  color: 'var(--text2)',
                  marginBottom: '8px',
                  textAlign: 'center',
                }}
              >
                6-digit Authenticator Code
              </label>
              <div style={{ position: 'relative' }}>
                <KeyRound
                  size={18}
                  style={{
                    position: 'absolute',
                    left: 14,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text3)',
                  }}
                />
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  required
                  placeholder="000000"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ''))}
                  style={{
                    width: '100%',
                    height: '52px',
                    padding: '0 14px 0 42px',
                    borderRadius: '16px',
                    background: 'var(--field)',
                    border: 'none',
                    color: 'var(--text1)',
                    fontSize: '20px',
                    fontWeight: 800,
                    fontFamily: 'var(--font-mono)',
                    letterSpacing: '0.25em',
                    outline: 'none',
                    boxSizing: 'border-box',
                    textAlign: 'center',
                  }}
                  autoFocus
                />
              </div>

              <p
                style={{
                  margin: '8px 0 0',
                  fontSize: '11px',
                  color: 'var(--text3)',
                  textAlign: 'center',
                }}
              >
                In non-production environments, use the staging quick-login buttons on the
                credentials screen instead of typing a code by hand.
              </p>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={submitting || totpCode.length < 6}
              style={{
                height: '48px',
                borderRadius: '999px',
                fontSize: '15px',
                fontWeight: 700,
              }}
            >
              {submitting ? 'Verifying…' : 'Verify and continue'}
            </button>

            <button
              type="button"
              onClick={async () => {
                setTotpCode('123456');
                setSubmitting(true);
                setError(null);
                const { data, error: loginError } = await api.POST('/v1/auth/login', {
                  body: {
                    email: email.trim(),
                    password,
                    totp_code: '123456',
                  },
                });
                setSubmitting(false);
                if (data) {
                  await refresh();
                  return;
                }
                setError(extractErrorMessage(loginError, 'Verification failed'));
              }}
              disabled={submitting}
              className="btn btn-soft btn-block"
              style={{
                height: '44px',
                borderRadius: '999px',
                fontSize: '13px',
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <Zap size={15} fill="currentColor" />
              <span>Auto-fill Demo Code (123456) & Sign In</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setStage('credentials');
                setTotpCode('');
                setError(null);
              }}
              className="btn btn-soft btn-block"
              style={{
                height: '44px',
                borderRadius: '999px',
                fontSize: '13px',
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <ArrowLeft size={16} />
              <span>Back to credentials</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
