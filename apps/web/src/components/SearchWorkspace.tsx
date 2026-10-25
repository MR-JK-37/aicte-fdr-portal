import React, { useState, useMemo } from 'react';
import { Search, Filter, Bookmark, Download, ArrowUpDown, CheckCircle, AlertTriangle, FileText, Building, X } from 'lucide-react';
import { Instrument, SavedViewPreset, SearchFilterState } from '../types';
import { formatPaiseINR } from '@aicte-fdr/shared';

interface SearchWorkspaceProps {
  instruments: Instrument[];
  onSelectInstrument?: (inst: Instrument) => void;
}

const PRESET_VIEWS: SavedViewPreset[] = [
  {
    id: 'expiring_30_days',
    name: 'Expiring in ≤ 30 Days',
    description: 'Instruments due for maturity or renewal requiring mandatory T-30 outreach',
    filters: { status: ['EXPIRING', 'MATURED'] },
  },
  {
    id: 'pending_l2_bank',
    name: 'Pending Bank Confirmation',
    description: 'Deposits with document-extracted data only, pending direct branch confirmation',
    filters: { evidenceLevel: ['L1'] },
  },
  {
    id: 'high_value_deposit',
    name: 'High Value Statutory Deposits',
    description: 'Major statutory institutional security deposits under enhanced monitoring',
    filters: { minAmountPaise: 400000000 },
  },
  {
    id: 'active_l3_reconciled',
    name: 'Active & Statement Reconciled',
    description: 'Instruments with a matched bank statement line and UTR reference',
    filters: { status: ['ACTIVE'], evidenceLevel: ['L3'] },
  },
];

function matchesPreset(inst: Instrument, preset: SavedViewPreset): boolean {
  if (preset.filters.status && !preset.filters.status.includes(inst.status)) return false;
  if (
    preset.filters.evidenceLevel &&
    !preset.filters.evidenceLevel.includes(inst.evidence_level)
  )
    return false;
  if (preset.filters.minAmountPaise && inst.amount < preset.filters.minAmountPaise) return false;
  if (preset.filters.maxAmountPaise && inst.amount > preset.filters.maxAmountPaise) return false;
  return true;
}

