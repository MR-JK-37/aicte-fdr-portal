import React, { useState, useMemo } from 'react';
import { Search, Filter, Bookmark, Download, ArrowUpDown, CheckCircle, AlertTriangle, FileText, Building, Hash } from 'lucide-react';
import { Instrument, SavedViewPreset, SearchFilterState } from '../types';

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
    badgeCount: 2,
  },
  {
    id: 'pending_l2_bank',
    name: 'Pending Bank Confirmation (L1 Only)',
    description: 'Deposits with only portal OCR extraction pending direct branch confirmation',
    filters: { evidenceLevel: ['L1'] },
    badgeCount: 1,
  },
  {
    id: 'high_value_deposit',
    name: 'High Value (≥ ₹40 Lakhs)',
    description: 'Major statutory institutional security deposits under enhanced monitoring',
    filters: { minAmountPaise: 400000000 },
    badgeCount: 2,
  },
  {
    id: 'active_l3_reconciled',
    name: 'Active & Statement Reconciled (L3)',
    description: 'Triple-verified instruments with matched bank statements and UTR references',
    filters: { status: ['ACTIVE'], evidenceLevel: ['L3'] },
    badgeCount: 2,
  },
];

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
      // Toggle off
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
      // Text query match across instrument_number, institution_name, institution_id, bank_name, UTR
      if (filterState.query.trim()) {
        const q = filterState.query.toLowerCase().trim();
        const matchesNumber = inst.instrument_number.toLowerCase().includes(q);
        const matchesInst = inst.institution_name.toLowerCase().includes(q) || inst.institution_id.toLowerCase().includes(q);
        const matchesBank = inst.bank_name.toLowerCase().includes(q);
        const matchesUtr = inst.utr_number ? inst.utr_number.toLowerCase().includes(q) : false;
        if (!matchesNumber && !matchesInst && !matchesBank && !matchesUtr) {
          return false;
        }
      }

      // Status filter
      if (filterState.status.length > 0 && !filterState.status.includes(inst.status)) {
        return false;
      }

      // Bank filter
      if (filterState.bank.length > 0 && !filterState.bank.includes(inst.bank_name)) {
        return false;
      }

      // Evidence level filter
      if (filterState.evidenceLevel.length > 0 && !filterState.evidenceLevel.includes(inst.evidence_level)) {
        return false;
      }

      // Amount filter
      if (filterState.minAmountPaise && inst.amount < filterState.minAmountPaise) {
        return false;
      }
      if (filterState.maxAmountPaise && inst.amount > filterState.maxAmountPaise) {
        return false;
      }

      return true;
    }).sort((a, b) => {
      if (filterState.sortBy === 'maturity_date') {
        const diff = new Date(a.maturity_date).getTime() - new Date(b.maturity_date).getTime();
        return filterState.sortOrder === 'asc' ? diff : -diff;
      }
      if (filterState.sortBy === 'amount') {
        const diff = a.amount - b.amount;
        return filterState.sortOrder === 'asc' ? diff : -diff;
      }
      return 0;
    });
  }, [instruments, filterState]);

  // Export filtered list to CSV
  const handleExportCSV = () => {
    const headers = ['ID', 'Instrument Number', 'Institution ID', 'Institution Name', 'Bank', 'IFSC', 'Amount (INR)', 'Maturity Date', 'Status', 'Evidence Level', 'UTR'];
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

  const formatPaiseINR = (paise: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(paise / 100);
  };

  return (
    <div className="space-y-6">
      {/* Search Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-purple-950/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                <Search size={22} />
              </span>
              <h1 className="text-2xl font-bold tracking-tight text-white">Universal Search & Saved Views</h1>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Query across all regulatory security deposits, UTR execution hashes, and institutional records (F-17)
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleExportCSV}
              disabled={filteredInstruments.length === 0}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 disabled:opacity-50 transition-colors"
            >
              <Download size={14} />
              Export Result ({filteredInstruments.length})
            </button>
          </div>
        </div>

        {/* Global Search Bar */}
        <div className="mt-6 relative">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-cyan-400" />
          <input
            type="text"
            value={filterState.query}
            onChange={(e) => setFilterState((prev) => ({ ...prev, query: e.target.value }))}
            placeholder="Search by FDR Number, Institution Name, AICTE Code, Bank, or UTR..."
            className="w-full pl-12 pr-4 py-3 rounded-xl bg-slate-950/90 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all text-sm"
          />
          {filterState.query && (
            <button
              onClick={() => setFilterState((prev) => ({ ...prev, query: '' }))}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-white"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {exportNotice && (
        <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle size={14} />
          {exportNotice}
        </div>
      )}

      {/* Saved View Presets */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
          <Bookmark size={14} className="text-cyan-400" />
          Regulatory Presets (Saved Views)
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {PRESET_VIEWS.map((preset) => {
            const isSelected = activePreset === preset.id;
            return (
              <button
                key={preset.id}
                onClick={() => handleApplyPreset(preset)}
                className={`text-left p-3.5 rounded-xl border transition-all ${
                  isSelected
                    ? 'bg-purple-950/50 border-cyan-400 text-white shadow-lg shadow-cyan-950/20'
                    : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-cyan-300">{preset.name}</span>
                  {preset.badgeCount !== undefined && (
                    <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                      {preset.badgeCount}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-[11px] text-slate-400 line-clamp-2">{preset.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Filters Bar & Sorting Controls */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5 text-slate-400 font-semibold">
            <Filter size={14} className="text-cyan-400" /> Filters:
          </span>

          {/* Status filter */}
          <select
            value={filterState.status[0] ?? ''}
            onChange={(e) =>
              setFilterState((prev) => ({
                ...prev,
                status: e.target.value ? [e.target.value] : [],
              }))
            }
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-400"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="EXPIRING">EXPIRING</option>
            <option value="MATURED">MATURED</option>
            <option value="RELEASE_REQUESTED">RELEASE_REQUESTED</option>
          </select>

          {/* Bank filter */}
          <select
            value={filterState.bank[0] ?? ''}
            onChange={(e) =>
              setFilterState((prev) => ({
                ...prev,
                bank: e.target.value ? [e.target.value] : [],
              }))
            }
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-400"
          >
            <option value="">All Scheduled Banks</option>
            {availableBanks.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>

          {/* Evidence level filter */}
          <select
            value={filterState.evidenceLevel[0] ?? ''}
            onChange={(e) =>
              setFilterState((prev) => ({
                ...prev,
                evidenceLevel: e.target.value ? [e.target.value] : [],
              }))
            }
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-400"
          >
            <option value="">All Evidence Levels</option>
            <option value="L1">L1: Scanned OCR</option>
            <option value="L2">L2: Bank Confirmed</option>
            <option value="L3">L3: Statement Reconciled</option>
          </select>

          {(filterState.status.length > 0 || filterState.bank.length > 0 || filterState.evidenceLevel.length > 0 || activePreset) && (
            <button
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
              className="text-cyan-400 hover:text-cyan-300 underline font-medium"
            >
              Reset Filters
            </button>
          )}
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Sort by:</span>
          <select
            value={filterState.sortBy}
            onChange={(e) => setFilterState((prev) => ({ ...prev, sortBy: e.target.value as any }))}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-400"
          >
            <option value="maturity_date">Maturity Date</option>
            <option value="amount">Deposit Amount</option>
          </select>
          <button
            onClick={() => setFilterState((prev) => ({ ...prev, sortOrder: prev.sortOrder === 'asc' ? 'desc' : 'asc' }))}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-slate-600 text-cyan-400"
            title={`Toggle sort order (Currently ${filterState.sortOrder.toUpperCase()})`}
          >
            <ArrowUpDown size={14} />
          </button>
        </div>
      </div>

      {/* Results Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300">Matching Results</span>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-cyan-950 text-cyan-400 border border-cyan-800">
              {filteredInstruments.length} Records
            </span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            Total Paired Value:{' '}
            <strong className="text-white">
              {formatPaiseINR(filteredInstruments.reduce((acc, curr) => acc + curr.amount, 0))}
            </strong>
          </div>
        </div>

        {filteredInstruments.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <AlertTriangle size={32} className="mx-auto mb-3 text-amber-400 opacity-80" />
            <h3 className="text-base font-semibold text-white">No Matching Security Deposits</h3>
            <p className="mt-1 text-xs text-slate-400 max-w-md mx-auto">
              No instruments match your active search and filter criteria. Try clearing queries or switching presets.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-950/40">
                  <th className="py-3 px-4">Instrument Number</th>
                  <th className="py-3 px-4">Institution</th>
                  <th className="py-3 px-4">Bank & Branch</th>
                  <th className="py-3 px-4 text-right">Amount (₹)</th>
                  <th className="py-3 px-4">Maturity Date</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Evidence</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredInstruments.map((inst) => {
                  const statusColors: Record<string, string> = {
                    ACTIVE: 'bg-emerald-950/60 text-emerald-300 border-emerald-700/60',
                    EXPIRING: 'bg-amber-950/60 text-amber-300 border-amber-700/60',
                    MATURED: 'bg-red-950/60 text-red-300 border-red-700/60',
                    RELEASE_REQUESTED: 'bg-purple-950/60 text-purple-300 border-purple-700/60',
                  };

                  const evidenceBadge: Record<string, { label: string; bg: string }> = {
                    L1: { label: 'L1: OCR', bg: 'bg-slate-800 text-slate-300 border-slate-700' },
                    L2: { label: 'L2: Branch Verified', bg: 'bg-blue-950 text-blue-300 border-blue-800' },
                    L3: { label: 'L3: Reconciled', bg: 'bg-emerald-950 text-emerald-300 border-emerald-800' },
                  };

                  return (
                    <tr
                      key={inst.id}
                      className="hover:bg-slate-900/60 transition-colors group cursor-pointer"
                      onClick={() => onSelectInstrument && onSelectInstrument(inst)}
                    >
                      <td className="py-3.5 px-4 font-mono font-medium text-cyan-300 flex items-center gap-1.5">
                        <FileText size={14} className="text-slate-500 group-hover:text-cyan-400" />
                        {inst.instrument_number}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-white">{inst.institution_name}</div>
                        <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                          <Building size={11} /> {inst.institution_id}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="text-slate-200">{inst.bank_name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{inst.branch_ifsc}</div>
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono font-semibold text-white">
                        {formatPaiseINR(inst.amount)}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-300">{inst.maturity_date}</td>
                      <td className="py-3.5 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${statusColors[inst.status] ?? 'bg-slate-800 text-slate-300'}`}>
                          {inst.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${evidenceBadge[inst.evidence_level]?.bg ?? 'bg-slate-800'}`}>
                          {evidenceBadge[inst.evidence_level]?.label ?? inst.evidence_level}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectInstrument && onSelectInstrument(inst);
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-cyan-950 text-cyan-300 hover:text-cyan-200 border border-slate-700 hover:border-cyan-500/50 text-[11px] font-medium transition-colors"
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
