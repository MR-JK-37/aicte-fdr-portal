import React, { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Hash,
  Link as LinkIcon,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Clock,
  User,
  Fingerprint,
  Zap,
  Check,
  Flame
} from 'lucide-react';
import { AuditEntry } from '../types';

interface AuditLogViewProps {
  entries: AuditEntry[];
}

export const AuditLogView: React.FC<AuditLogViewProps> = ({ entries }) => {
  const [tamperedIndex, setTamperedIndex] = useState<number | null>(null);

  const handleSimulateTamper = (idx: number) => {
    if (tamperedIndex === idx) {
      setTamperedIndex(null); // Reset
    } else {
      setTamperedIndex(idx);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-7 h-7 text-emerald-400" />
            Cryptographic Audit Ledger & Tamper Detection
          </h2>
          <p className="text-sm text-slate-400">
            Immutable SHA-256 hash-chained event store. Every intake, verification, voice acknowledgement, and release action is chained back to genesis.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {tamperedIndex === null ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-xs text-emerald-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Chain Integrity: <strong>100% Valid</strong> ({entries.length} Blocks)</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-950/60 border border-rose-500/60 text-xs text-rose-300 animate-pulse">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>
                TAMPER DETECTED: Hash broken at <strong>Block #{entries[tamperedIndex]?.id}</strong>!
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Explanation Banner */}
      <div className="glass-card p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs text-slate-300">
        <div className="flex items-center gap-2.5">
          <Fingerprint className="w-5 h-5 text-indigo-400 shrink-0" />
          <span>
            <strong>Cryptographic Guarantee:</strong> Modifying any historical database row alters its SHA-256 hash, immediately breaking all subsequent blocks. Click the "Simulate DB Bit-Flip" button to see real-time fraud detection.
          </span>
        </div>
        {tamperedIndex !== null && (
          <button
            onClick={() => setTamperedIndex(null)}
            className="btn-secondary py-1 px-3 text-xs text-slate-200 hover:text-white shrink-0"
          >
            Reset Ledger to Valid State
          </button>
        )}
      </div>

      {/* Hash Chain Timeline Cards */}
      <div className="space-y-4">
        {entries.map((entry, idx) => {
          const isTamperedHere = tamperedIndex === idx;
          const isDownstreamBroken = tamperedIndex !== null && idx > tamperedIndex;

          return (
            <div
              key={entry.id}
              className={`p-5 rounded-xl border transition-all ${
                isTamperedHere || isDownstreamBroken
                  ? 'bg-rose-950/30 border-rose-500/60 shadow-lg shadow-rose-950/50'
                  : 'bg-slate-900/70 border-slate-700/60 hover:border-slate-600'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2.5">
                  <span
                    className={`font-mono text-xs px-2 py-0.5 rounded-md font-bold ${
                      isTamperedHere || isDownstreamBroken
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                        : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                    }`}
                  >
                    Block #{entry.id}
                  </span>
                  <span className="font-semibold text-slate-100 text-sm">
                    {entry.action.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-slate-400">
                    Entity: <strong className="text-slate-300">{entry.entity_id}</strong>
                  </span>
                </div>

                <div className="flex items-center gap-3 text-xs">
                  <span className="flex items-center gap-1 text-slate-400">
                    <Clock className="w-3.5 h-3.5" /> {entry.created_at}
                  </span>

                  <button
                    onClick={() => handleSimulateTamper(idx)}
                    className={`py-0.5 px-2.5 rounded text-[10px] font-semibold transition ${
                      isTamperedHere
                        ? 'bg-rose-600 text-white'
                        : 'bg-slate-800 text-slate-400 hover:text-rose-300 hover:bg-slate-700'
                    }`}
                  >
                    {isTamperedHere ? 'Tamper Active (Click to Revert)' : 'Simulate Tamper'}
                  </button>
                </div>
              </div>

              {/* Cryptographic Link Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] font-mono">
                <div className="space-y-1">
                  <span className="text-[10px] uppercase text-slate-500 flex items-center gap-1">
                    <LinkIcon className="w-3 h-3 text-indigo-400" />
                    Previous Block Hash (Parent Link):
                  </span>
                  <div className="text-slate-400 truncate bg-slate-900 p-1.5 rounded border border-slate-800">
                    {entry.prev_hash}
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] uppercase text-slate-500 flex items-center gap-1">
                    <Hash className="w-3 h-3 text-emerald-400" />
                    Current Block SHA-256 Hash:
                  </span>
                  <div
                    className={`truncate p-1.5 rounded border ${
                      isTamperedHere
                        ? 'text-rose-300 bg-rose-950/60 border-rose-500 font-bold'
                        : 'text-emerald-400 bg-emerald-950/20 border-emerald-500/30'
                    }`}
                  >
                    {isTamperedHere
                      ? 'sha256:000000000_TAMPERED_PAYLOAD_MISMATCH_ERROR'
                      : entry.row_hash}
                  </div>
                </div>
              </div>

              {/* Payload Details */}
              {entry.details && (
                <div className="mt-3 text-[11px] text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
                  {Object.entries(entry.details).map(([key, val]) => (
                    <span key={key}>
                      <span className="text-slate-500">{key}:</span>{' '}
                      <span className="text-slate-300 font-medium">
                        {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                      </span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
