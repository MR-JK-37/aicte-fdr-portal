import React, { useEffect, useState } from 'react';
import { ShieldCheck, Smartphone, LogOut, CheckCircle2, Circle, KeyRound, Globe, ChevronRight, Lock, Eye, Edit2 } from 'lucide-react';
import { api } from '../lib/apiClient';
import { useAuth } from '../auth/AuthContext';
import { MfaEnrolmentWizard } from '../auth/MfaEnrolmentWizard';
import type { paths } from '@aicte-fdr/api-client';

type ProfileCompletion =
  paths['/v1/me/profile-completion']['get']['responses'][200]['content']['application/json'];
type SessionInfo = paths['/v1/auth/sessions']['get']['responses'][200]['content']['application/json'][number];

/**
 * Profile & Security View — Matching Screen 4 ("Profile") in ui-refrence.png.
 *  - Header card with Region chip, Avatar circle, Name, Role, and "Show my name to institutions" toggle
 *  - Grouped settings list: Two-step verification, Passkeys, Devices & sessions, Language, Privacy policy
 *  - Real profile completion meter
 *  - Real session revocation & step-up integration
 */
export const SecurityView: React.FC = () => {
  const { user, refresh } = useAuth();
  const [completion, setCompletion] = useState<ProfileCompletion | null>(null);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [showMfaWizard, setShowMfaWizard] = useState(false);
  const [showNamePublicly, setShowNamePublicly] = useState(true);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const [{ data: comp }, { data: sess }] = await Promise.all([
      api.GET('/v1/me/profile-completion'),
      api.GET('/v1/auth/sessions'),
    ]);
    setCompletion(comp ?? null);
    setSessions(sess ?? []);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const revokeSession = async (sessionId: string) => {
    await api.DELETE('/v1/auth/sessions/{session_id}', {
      params: { path: { session_id: sessionId } },
    });
    load();
  };

  const signOutEverywhere = async () => {
    await api.POST('/v1/auth/logout-all');
    await refresh();
  };

  if (loading) {
    return <div style={{ padding: 24, color: 'var(--text3)', fontSize: 13, fontWeight: 600 }}>Loading profile…</div>;
  }

  const initials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : 'AK';

  const region = (user as any)?.region || 'South';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
      {/* 1. Profile Hero Card (Screen 4 in ui-refrence.png) */}
      <div
        className="card"
        style={{
          padding: '28px 24px',
          background: 'var(--surface)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Region Chip */}
        <div style={{ alignSelf: 'flex-start', marginBottom: '8px' }}>
          <span className="chip" style={{ fontSize: '12px', fontWeight: 700, padding: '4px 12px', background: 'var(--field)' }}>
            Region: {region}
          </span>
        </div>

        {/* Large Avatar Circle */}
        <div
          style={{
            width: '88px',
            height: '88px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #c9d7f7, #e6edff)',
            color: 'var(--primary)',
            display: 'grid',
            placeItems: 'center',
            fontSize: '28px',
            fontWeight: 800,
            fontFamily: 'var(--font-display)',
            boxShadow: '0 8px 24px rgba(35, 40, 110, 0.12)',
            marginBottom: '12px',
          }}
        >
          {initials}
        </div>

        <h2 style={{ margin: '0 0 4px', fontSize: '20px', fontWeight: 800, color: 'var(--text1)', fontFamily: 'var(--font-display)' }}>
          {user?.full_name || 'Anil Kumar'}
        </h2>
        <p style={{ margin: '0 0 4px', fontSize: '13px', color: 'var(--text2)', fontWeight: 600 }}>
          {user?.email || 'officer@example.com'}
        </p>
        <p style={{ margin: '0 0 16px', fontSize: '12px', color: 'var(--text3)', fontWeight: 600 }}>
          {user?.role ? user.role.replace(/_/g, ' ') : 'Scrutiny Officer'}
        </p>

        {/* Show my name to institutions toggle */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '100%',
            maxWidth: '360px',
            padding: '12px 16px',
            borderRadius: '16px',
            background: 'var(--field)',
          }}
        >
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text1)' }}>
            Show my name to institutions
          </span>
          <input
            type="checkbox"
            checked={showNamePublicly}
            onChange={(e) => setShowNamePublicly(e.target.checked)}
            style={{ width: 18, height: 18, accentColor: 'var(--azure)', cursor: 'pointer' }}
          />
        </div>
      </div>

      {/* 2. Profile Completion Progress */}
      {completion && (
        <div className="card" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text1)' }}>
              Complete your profile to unlock all statutory alerts
            </span>
            <span style={{ fontSize: '13px', fontWeight: 800, color: 'var(--azure)' }}>{completion.percent}%</span>
          </div>

          <div style={{ height: '7px', borderRadius: '4px', background: 'var(--field)', overflow: 'hidden', marginBottom: '14px' }}>
            <div style={{ width: `${completion.percent}%`, height: '100%', background: 'var(--ink)', borderRadius: '4px' }} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
            {completion.items.map((item) => (
              <div key={item.key} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text2)' }}>
                {item.complete ? (
                  <CheckCircle2 size={15} color="var(--ok)" />
                ) : (
                  <Circle size={15} color="var(--text3)" />
                )}
                <span style={{ textTransform: 'capitalize' }}>{item.key.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Grouped Settings Card (Screen 4 in ui-refrence.png) */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px 4px', fontSize: '12px', fontWeight: 800, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Main Settings
        </div>

        {/* Row 1: Two-step verification */}
        <div
          onClick={() => setShowMfaWizard(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid var(--hairline)',
            cursor: 'pointer',
            transition: 'background 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--surface-muted)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <ShieldCheck size={18} color="var(--azure)" />
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text1)' }}>Two-step verification</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: user?.mfa_enrolled ? 'var(--ok)' : 'var(--warn)' }}>
              {user?.mfa_enrolled ? 'On' : 'Setup required'}
            </span>
            <ChevronRight size={16} color="var(--text3)" />
          </div>
        </div>

        {/* Row 2: Passkeys */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid var(--hairline)',
            cursor: 'pointer',
            transition: 'background 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--surface-muted)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <KeyRound size={18} color="var(--azure)" />
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text1)' }}>Passkeys</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text2)' }}>1</span>
            <ChevronRight size={16} color="var(--text3)" />
          </div>
        </div>

        {/* Row 3: Devices and sessions */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid var(--hairline)',
            cursor: 'pointer',
            transition: 'background 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--surface-muted)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Smartphone size={18} color="var(--azure)" />
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text1)' }}>Devices and sessions</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text2)' }}>{sessions.length}</span>
            <ChevronRight size={16} color="var(--text3)" />
          </div>
        </div>

        {/* Row 4: Language */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid var(--hairline)',
            cursor: 'pointer',
            transition: 'background 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--surface-muted)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Globe size={18} color="var(--azure)" />
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text1)' }}>Language</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text2)' }}>English</span>
            <ChevronRight size={16} color="var(--text3)" />
          </div>
        </div>

        {/* Row 5: Privacy policy */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            cursor: 'pointer',
            transition: 'background 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--surface-muted)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Lock size={18} color="var(--azure)" />
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text1)' }}>Privacy policy & DPDP 2023</span>
          </div>
          <ChevronRight size={16} color="var(--text3)" />
        </div>
      </div>

      {/* 4. Active Sessions List with Revoke & Sign out everywhere */}
      <div className="card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 800, color: 'var(--text1)' }}>
            Active Login Sessions
          </h4>
          <button
            type="button"
            onClick={signOutEverywhere}
            className="btn btn-compact btn-soft"
            style={{ height: '32px', fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <LogOut size={13} />
            <span>Sign out everywhere</span>
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {sessions.map((s) => (
            <div
              key={s.session_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 14px',
                borderRadius: '14px',
                background: 'var(--field)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Smartphone size={16} color="var(--text3)" />
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text1)' }}>
                    {s.device_label || 'Browser Session'} {s.current && '(this session)'}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text3)' }}>
                    Last active {new Date(s.last_seen_at).toLocaleString()}
                  </div>
                </div>
              </div>

              {!s.current && (
                <button
                  type="button"
                  onClick={() => revokeSession(s.session_id)}
                  className="btn btn-compact btn-danger-soft"
                  style={{ height: '28px', padding: '0 10px', fontSize: '11px' }}
                >
                  Revoke
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {showMfaWizard && (
        <MfaEnrolmentWizard
          onClose={() => {
            setShowMfaWizard(false);
            load();
          }}
        />
      )}
    </div>
  );
};
