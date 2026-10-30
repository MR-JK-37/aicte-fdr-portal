import React, { useEffect, useState } from 'react';
import { Inbox, Building2, RefreshCw, AlertCircle, ChevronRight } from 'lucide-react';
import { api } from '../lib/apiClient';

interface QueueItem {
  case_id: string;
  entity_type: string;
  title: string;
  institution_id: string;
  institution_name: string;
  status: string;
  created_at: string;
  assigned_to_user_id: string | null;
}

interface IntakeQueueViewProps {
  /** Opens the case in Search & Views, pre-filtered by institution name. */
  onOpenCase?: (query: string) => void;
}

const cardStyle: React.CSSProperties = {
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  borderRadius: '20px',
  padding: '24px',
  boxShadow: 'var(--shadow-card)',
};

/**
 * Intake / Scrutiny Queue — reads the real GET /v1/queues/intake and
 * GET /v1/queues/scrutiny endpoints (app/queues/router.py, F-24). These
 * endpoints existed and were tenant-scoped correctly, but no web screen
 * ever called them and the sidebar's nav list (App.tsx's ROLE_NAV_KEYS) had
 * no entry for intake_officer/scrutiny_officer to reach one — newly
 * submitted instruments were sitting in the database with nothing in the
 * UI to show staff they existed. This is that missing screen.
 */
export const IntakeQueueView: React.FC<IntakeQueueViewProps> = ({ onOpenCase }) => {
  const [tab, setTab] = useState<'intake' | 'scrutiny'>('intake');
  const [items, setItems] = useState<QueueItem[]>([]);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  const load = async (which: 'intake' | 'scrutiny') => {
    setIsLoading(true);
    setIsError(false);
    const { data, error } = await api.GET(
      which === 'intake' ? '/v1/queues/intake' : '/v1/queues/scrutiny'
    );
    if (error || !data) {
      setIsError(true);
      setItems([]);
    } else {
      setItems(data as QueueItem[]);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    load(tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
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
            <Inbox size={14} />
            Casework Queue
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
            {tab === 'intake' ? 'Intake Queue' : 'Scrutiny Queue'}
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text2)', margin: 0, fontWeight: 500 }}>
            {tab === 'intake'
              ? 'Pending onboarding requests and newly submitted instruments awaiting intake review.'
              : 'Instruments currently under scrutiny.'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => load(tab)}
          className="btn btn-compact"
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
        {(['intake', 'scrutiny'] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`chip ${tab === t ? 'chip-active' : ''}`}
            style={{
              padding: '8px 16px',
              borderRadius: '999px',
              border: 'none',
              fontSize: '13px',
              fontWeight: 700,
              cursor: 'pointer',
              background: tab === t ? 'var(--ink)' : 'var(--field)',
              color: tab === t ? '#FFFFFF' : 'var(--text2)',
            }}
          >
            {t === 'intake' ? 'Intake' : 'Scrutiny'}
          </button>
        ))}
        </div>
        {!isLoading && !isError && (
          <span style={{ fontSize: '12px', color: 'var(--text3)', fontWeight: 700 }}>
            {items.length} {items.length === 1 ? 'case' : 'cases'}
          </span>
        )}
      </div>

      {isError && (
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
            fontWeight: 600,
          }}
        >
          <AlertCircle size={16} />
          <span>
            Could not load this queue. Your role may not be entitled to view it, or the server is
            temporarily unavailable.
          </span>
        </div>
      )}

      {!isError && isLoading && (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--text3)', fontWeight: 600 }}>
            Loading {tab} queue from the server…
          </p>
        </div>
      )}

      {!isError && !isLoading && items.length === 0 && (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--text2)', fontWeight: 600 }}>
            Nothing in the {tab} queue right now. Items appear here as soon as an institution
            submits or a case enters scrutiny — nothing on this screen is simulated.
          </p>
        </div>
      )}

      {!isError && !isLoading && items.length > 0 && (
        <div style={{ ...cardStyle, padding: 0, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--field)' }}>
                {['Institution', 'Case', 'Status', 'Entered queue', ''].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: 'left',
                      padding: '12px 20px',
                      fontSize: '11px',
                      fontWeight: 800,
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      color: 'var(--text3)',
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.case_id}
                  onClick={() => onOpenCase?.(item.institution_name)}
                  onMouseEnter={() => setHoveredId(item.case_id)}
                  onMouseLeave={() => setHoveredId((id) => (id === item.case_id ? null : id))}
                  style={{
                    borderTop: '1px solid var(--border)',
                    cursor: onOpenCase ? 'pointer' : 'default',
                    background: hoveredId === item.case_id ? 'var(--field)' : 'transparent',
                  }}
                >
                  <td style={{ padding: '14px 20px', fontSize: '13px', color: 'var(--text1)', fontWeight: 700 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Building2 size={14} color="var(--text3)" />
                      {item.institution_name}
                    </div>
                  </td>
                  <td style={{ padding: '14px 20px', fontSize: '13px', color: 'var(--text2)', fontWeight: 600 }}>
                    {item.title}
                  </td>
                  <td style={{ padding: '14px 20px' }}>
                    <span className="pill pill-neutral">{item.status}</span>
                  </td>
                  <td style={{ padding: '14px 20px', fontSize: '12px', color: 'var(--text3)', fontWeight: 600 }}>
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                    {onOpenCase && <ChevronRight size={16} color="var(--text3)" />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
