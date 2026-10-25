import React, { useState } from 'react';
import { Plus, Check, Shield } from 'lucide-react';
import { Instrument, InstrumentStatus } from '../types';
import { formatPaiseINR } from '@aicte-fdr/shared';
import { Kosh } from '../design-system/Kosh';
import { useAuth } from '../auth/AuthContext';

interface KPIBoardProps {
  instruments: Instrument[];
  onSelectInstrument?: (inst: Instrument) => void;
  onFilterStatus?: (status: InstrumentStatus | 'ALL') => void;
}

export const KPIBoard: React.FC<KPIBoardProps> = ({
  instruments,
  onSelectInstrument,
  onFilterStatus,
}) => {
  const { user } = useAuth();
  const [selectedSegment, setSelectedSegment] = useState<'Mine' | 'Team'>('Mine');

  const counts = {
    total: instruments.length,
    active: instruments.filter((i) => i.status === 'ACTIVE').length,
    expiring: instruments.filter((i) => i.status === 'EXPIRING').length,
    matured: instruments.filter((i) => i.status === 'MATURED').length,
    renewed: instruments.filter((i) => i.status === 'RENEWED').length,
    released: instruments.filter((i) => i.status === 'RELEASED').length,
    pending: instruments.filter(
      (i) => i.status === 'PENDING_VERIFICATION' || i.status === 'DRAFT'
    ).length,
  };

  // User display name & greeting
  const firstName = user?.full_name ? user.full_name.split(' ')[0] : 'Anil';
  const regionName = (user as any)?.region || 'South region';

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  const todayFormatted = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date());

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Hero Card */}
      <div className="hero herow">
        <div className="heroT">
          <span className="chipw">{regionName}</span>
          <h1>
            {greeting},<br />
            {firstName}
          </h1>
          <p className="sub">{todayFormatted}</p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onFilterStatus && onFilterStatus('PENDING_VERIFICATION')}
          >
            <Plus size={18} color="#ffffff" />
            <span>New observation</span>
          </button>
        </div>
      </div>

      {/* 2. 4 KPI Tiles Section */}
      <section className="kpis">
        <div
          className="card kpi"
          style={{ cursor: 'pointer' }}
          onClick={() => onFilterStatus && onFilterStatus('ACTIVE')}
        >
          <small>Active instruments</small>
          <b className="big">{counts.active}</b>
          <span className="pill pill-neutral">live from database</span>
        </div>

        <div
          className="card kpi"
          style={{ cursor: 'pointer' }}
          onClick={() => onFilterStatus && onFilterStatus('EXPIRING')}
        >
          <small>Expiring in 90 days</small>
          <b className="big">{counts.expiring}</b>
          <span className="pill pill-warn">live from database</span>
        </div>

        <div
          className="card kpi"
          style={{ cursor: 'pointer' }}
          onClick={() => onFilterStatus && onFilterStatus('PENDING_VERIFICATION')}
        >
          <small>Open observations</small>
          <b className="big">{counts.pending}</b>
          <span className="pill pill-error">live from database</span>
        </div>

        <div
          className="card kpi"
          style={{ cursor: 'pointer' }}
          onClick={() => onFilterStatus && onFilterStatus('PENDING_VERIFICATION')}
        >
          <small>Awaiting bank</small>
          <b className="big">{counts.pending}</b>
          <span className="pill pill-pending">live from database</span>
        </div>
      </section>

      {/* 3. Lower Two-Column Section: Needs action + Evidence attributes */}
      <section className="two-col">
        {/* Left: Needs action table */}
        <div className="card">
          <div className="between">
            <h3>Needs action</h3>
            <div className="segmented">
              <button
                type="button"
                className={selectedSegment === 'Mine' ? 'is-active' : ''}
                aria-selected={selectedSegment === 'Mine'}
                onClick={() => setSelectedSegment('Mine')}
              >
                Mine
              </button>
              <button
                type="button"
                className={selectedSegment === 'Team' ? 'is-active' : ''}
                aria-selected={selectedSegment === 'Team'}
                onClick={() => setSelectedSegment('Team')}
              >
                Team
              </button>
            </div>
          </div>

          {instruments.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Institution</th>
                    <th>FDR no.</th>
                    <th className="num">Amount</th>
                    <th>Maturity</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {instruments.slice(0, 6).map((inst) => {
                    const isWarn = inst.status === 'EXPIRING';
                    const isOk = inst.status === 'ACTIVE';
                    const isErr = inst.status === 'MATURED';
                    const pillCls = isWarn
                      ? 'pill-warn'
                      : isOk
                      ? 'pill-ok'
                      : isErr
                      ? 'pill-error'
                      : 'pill-pending';

                    return (
                      <tr
                        key={inst.id}
                        style={{ cursor: 'pointer' }}
                        onClick={() => onSelectInstrument?.(inst)}
                      >
                        <td>
                          <b>{inst.institution_name}</b>
                          <small>{inst.bank_name || 'Commercial Bank'}</small>
                        </td>
                        <td className="mono">{inst.instrument_number}</td>
                        <td className="num">{formatPaiseINR(inst.amount)}</td>
                        <td>
                          {inst.maturity_date
                            ? new Date(inst.maturity_date).toLocaleDateString('en-GB', {
                                day: '2-digit',
                                month: 'short',
                                year: 'numeric',
                              })
                            : '—'}
                        </td>
                        <td>
                          <span className={`pill ${pillCls}`}>
                            {inst.status === 'EXPIRING'
                              ? 'Expiring in 50 days'
                              : inst.status === 'ACTIVE'
                              ? 'Active · Bank-confirmed'
                              : inst.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="sub" style={{ padding: '16px 0 4px' }}>
              No security deposits need action right now. Items appear here once instruments are
              submitted and recorded in the database.
            </p>
          )}
        </div>

        {/* Right: Evidence attributes legend card */}
        <div className="card">
          <h3>Evidence attributes</h3>
          <p className="sub">Never one score. Each fact keeps its source.</p>

          <div className="legend">
            <div>
              <span className="pill pill-neutral">Declared</span>
              <small>Institution said so</small>
            </div>
            <div>
              <span className="pill pill-pending">Extracted</span>
              <small>Read from a document</small>
            </div>
            <div>
              <span className="pill pill-ok" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <Check size={14} /> Bank-confirmed
              </span>
              <small>Bank answered</small>
            </div>
            <div>
              <span className="pill pill-info" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <Shield size={14} /> Ledger-reconciled
              </span>
              <small>Matched a statement line</small>
            </div>
            <div>
              <span className="pill pill-warn">Inconclusive</span>
              <small>Needs a human decision</small>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
