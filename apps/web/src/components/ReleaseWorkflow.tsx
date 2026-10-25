import React, { useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { KeyRound, CheckCircle2, AlertCircle } from 'lucide-react';
import { AppRole } from '../types';
import { useAuth } from '../auth/AuthContext';
import { apiFetch, ProblemError } from '../lib/apiFetch';
import { formatINR } from '@aicte-fdr/shared';
import { useReleaseRequestDetail, useReleaseRequests } from '../hooks/useReleaseRequests';

interface ReleaseWorkflowProps {
  userRole: AppRole;
}

interface DecisionPayload {
  decision: 'APPROVE' | 'REJECT';
  reason: string;
  step_up_token?: string;
}

/**
 * Release Workflow Screen — maker-checker release decision (AICTE APH cl. 6.46).
 * Every field shown here is read from /v1/release-requests; the decision
 * buttons call POST /v1/release-requests/{id}/decision for real — no
 * client-side "approved" state is ever shown without a 2xx from that call
 * (CLAUDE.md non-negotiable #9: never display success you did not observe).
 */
export const ReleaseWorkflow: React.FC<ReleaseWorkflowProps> = ({ userRole }) => {
  const { navigation } = useAuth();
  const queryClient = useQueryClient();

  // AUTH_ROLES_MATRIX.md §2.3: never hard-code role names in UI logic — ask
  // the server-built navigation manifest whether this principal is entitled
  // to the approve_release action instead.
  const canDecide = useMemo(
    () =>
      navigation?.web_sidebar?.some(
        (item: { required_permission?: string | null }) =>
          item.required_permission === 'approve_release'
      ) ?? false,
    [navigation]
  );

  const { data: requests, isLoading, isError, error, refetch } = useReleaseRequests();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const activeId = selectedId ?? requests?.[0]?.id ?? null;
  const { data: detail } = useReleaseRequestDetail(activeId);

  const [reason, setReason] = useState<string>('');
  const [stepUpToken, setStepUpToken] = useState<string>('');
  const [needsStepUp, setNeedsStepUp] = useState<boolean>(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const decisionMutation = useMutation({
    mutationFn: (payload: DecisionPayload) =>
      apiFetch<{ id: string; status: string; decision: string }>(
        `/v1/release-requests/${activeId}/decision`,
        { method: 'POST', body: JSON.stringify(payload) }
      ),
    onSuccess: (res) => {
      setResultMessage(
        res.decision === 'APPROVE'
          ? 'Release authorization approved with step-up verification. Status moved to execution-pending.'
          : 'Release decision recorded as rejected.'
      );
      setErrorMessage(null);
      setNeedsStepUp(false);
      setStepUpToken('');
      queryClient.invalidateQueries({ queryKey: ['release-requests'] });
      queryClient.invalidateQueries({ queryKey: ['release-request', activeId] });
    },
    onError: (err: unknown) => {
      if (err instanceof ProblemError && err.isStepUpRequired) {
        setNeedsStepUp(true);
        setErrorMessage('Enter your current 6-digit authenticator code to confirm this decision.');
        return;
      }
      if (err instanceof ProblemError) {
        setErrorMessage(err.problem.detail || err.problem.title || 'The decision was not accepted.');
        return;
      }
      setErrorMessage('The decision was not accepted. Check your connection and try again.');
    },
  });

  const submitDecision = (decision: 'APPROVE' | 'REJECT') => {
    setResultMessage(null);
    decisionMutation.mutate({
      decision,
      reason,
      step_up_token: needsStepUp && stepUpToken ? stepUpToken : undefined,
    });
  };

  const instInitials = detail
    ? detail.institution_name
        .split(' ')
        .slice(0, 2)
        .map((w) => w[0])
        .join('')
        .toUpperCase()
    : '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
      {/* Header Banner */}
      <div
        className="card"
        style={{
          padding: '24px 28px',
          background: 'linear-gradient(135deg, var(--hero-from), var(--hero-to) 70%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              borderRadius: '999px',
              background: 'rgba(255, 255, 255, 0.7)',
              color: 'var(--azure)',
              fontSize: '12px',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '10px',
            }}
          >
            <KeyRound size={14} />
            Statutory Authorization
          </span>
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '28px',
              fontWeight: 800,
              color: 'var(--text1)',
              margin: '0 0 6px',
            }}
          >
            Security Deposit Release Decision
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text2)', margin: 0, fontWeight: 500 }}>
            Maker-checker authorization separation under AICTE APH cl. 6.46. Maturity alone is never permission to release.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="pill pill-role" style={{ fontSize: '12px', padding: '6px 14px' }}>
            {userRole.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      {isError && (
        <div
          style={{
            padding: '14px 18px',
            borderRadius: '16px',
            background: 'var(--danger-container)',
            color: 'var(--on-danger-container)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '10px',
            fontSize: '13px',
            fontWeight: 600,
          }}
        >
          <span>
            <AlertCircle size={16} style={{ verticalAlign: 'text-bottom', marginRight: 6 }} />
            Failed to load release requests.{' '}
            {error instanceof ProblemError && error.correlationId
              ? `(Correlation ID: ${error.correlationId})`
              : ''}
          </span>
          <button type="button" onClick={() => refetch()} className="btn btn-compact btn-danger">
            Retry
          </button>
        </div>
      )}

      {!isError && isLoading && (
        <div className="card" style={{ padding: '20px 24px', fontSize: 13, color: 'var(--text3)', fontWeight: 600 }}>
          Loading release requests from the server…
        </div>
      )}

      {!isError && !isLoading && (!requests || requests.length === 0) && (
        <div className="card" style={{ padding: '20px 24px' }}>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--text2)', fontWeight: 600 }}>
            No release requests are pending a decision right now. A request appears here once an
            institution's security deposit has cleared the completeness checklist and scrutiny
            recommendation — nothing on this screen is simulated or invented.
          </p>
        </div>
      )}

      {!isError && requests && requests.length > 0 && detail && (
        <>
          {resultMessage && (
            <div
              style={{
                padding: '14px 18px',
                borderRadius: '16px',
                background: 'var(--ok-container)',
                color: 'var(--on-ok-container)',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                fontSize: '13px',
                fontWeight: 700,
              }}
            >
              <CheckCircle2 size={18} />
              <span>{resultMessage}</span>
            </div>
          )}

          {errorMessage && !resultMessage && (
            <div
              style={{
                padding: '14px 18px',
                borderRadius: '16px',
                background: 'var(--danger-container)',
                color: 'var(--on-danger-container)',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                fontSize: '13px',
                fontWeight: 700,
              }}
            >
              <AlertCircle size={18} />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Select Instrument (if multiple available) */}
          {requests.length > 1 && (
            <div className="card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text2)' }}>
                Selected Release Request:
              </span>
              <select
                value={activeId ?? ''}
                onChange={(e) => {
                  setSelectedId(e.target.value);
                  setResultMessage(null);
                  setErrorMessage(null);
                  setNeedsStepUp(false);
                }}
                style={{
                  padding: '8px 14px',
                  borderRadius: '12px',
                  background: 'var(--field)',
                  border: 'none',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: 'var(--text1)',
                  outline: 'none',
                  cursor: 'pointer',
                }}
              >
                {requests.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.institution_name} ({r.instrument_number})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* 1. Institution Card with Avatar */}
          <div className="card" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #c9d7f7, #e6edff)',
                color: 'var(--primary)',
                display: 'grid',
                placeItems: 'center',
                fontFamily: 'var(--font-display)',
                fontWeight: 800,
                fontSize: '16px',
                flexShrink: 0,
              }}
            >
              {instInitials}
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: '0 0 2px', fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-display)', color: 'var(--text1)' }}>
                {detail.institution_name}
              </h3>
              <p style={{ margin: 0, fontSize: '13px', color: 'var(--text3)', fontWeight: 600 }}>
                Release request • FDR {detail.instrument_number} • {formatINR(Number(detail.amount))}
              </p>
            </div>
            <span className="pill pill-neutral">{detail.status}</span>
          </div>

          {/* 2. Checklist Status Card */}
          <div
            className="card"
            style={{
              padding: '20px 24px',
              background: 'var(--surface)',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
              <CheckCircle2
                size={18}
                color={detail.checklist.every((c) => c.status === 'SATISFIED') ? 'var(--ok)' : 'var(--text3)'}
                style={{ marginTop: '2px', flexShrink: 0 }}
              />
              <p style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: 'var(--text1)', lineHeight: '20px' }}>
                {detail.checklist.length === 0
                  ? 'No clause 6.46 checklist rows recorded yet for this request.'
                  : detail.checklist.every((c) => c.status === 'SATISFIED')
                  ? 'Checklist is complete.'
                  : `${detail.checklist.filter((c) => c.status !== 'SATISFIED').length} of ${detail.checklist.length} checklist rows still open.`}
              </p>
            </div>

            {detail.checklist.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {detail.checklist.map((item) => (
                  <div key={item.rule_id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600, color: 'var(--text2)' }}>
                    <span>{item.label}</span>
                    <span className={`pill ${item.status === 'SATISFIED' ? 'pill-ok' : 'pill-pending'}`}>{item.status}</span>
                  </div>
                ))}
              </div>
            )}

            {detail.recommendation ? (
              <div
                style={{
                  background: 'var(--field)',
                  borderRadius: '16px',
                  padding: '16px 18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text1)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Recommendation: {detail.recommendation}
                  </span>
                  {detail.recommended_at && (
                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text3)' }}>
                      {new Date(detail.recommended_at).toLocaleString()}
                    </span>
                  )}
                </div>
                {detail.recommendation_reason && (
                  <p style={{ margin: 0, fontSize: '13px', color: 'var(--text2)', lineHeight: '18px', fontWeight: 500 }}>
                    {detail.recommendation_reason}
                  </p>
                )}
              </div>
            ) : (
              <p style={{ margin: 0, fontSize: '13px', color: 'var(--text3)', fontWeight: 600 }}>
                No scrutiny recommendation recorded yet.
              </p>
            )}
          </div>

          {!canDecide && (
            <div className="card" style={{ padding: '16px 20px', fontSize: 13, color: 'var(--text2)', fontWeight: 600 }}>
              Your role is not entitled to decide release requests. This view is read-only; only
              the competent authority can approve or reject a release.
            </div>
          )}

          {canDecide && (
            <>
              {/* 3. Reason for Decision Card */}
              <div className="card" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: 'var(--text1)', fontFamily: 'var(--font-display)' }}>
                  Add a reason for your decision
                </h4>
                <div
                  style={{
                    background: 'var(--field)',
                    borderRadius: '16px',
                    padding: '14px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value.slice(0, 500))}
                    placeholder="Reason (optional)"
                    rows={3}
                    style={{
                      width: '100%',
                      background: 'transparent',
                      border: 'none',
                      outline: 'none',
                      resize: 'none',
                      fontSize: '13px',
                      fontWeight: 600,
                      color: 'var(--text1)',
                      fontFamily: 'var(--font-body)',
                    }}
                  />
                  <div style={{ textAlign: 'right', fontSize: '11px', fontWeight: 600, color: 'var(--text3)' }}>
                    {reason.length}/500
                  </div>
                </div>

                {needsStepUp && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--text1)' }}>
                      6-digit authenticator code (step-up verification)
                    </label>
                    <input
                      type="text"
                      inputMode="numeric"
                      maxLength={6}
                      value={stepUpToken}
                      onChange={(e) => setStepUpToken(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      style={{
                        padding: '10px 14px',
                        borderRadius: '12px',
                        background: 'var(--field)',
                        border: 'none',
                        fontSize: '15px',
                        fontWeight: 700,
                        letterSpacing: '0.2em',
                        color: 'var(--text1)',
                        outline: 'none',
                      }}
                    />
                  </div>
                )}
              </div>

              {/* 4. Action Buttons */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => submitDecision('APPROVE')}
                  disabled={decisionMutation.isPending || (needsStepUp && stepUpToken.length !== 6)}
                  className="btn btn-primary btn-block"
                  style={{ height: '48px', fontSize: '15px' }}
                >
                  {decisionMutation.isPending ? 'Submitting…' : 'Approve with step-up'}
                </button>

                <button
                  type="button"
                  onClick={() => submitDecision('REJECT')}
                  disabled={decisionMutation.isPending}
                  className="btn btn-danger-soft btn-block"
                  style={{ height: '48px', fontSize: '15px' }}
                >
                  Reject
                </button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};
