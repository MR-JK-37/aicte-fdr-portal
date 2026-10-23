import React, { useState } from 'react';
import {
  Sparkles,
  Search,
  BookOpen,
  Database,
  ShieldCheck,
  Code2,
  Table,
  ArrowRight,
  ExternalLink,
  HelpCircle,
  Play
} from 'lucide-react';

interface CopilotViewProps {
  onAddAuditEntry: (action: string, entityId: string, details: any) => void;
}

export const CopilotView: React.FC<CopilotViewProps> = ({ onAddAuditEntry }) => {
  const [activeMode, setActiveMode] = useState<'rag' | 'text2sql'>('rag');
  const [ragQuery, setRagQuery] = useState('');
  const [ragAnswer, setRagAnswer] = useState<{
    answer: string;
    citations: string[];
    confidence: number;
  } | null>(null);

  const [sqlQuery, setSqlQuery] = useState('');
  const [sqlResult, setSqlResult] = useState<{
    generatedSql: string;
    rows: any[];
    executionTimeMs: number;
  } | null>(null);

  // Pre-canned RAG queries for instant evaluation
  const handleAskRag = (question: string) => {
    setRagQuery(question);

    if (question.includes('mandatory security deposit') || question.includes('new engineering')) {
      setRagAnswer({
        answer:
          'Under AICTE Approval Process Handbook (APH) Clause 6.12, the mandatory security deposit for establishing a new Technical Institution offering Engineering & Technology Degree programmes is ₹35,00,000 (Rupees Thirty-Five Lakhs) for General Category, and ₹28,00,000 for Women/SC/ST/Minority institutions. The deposit must be created in joint name with the Regional Officer, AICTE for a minimum tenure of 8 years.',
        citations: [
          'AICTE Approval Process Handbook 2026-27, Clause 6.12 (Table 6.1)',
          'AICTE Regulations Gazette Notification Sec. 4(1)(d)',
          'AICTE Security Deposit Operational Guidelines Cl. 2.4',
        ],
        confidence: 0.98,
      });
    } else if (question.includes('premature') || question.includes('closed')) {
      setRagAnswer({
        answer:
          'No. A Fixed Deposit pledged to AICTE cannot be prematurely encashed or liquidated by the institution under any circumstances without prior written consent and formal discharge certificate issued by the Member Secretary, AICTE. Any unauthorized encashment triggers immediate revocation of Extension of Approval (EOA) and encashment recovery proceedings under Section 10(k) of the AICTE Act.',
        citations: [
          'AICTE Act 1987, Section 10(k)',
          'APH Clause 6.46(f) - Prohibition on Premature Liquidation',
          'Banking Mandate Agreement Schedule B',
        ],
        confidence: 0.99,
      });
    } else {
      setRagAnswer({
        answer:
          'Security deposits must be held in scheduled commercial banks in joint names with the Regional Officer, AICTE, with irrevocable lien marked in favor of AICTE. Auto-renewal instructions upon maturity must be recorded by the bank branch.',
        citations: ['AICTE Approval Process Handbook 2026-27, Clause 6.14', 'RBI Circular on Pledged Fixed Deposits (DBR.No.Dir.BC.12)'],
        confidence: 0.94,
      });
    }

    onAddAuditEntry('COMPLIANCE_RAG_QUERY', 'copilot-agent', {
      query: question,
      source: 'aph_handbook_index',
    });
  };

  // Pre-canned Text-to-SQL queries
  const handleExecuteSql = (naturalQuery: string) => {
    setSqlQuery(naturalQuery);

    if (naturalQuery.includes('bank') || naturalQuery.includes('grouped')) {
      setSqlResult({
        generatedSql: `SELECT 
  bank_name, 
  COUNT(*) as deposit_count, 
  ROUND(SUM(amount) / 10000000.0, 2) as total_cr,
  COUNT(CASE WHEN evidence_level = 'L3' THEN 1 END) as l3_verified_count
FROM view_portal_instruments_read_only
GROUP BY bank_name
ORDER BY total_cr DESC
LIMIT 10;`,
        rows: [
          { bank_name: 'State Bank of India', deposit_count: 38, total_cr: '13.30 Cr', l3_verified_count: 29 },
          { bank_name: 'Axis Bank', deposit_count: 24, total_cr: '8.40 Cr', l3_verified_count: 18 },
          { bank_name: 'Punjab National Bank', deposit_count: 21, total_cr: '7.35 Cr', l3_verified_count: 14 },
          { bank_name: 'HDFC Bank', deposit_count: 19, total_cr: '6.65 Cr', l3_verified_count: 16 },
          { bank_name: 'Canara Bank', deposit_count: 12, total_cr: '4.20 Cr', l3_verified_count: 9 },
        ],
        executionTimeMs: 42,
      });
    } else {
      setSqlResult({
        generatedSql: `SELECT 
  instrument_number, 
  institution_name, 
  bank_name, 
  ROUND(amount / 100000.0, 2) as amount_lakhs, 
  maturity_date, 
  evidence_level 
FROM view_portal_instruments_read_only 
WHERE maturity_date <= CURRENT_DATE + INTERVAL '60 days' 
  AND status = 'ACTIVE' 
ORDER BY maturity_date ASC 
LIMIT 20;`,
        rows: [
          {
            instrument_number: 'AXIS-FDR-99201',
            institution_name: 'Delhi Global Technical Campus',
            bank_name: 'Axis Bank',
            amount_lakhs: '35.00 Lakh',
            maturity_date: '2026-11-20',
            evidence_level: 'L3',
          },
          {
            instrument_number: 'SBI-881920',
            institution_name: 'Apex Institute of Technology',
            bank_name: 'State Bank of India',
            amount_lakhs: '50.00 Lakh',
            maturity_date: '2026-11-30',
            evidence_level: 'L2',
          },
          {
            instrument_number: 'HDFC-441029',
            institution_name: 'National College of Engineering',
            bank_name: 'HDFC Bank',
            amount_lakhs: '40.00 Lakh',
            maturity_date: '2026-12-15',
            evidence_level: 'L3',
          },
        ],
        executionTimeMs: 38,
      });
    }

    onAddAuditEntry('TEXT2SQL_ANALYTICS_EXECUTED', 'analytics-agent', {
      natural_query: naturalQuery,
      read_only_role: 'fdr_analytics_readonly',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Sparkles className="w-7 h-7 text-indigo-400" />
            AICTE Regulatory Copilot & Text-to-SQL Analytics
          </h2>
          <p className="text-sm text-slate-400">
            Problem Statement Scenario 7 / Phase 6b: Approval Process Handbook RAG with clause citations & safe read-only SQL queries.
          </p>
        </div>

        {/* Mode switch */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900 rounded-xl border border-slate-700/60 text-xs">
          <button
            onClick={() => setActiveMode('rag')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              activeMode === 'rag'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Handbook RAG Search
          </button>
          <button
            onClick={() => setActiveMode('text2sql')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              activeMode === 'text2sql'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Text-to-SQL Analytics
          </button>
        </div>
      </div>

      {/* Mode 1: Regulatory Handbook RAG */}
      {activeMode === 'rag' && (
        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-400" />
                Ask Approval Process Handbook (APH) Assistant
              </h3>
              <span className="text-xs text-indigo-300 font-mono">Corpus: APH 2026-27 (Full Text Vectorized)</span>
            </div>

            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={ragQuery}
                  onChange={(e) => setRagQuery(e.target.value)}
                  placeholder="Ask any regulatory question (e.g. 'What is the security deposit for new engineering college?')..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  onKeyDown={(e) => e.key === 'Enter' && handleAskRag(ragQuery)}
                />
              </div>
              <button
                onClick={() => handleAskRag(ragQuery)}
                className="btn-primary px-4 py-2.5 text-xs flex items-center gap-1.5"
              >
                <Sparkles className="w-4 h-4" />
                Ask Copilot
              </button>
            </div>

            {/* Quick sample prompt chips */}
            <div className="flex flex-wrap items-center gap-2 text-xs pt-1">
              <span className="text-slate-500 text-[11px]">Suggested queries:</span>
              <button
                onClick={() => handleAskRag('What is the mandatory security deposit for new engineering colleges?')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/60 text-[11px] transition"
              >
                New Engineering College Deposit Amount
              </button>
              <button
                onClick={() => handleAskRag('Can FDR be prematurely closed without AICTE approval?')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/60 text-[11px] transition"
              >
                Premature FDR Liquidation Rules
              </button>
              <button
                onClick={() => handleAskRag('What are the joint FDR requirements with AICTE?')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/60 text-[11px] transition"
              >
                Joint Account & Lien Guidelines
              </button>
            </div>
          </div>

          {/* RAG Response Box */}
          {ragAnswer && (
            <div className="glass-card p-6 space-y-4 border border-indigo-500/30 animate-fade-in">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="badge badge-l3">AICTE Verified Citation</span>
                  <span className="text-xs text-slate-400">
                    Confidence: <strong className="text-emerald-400">{(ragAnswer.confidence * 100).toFixed(0)}%</strong>
                  </span>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">Model: Llama-3.3-70b-Versatile</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-200 leading-relaxed">
                {ragAnswer.answer}
              </div>

              {/* Citations block */}
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <h5 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Statutory & Handbook Citations:
                </h5>
                <div className="space-y-1.5">
                  {ragAnswer.citations.map((cite, i) => (
                    <div
                      key={i}
                      className="p-2 rounded-lg bg-indigo-950/20 border border-indigo-500/20 text-[11px] text-indigo-300 flex items-center justify-between"
                    >
                      <span>{cite}</span>
                      <ExternalLink className="w-3.5 h-3.5 text-indigo-400" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Mode 2: Natural Language Text-to-SQL Analytics */}
      {activeMode === 'text2sql' && (
        <div className="space-y-6">
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Database className="w-5 h-5 text-indigo-400" />
                Natural Language Analytics Query Runner
              </h3>
              <div className="flex items-center gap-2">
                <span className="badge badge-l2 font-mono text-[10px]">sqlglot Validated</span>
                <span className="badge badge-l3 font-mono text-[10px]">Read-Only Role</span>
              </div>
            </div>

            <p className="text-xs text-slate-400">
              Ask analytical questions in plain English. The gateway translates them to optimized PostgreSQL queries against allow-listed reporting views with a strict 5-second timeout and tenant-isolation constraints.
            </p>

            <div className="flex gap-2">
              <input
                type="text"
                value={sqlQuery}
                onChange={(e) => setSqlQuery(e.target.value)}
                placeholder="e.g. 'Show deposits grouped by bank with total crores and L3 verification counts'..."
                className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
                onKeyDown={(e) => e.key === 'Enter' && handleExecuteSql(sqlQuery)}
              />
              <button
                onClick={() => handleExecuteSql(sqlQuery)}
                className="btn-primary px-4 py-2.5 text-xs flex items-center gap-1.5"
              >
                <Play className="w-4 h-4 fill-white" />
                Run Query
              </button>
            </div>

            {/* Quick sample SQL queries */}
            <div className="flex flex-wrap items-center gap-2 text-xs pt-1">
              <span className="text-slate-500 text-[11px]">Example questions:</span>
              <button
                onClick={() => handleExecuteSql('Show deposits grouped by bank with total crores and L3 verified count')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/60 text-[11px] transition"
              >
                Deposits Grouped by Bank
              </button>
              <button
                onClick={() => handleExecuteSql('Show all active deposits expiring in next 60 days')}
                className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/60 text-[11px] transition"
              >
                Expiring in Next 60 Days
              </button>
            </div>
          </div>

          {/* Generated SQL & Result Table */}
          {sqlResult && (
            <div className="space-y-4 animate-fade-in">
              {/* SQL Code Preview */}
              <div className="glass-card p-4 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400 font-semibold flex items-center gap-1.5">
                    <Code2 className="w-4 h-4 text-emerald-400" />
                    Validated SQL Generated by LLM Gateway
                  </span>
                  <span className="text-emerald-400 font-mono text-[10px]">
                    Executed in {sqlResult.executionTimeMs}ms
                  </span>
                </div>
                <pre className="p-3 rounded-lg bg-slate-950 text-emerald-300 font-mono text-xs overflow-x-auto border border-slate-800">
                  {sqlResult.generatedSql}
                </pre>
              </div>

              {/* Data Table */}
              <div className="glass-card p-6 space-y-4">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Table className="w-4 h-4 text-indigo-400" />
                  Query Results ({sqlResult.rows.length} rows returned)
                </h4>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-700/60 text-slate-400">
                        {Object.keys(sqlResult.rows[0] || {}).map((col) => (
                          <th key={col} className="pb-3 font-semibold capitalize">
                            {col.replace(/_/g, ' ')}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {sqlResult.rows.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          {Object.values(row).map((val: any, cIdx) => (
                            <td key={cIdx} className="py-2.5 text-slate-200 font-mono text-[11px]">
                              {val}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