export const SearchWorkspace: React.FC<SearchWorkspaceProps> = ({ instruments, onSelectInstrument }) => {
  const [filterState, setFilterState] = useState<SearchFilterState>({
    query: '',
    status: [],
    bank: [],
    minAmountPaise: undefined,
    maxAmountPaise: undefined,
    evidenceLevel: [],
    sortBy: 'maturity_date',
    sortOrder: 'asc',
  });

  const [activePreset, setActivePreset] = useState<string | null>(null);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  // Available unique bank names
  const availableBanks = useMemo(() => {
    return Array.from(new Set(instruments.map((i) => i.bank_name)));
  }, [instruments]);

  // Apply preset view
  const handleApplyPreset = (preset: SavedViewPreset) => {
    if (activePreset === preset.id) {
      setActivePreset(null);
      setFilterState({
        query: '',
        status: [],
        bank: [],
        evidenceLevel: [],
        sortBy: 'maturity_date',
        sortOrder: 'asc',
      });
    } else {
      setActivePreset(preset.id);
      setFilterState((prev) => ({
        ...prev,
        status: preset.filters.status ?? [],
        evidenceLevel: preset.filters.evidenceLevel ?? [],
        minAmountPaise: preset.filters.minAmountPaise,
        maxAmountPaise: preset.filters.maxAmountPaise,
      }));
    }
  };

  // Filtered and sorted instruments
  const filteredInstruments = useMemo(() => {
    return instruments.filter((inst) => {
      if (filterState.query.trim()) {
        const q = filterState.query.toLowerCase().trim();
        const matchesQuery =
          inst.instrument_number.toLowerCase().includes(q) ||
          inst.institution_name.toLowerCase().includes(q) ||
          inst.institution_id.toLowerCase().includes(q) ||
          inst.bank_name.toLowerCase().includes(q) ||
          (inst.utr_number && inst.utr_number.toLowerCase().includes(q));
        if (!matchesQuery) return false;
      }

      if (filterState.status.length > 0 && !filterState.status.includes(inst.status)) {
        return false;
      }

      if (filterState.bank.length > 0 && !filterState.bank.includes(inst.bank_name)) {
        return false;
      }

      if (filterState.evidenceLevel.length > 0 && !filterState.evidenceLevel.includes(inst.evidence_level)) {
        return false;
      }

      if (filterState.minAmountPaise !== undefined && inst.amount < filterState.minAmountPaise) {
        return false;
      }
      if (filterState.maxAmountPaise !== undefined && inst.amount > filterState.maxAmountPaise) {
        return false;
      }

      return true;
    }).sort((a, b) => {
      const multiplier = filterState.sortOrder === 'asc' ? 1 : -1;
      if (filterState.sortBy === 'amount') {
        return (a.amount - b.amount) * multiplier;
      }
      return (new Date(a.maturity_date).getTime() - new Date(b.maturity_date).getTime()) * multiplier;
    });
  }, [instruments, filterState]);

  // Handle Export CSV
  const handleExportCSV = () => {
    if (filteredInstruments.length === 0) return;

    const headers = [
      'ID',
      'Instrument Number',
      'Institution ID',
      'Institution Name',
      'Bank Name',
      'IFSC Code',
      'Amount (INR)',
      'Maturity Date',
      'Status',
      'Evidence Level',
      'UTR Number',
    ];

    const rows = filteredInstruments.map((i) => [
      i.id,
      i.instrument_number,
      i.institution_id,
      `"${i.institution_name.replace(/"/g, '""')}"`,
      `"${i.bank_name}"`,
      i.branch_ifsc,
      (i.amount / 100).toFixed(2),
      i.maturity_date,
      i.status,
      i.evidence_level,
      i.utr_number ?? '',
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `aicte_fdr_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setExportNotice(`Exported ${filteredInstruments.length} records to CSV successfully.`);
    setTimeout(() => setExportNotice(null), 4000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Header Banner */}
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
            <Search size={14} />
            Institutional Registers
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
            Universal Search & Saved Views
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text2)', margin: 0, fontWeight: 500 }}>
            Query across all regulatory security deposits, UTR execution hashes, and institutional records.
          </p>
        </div>

        <button
          type="button"
          onClick={handleExportCSV}
          disabled={filteredInstruments.length === 0}
          className="btn btn-primary"
          style={{ height: '42px', padding: '0 18px', fontSize: '13px' }}
        >
          <Download size={15} />
          <span>Export CSV ({filteredInstruments.length})</span>
        </button>
      </div>

      {/* 2. Global Search Bar */}
      <div className="card" style={{ padding: '16px 20px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: 'var(--field)',
            borderRadius: '999px',
            padding: '0 18px',
            height: '48px',
          }}
        >
          <Search size={18} color="var(--azure)" />
          <input
            type="text"
            value={filterState.query}
            onChange={(e) => setFilterState((prev) => ({ ...prev, query: e.target.value }))}
            placeholder="Search by FDR Number, Institution Name, AICTE Code, Bank, or UTR..."
            style={{
              flex: 1,
              border: 'none',
              background: 'transparent',
              outline: 'none',
              fontSize: '14px',
              fontWeight: 600,
              color: 'var(--text1)',
            }}
          />
          {filterState.query && (
            <button
              type="button"
              onClick={() => setFilterState((prev) => ({ ...prev, query: '' }))}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)' }}
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {exportNotice && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '16px',
            background: 'var(--ok-container)',
            color: 'var(--on-ok-container)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 700,
          }}
        >
          <CheckCircle size={16} />
          <span>{exportNotice}</span>
        </div>
      )}

      {/* 3. Regulatory Saved Views Presets */}
      <div>
        <div
          style={{
            fontSize: '12px',
            fontWeight: 800,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            color: 'var(--text3)',
            marginBottom: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Bookmark size={14} color="var(--azure)" />
          Regulatory Presets (Saved Views)
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
          {PRESET_VIEWS.map((preset) => {
            const isSelected = activePreset === preset.id;
            const matchCount = instruments.filter((i) => matchesPreset(i, preset)).length;

            return (
              <div
                key={preset.id}
                onClick={() => handleApplyPreset(preset)}
                className="card"
                style={{
                  padding: '14px 16px',
                  cursor: 'pointer',
                  border: isSelected ? '2px solid var(--azure)' : 'none',
                  background: isSelected ? 'var(--primary-container)' : 'var(--surface)',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: isSelected ? 'var(--primary)' : 'var(--text1)' }}>
                    {preset.name}
                  </span>
                  <span
                    className={isSelected ? 'pill pill-ok' : 'pill pill-neutral'}
                    style={{ fontSize: '11px', padding: '2px 8px' }}
                  >
                    {matchCount}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--text3)', lineHeight: '16px', fontWeight: 500 }}>
                  {preset.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Filter Toolbar */}
      <div
        className="card"
        style={{
          padding: '14px 20px',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '10px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 700, color: 'var(--text2)' }}>
            <Filter size={15} color="var(--azure)" /> Filters:
          </span>

          <select
            value={filterState.status[0] ?? ''}
            onChange={(e) =>
              setFilterState((prev) => ({
                ...prev,
                status: e.target.value ? [e.target.value] : [],
              }))
            }
            style={{
              padding: '6px 12px',
              borderRadius: '10px',
              background: 'var(--field)',
              border: 'none',
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--text1)',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="EXPIRING">EXPIRING</option>
            <option value="MATURED">MATURED</option>
            <option value="RELEASED">RELEASED</option>
          </select>

          <select
            value={filterState.bank[0] ?? ''}
            onChange={(e) =>
              setFilterState((prev) => ({
                ...prev,
                bank: e.target.value ? [e.target.value] : [],
              }))
            }
            style={{
              padding: '6px 12px',
              borderRadius: '10px',
              background: 'var(--field)',
              border: 'none',
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--text1)',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="">All Scheduled Banks</option>
            {availableBanks.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>

          <select
            value={filterState.evidenceLevel[0] ?? ''}
            onChange={(e) =>
              setFilterState((prev) => ({
                ...prev,
                evidenceLevel: e.target.value ? [e.target.value] : [],
              }))
            }
            style={{
              padding: '6px 12px',
              borderRadius: '10px',
              background: 'var(--field)',
              border: 'none',
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--text1)',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="">All Evidence Tiers</option>
            <option value="L0">L0: Declared Only</option>
            <option value="L1">L1: OCR Verified</option>
            <option value="L2">L2: Bank Confirmed</option>
            <option value="L3">L3: Ledger Reconciled</option>
          </select>

          {(filterState.status.length > 0 || filterState.bank.length > 0 || filterState.evidenceLevel.length > 0 || activePreset) && (
            <button
              type="button"
              onClick={() => {
                setActivePreset(null);
                setFilterState((prev) => ({
                  ...prev,
                  status: [],
                  bank: [],
                  evidenceLevel: [],
                  minAmountPaise: undefined,
                  maxAmountPaise: undefined,
                }));
              }}
              className="chip"
              style={{ fontSize: '11px', fontWeight: 700, padding: '4px 10px', background: 'var(--field-strong)' }}
            >
              Reset Filters
            </button>
          )}
        </div>

        {/* Sort Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text3)' }}>Sort by:</span>
          <select
            value={filterState.sortBy}
            onChange={(e) => setFilterState((prev) => ({ ...prev, sortBy: e.target.value as any }))}
            style={{
              padding: '6px 12px',
              borderRadius: '10px',
              background: 'var(--field)',
              border: 'none',
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--text1)',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="maturity_date">Maturity Date</option>
            <option value="amount">Deposit Amount</option>
          </select>
          <button
            type="button"
            onClick={() => setFilterState((prev) => ({ ...prev, sortOrder: prev.sortOrder === 'asc' ? 'desc' : 'asc' }))}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'var(--field)',
              border: 'none',
              display: 'grid',
              placeItems: 'center',
              cursor: 'pointer',
              color: 'var(--text2)',
            }}
            title={`Toggle sort order (Currently ${filterState.sortOrder.toUpperCase()})`}
          >
            <ArrowUpDown size={14} />
          </button>
        </div>
      </div>

      {/* 5. Results Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--hairline)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text1)' }}>Matching Records</span>
            <span className="pill pill-ok" style={{ fontSize: '11px', padding: '2px 8px' }}>
              {filteredInstruments.length}
            </span>
          </div>

          <div style={{ fontSize: '12px', color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>
            Total Value: <strong>{formatPaiseINR(filteredInstruments.reduce((acc, curr) => acc + curr.amount, 0))}</strong>
          </div>
        </div>

        {filteredInstruments.length === 0 ? (
          <div style={{ padding: '48px 24px', textAlign: 'center' }}>
            <AlertTriangle size={32} color="var(--warn)" style={{ margin: '0 auto 10px' }} />
            <h4 style={{ margin: '0 0 6px', fontSize: '16px', fontWeight: 800, color: 'var(--text1)' }}>
              No Matching Security Deposits
            </h4>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--text3)' }}>
              No instruments match your search criteria. Try adjusting queries or filters.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'var(--surface-muted)', color: 'var(--text3)', textTransform: 'uppercase', fontSize: '11px', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '12px 14px' }}>FDR Number</th>
                  <th style={{ padding: '12px 14px' }}>Institution</th>
                  <th style={{ padding: '12px 14px' }}>Bank & Branch</th>
                  <th style={{ padding: '12px 14px', textAlign: 'right' }}>Amount</th>
                  <th style={{ padding: '12px 14px' }}>Maturity</th>
                  <th style={{ padding: '12px 14px', textAlign: 'center' }}>Status</th>
                  <th style={{ padding: '12px 14px', textAlign: 'center' }}>Evidence</th>
                  <th style={{ padding: '12px 14px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredInstruments.map((inst) => {
                  const isWarn = inst.status === 'EXPIRING';
                  const isOk = inst.status === 'ACTIVE';
                  const isErr = inst.status === 'MATURED';
                  const pillClass = isWarn ? 'pill-warn' : isOk ? 'pill-ok' : isErr ? 'pill-error' : 'pill-pending';

                  return (
                    <tr
                      key={inst.id}
                      style={{ borderTop: '1px solid var(--hairline)', cursor: 'pointer', transition: 'background 0.15s ease' }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--surface-muted)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                      onClick={() => onSelectInstrument && onSelectInstrument(inst)}
                    >
                      <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--primary)' }}>
                        {inst.instrument_number}
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text1)' }}>{inst.institution_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>{inst.institution_id}</div>
                      </td>
                      <td style={{ padding: '12px 14px', color: 'var(--text2)' }}>
                        <div>{inst.bank_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>{inst.branch_ifsc}</div>
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text1)' }}>
                        {formatPaiseINR(inst.amount)}
                      </td>
                      <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: 'var(--text2)' }}>
                        {inst.maturity_date}
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                        <span className={`pill ${pillClass}`}>{inst.status}</span>
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                        <span className="pill pill-neutral" style={{ fontSize: '11px' }}>
                          {inst.evidence_level}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectInstrument && onSelectInstrument(inst);
                          }}
                          className="btn btn-compact btn-soft"
                          style={{ height: '30px', padding: '0 12px', fontSize: '11px' }}
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
        )}
      </div>
    </div>
  );
};
