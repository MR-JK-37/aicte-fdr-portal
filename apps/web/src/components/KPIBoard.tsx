import React from 'react';
import {
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  FileCheck,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowUpRight,
  Database,
  Building,
} from 'lucide-react';
import { Instrument, InstrumentStatus } from '../types';

interface KPIBoardProps {
  instruments: Instrument[];
  onSelectInstrument: (inst: Instrument) => void;
  onFilterStatus?: (status: InstrumentStatus | 'ALL') => void;
}

export const KPIBoard: React.FC<KPIBoardProps> = ({
  instruments,
  onSelectInstrument,
  onFilterStatus,
}) => {
  const counts = {
    total: instruments.length,
    active: instruments.filter((i) => i.status === 'ACTIVE').length,
    expiring: instruments.filter((i) => i.status === 'EXPIRING').length,
    matured: instruments.filter((i) => i.status === 'MATURED').length,
    renewed: instruments.filter((i) => i.status === 'RENEWED').length,
    released: instruments.filter((i) => i.status === 'RELEASED').length,
    pending: instruments.filter((i) => i.status === 'PENDING_VERIFICATION' || i.status === 'DRAFT').length,
  };

  const evidenceCounts = {
    l0: instruments.filter((i) => i.evidence_level === 'L0').length,
    l1: instruments.filter((i) => i.evidence_level === 'L1').length,
    l2: instruments.filter((i) => i.evidence_level === 'L2').length,
    l3: instruments.filter((i) => i.evidence_level === 'L3').length,
  };

  const totalPaise = instruments.reduce((sum, i) => sum + i.amount, 0);
  const totalCrores = (totalPaise / 1000000000).toFixed(2);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner: Problem vs Solution Metrics */}
      <div className="glass-panel" style={{ padding: '20px 24px', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(6, 182, 212, 0.1))', border: '1px solid var(--border-glow-cyan)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#22d3ee', fontSize: '13px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <Sparkles size={16} />
              AICTE Security Deposit Surveillance Overview
            </div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '26px', fontWeight: 700, marginTop: '4px' }}>
              ₹{totalCrores} Crore FDR Security Pool
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              {counts.total} Total Registered Instruments • Live Multi-Tier Bank Reconciliation Active
            </p>
          </div>

          {/* Quick Metrics: Measured Impact */}
          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            <div style={{ padding: '10px 16px', background: 'rgba(0, 0, 0, 0.3)', borderRadius: 10, border: '1px solid var(--border-glass)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Turnaround</div>
              <div style={{ fontSize: '16px', fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
                1.5 Days <span style={{ fontSize: '11px', color: 'var(--text-muted)', textDecoration: 'line-through' }}>45d</span>
              </div>
            </div>
            <div style={{ padding: '10px 16px', background: 'rgba(0, 0, 0, 0.3)', borderRadius: 10, border: '1px solid var(--border-glass)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Bank Confirmed</div>
              <div style={{ fontSize: '16px', fontWeight: 700, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                84% (L2+) <span style={{ fontSize: '11px', color: 'var(--text-muted)', textDecoration: 'line-through' }}>18%</span>
              </div>
            </div>
            <div style={{ padding: '10px 16px', background: 'rgba(0, 0, 0, 0.3)', borderRadius: 10, border: '1px solid var(--border-glass)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>SLA Compliance</div>
              <div style={{ fontSize: '16px', fontWeight: 700, color: '#a78bfa', display: 'flex', alignItems: 'center', gap: '4px' }}>
                96% on-time <span style={{ fontSize: '11px', color: 'var(--text-muted)', textDecoration: 'line-through' }}>42%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Primary Lifecycle Status Tiles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '14px' }}>
        {[
          { label: 'Active', count: counts.active, color: '#34d399', border: 'rgba(16, 185, 129, 0.3)', bg: 'rgba(16, 185, 129, 0.1)', status: 'ACTIVE' },
          { label: 'Expiring (T-90/30/7)', count: counts.expiring, color: '#fbbf24', border: 'rgba(245, 158, 11, 0.4)', bg: 'rgba(245, 158, 11, 0.12)', status: 'EXPIRING', pulse: true },
          { label: 'Matured', count: counts.matured, color: '#f87171', border: 'rgba(239, 68, 68, 0.3)', bg: 'rgba(239, 68, 68, 0.1)', status: 'MATURED' },
          { label: 'Renewed', count: counts.renewed, color: '#38bdf8', border: 'rgba(56, 189, 248, 0.3)', bg: 'rgba(56, 189, 248, 0.1)', status: 'RENEWED' },
          { label: 'Released', count: counts.released, color: '#a5b4fc', border: 'rgba(129, 140, 248, 0.3)', bg: 'rgba(129, 140, 248, 0.1)', status: 'RELEASED' },
          { label: 'Pending Review', count: counts.pending, color: '#cbd5e1', border: 'rgba(148, 163, 184, 0.3)', bg: 'rgba(148, 163, 184, 0.08)', status: 'PENDING_VERIFICATION' },
        ].map((tile) => (
          <div
            key={tile.label}
            onClick={() => onFilterStatus && onFilterStatus(tile.status as any)}
            className={`glass-panel ${tile.pulse && tile.count > 0 ? 'glass-panel-glow' : ''}`}
            style={{
              padding: '16px',
              border: `1px solid ${tile.border}`,
              background: tile.bg,
              cursor: 'pointer',
              transition: 'transform 0.15s ease',
            }}
          >
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              {tile.label}
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '28px', fontWeight: 700, color: tile.color, marginTop: '6px' }}>
              {tile.count}
            </div>
          </div>
        ))}
      </div>

      {/* Evidence Tier Distribution (L0 -> L3) */}
      <div className="glass-panel" style={{ padding: '20px 24px' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={20} color="#22d3ee" />
          Evidence Tier Distribution (Multi-Tier Verification)
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          <div style={{ padding: '14px', borderRadius: 12, background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(100, 116, 139, 0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span className="badge-evidence badge-l0">L0 • Unverified</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '18px' }}>{evidenceCounts.l0}</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Declared by institution; no OCR or scan match yet.</div>
          </div>

          <div style={{ padding: '14px', borderRadius: 12, background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span className="badge-evidence badge-l1">L1 • OCR & Officer Verified</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '18px', color: '#fde68a' }}>{evidenceCounts.l1}</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>OCR + Pydantic validation confirmed by Scrutiny Officer.</div>
          </div>

          <div style={{ padding: '14px', borderRadius: 12, background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(6, 182, 212, 0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span className="badge-evidence badge-l2">L2 • Bank Confirmation</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '18px', color: '#a5f3fc' }}>{evidenceCounts.l2}</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Bank branch reply matched with lien confirmation.</div>
          </div>

          <div style={{ padding: '14px', borderRadius: 12, background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(16, 185, 129, 0.4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span className="badge-evidence badge-l3">L3 • Statement Reconciliation</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '18px', color: '#6ee7b7' }}>{evidenceCounts.l3}</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Bank statement CSV reconciliation with UTR match.</div>
          </div>
        </div>
      </div>

      {/* Instruments Table */}
      <div className="glass-panel" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 600 }}>Active Security Deposit Register</h3>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Showing {instruments.length} Instruments</span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)', textTransform: 'uppercase', fontSize: '11px', letterSpacing: '0.05em' }}>
                <th style={{ padding: '10px 12px' }}>FDR Number</th>
                <th style={{ padding: '10px 12px' }}>Institution</th>
                <th style={{ padding: '10px 12px' }}>Bank & Branch</th>
                <th style={{ padding: '10px 12px' }}>Amount</th>
                <th style={{ padding: '10px 12px' }}>Maturity Date</th>
                <th style={{ padding: '10px 12px' }}>Status</th>
                <th style={{ padding: '10px 12px' }}>Evidence</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {instruments.map((inst) => {
                const amountCr = (inst.amount / 1000000000).toFixed(2);
                return (
                  <tr
                    key={inst.id}
                    style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', transition: 'background 0.15s ease' }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#38bdf8' }}>
                      {inst.instrument_number}
                    </td>
                    <td style={{ padding: '12px', fontWeight: 500 }}>{inst.institution_name}</td>
                    <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>
                      {inst.bank_name} <br />
                      <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{inst.branch_ifsc}</span>
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      ₹{amountCr} Cr
                    </td>
                    <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>{inst.maturity_date}</td>
                    <td style={{ padding: '12px' }}>
                      <span className={`status-pill status-${inst.status.toLowerCase()}`}>
                        {inst.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span className={`badge-evidence badge-${inst.evidence_level.toLowerCase()}`}>
                        {inst.evidence_level}
                      </span>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>
                      <button
                        onClick={() => onSelectInstrument(inst)}
                        style={{
                          padding: '4px 10px',
                          borderRadius: 6,
                          background: 'rgba(6, 182, 212, 0.15)',
                          border: '1px solid rgba(6, 182, 212, 0.3)',
                          color: '#22d3ee',
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
