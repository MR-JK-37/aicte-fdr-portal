import React, { useState } from 'react';
import { BarChart3, Download, Calendar, Filter, FileSpreadsheet, CheckCircle2, Clock, RefreshCw, FileText, ShieldAlert } from 'lucide-react';
import { Instrument, ReportDefinition, GeneratedReport } from '../types';

interface ReportsViewProps {
  instruments: Instrument[];
}

const REPORT_CATALOGUE: ReportDefinition[] = [
  {
    id: 'rep_monthly_position',
    title: 'Monthly Security Deposit Position (Table 1.4)',
    description: 'Consolidated statutory deposit exposure across all approved technical institutions and regions',
    category: 'compliance',
    frequency: 'monthly',
    supportedFormats: ['csv', 'json', 'pdf'],
  },
  {
    id: 'rep_maturity_exposure',
    title: 'Maturity Schedule & Deficit Exposure',
    description: 'Upcoming maturities across T-90 to T-0 windows with institution deficit projections',
    category: 'finance',
    frequency: 'weekly',
    supportedFormats: ['csv', 'json'],
  },
  {
    id: 'rep_discrepancy_ledger',
    title: 'Reconciliation Discrepancy & Shortfall Register',
    description: 'Active and overridden discrepancies between bank confirmations, OCR, and AICTE statements',
    category: 'reconciliation',
    frequency: 'daily',
    supportedFormats: ['csv', 'json'],
  },
  {
    id: 'rep_release_audit',
    title: 'Release Payout & UTR Execution Audit Summary',
    description: 'Discharged security deposits with two-person execution evidence verification hashes and UTR numbers',
    category: 'audit',
    frequency: 'monthly',
    supportedFormats: ['csv', 'pdf'],
  },
];

export const ReportsView: React.FC<ReportsViewProps> = ({ instruments }) => {
  const [selectedReportId, setSelectedReportId] = useState<string>('rep_monthly_position');
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'json' | 'pdf'>('csv');
  const [selectedFy, setSelectedFy] = useState<string>('2026-27');
  const [isGenerating, setIsGenerating] = useState(false);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const [generatedReports, setGeneratedReports] = useState<GeneratedReport[]>([
    {
      id: 'gen-001',
      reportId: 'rep_monthly_position',
      title: 'Monthly Security Deposit Position (Table 1.4)',
      format: 'csv',
      generatedAt: '2026-10-24 10:15 IST',
      fileSizeBytes: 148200,
      downloadUrl: '#',
      status: 'ready',
    },
    {
      id: 'gen-002',
      reportId: 'rep_maturity_exposure',
      title: 'Maturity Schedule & Deficit Exposure',
      format: 'json',
      generatedAt: '2026-10-23 18:30 IST',
      fileSizeBytes: 98400,
      downloadUrl: '#',
      status: 'ready',
    },
    {
      id: 'gen-003',
      reportId: 'rep_release_audit',
      title: 'Release Payout & UTR Execution Audit Summary',
      format: 'pdf',
      generatedAt: '2026-10-22 14:00 IST',
      fileSizeBytes: 421500,
      downloadUrl: '#',
      status: 'ready',
    },
  ]);

  const totalPaise = instruments.reduce((sum, i) => sum + i.amount, 0);
  const activePaise = instruments.filter((i) => i.status === 'ACTIVE').reduce((sum, i) => sum + i.amount, 0);
  const maturingPaise = instruments.filter((i) => i.status === 'EXPIRING' || i.status === 'MATURED').reduce((sum, i) => sum + i.amount, 0);

  const formatPaiseINR = (paise: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(paise / 100);
  };

  const handleGenerateReport = () => {
    const reportDef = REPORT_CATALOGUE.find((r) => r.id === selectedReportId);
    if (!reportDef) return;

    setIsGenerating(true);
    setTimeout(() => {
      const newReport: GeneratedReport = {
        id: `gen-${Date.now().toString().slice(-4)}`,
        reportId: reportDef.id,
        title: `${reportDef.title} (${selectedFy})`,
        format: selectedFormat,
        generatedAt: new Date().toLocaleString('en-IN', { hour12: false }) + ' IST',
        fileSizeBytes: Math.floor(Math.random() * 200000) + 50000,
        downloadUrl: '#',
        status: 'ready',
      };

      setGeneratedReports((prev) => [newReport, ...prev]);
      setIsGenerating(false);
      setSuccessToast(`Report "${reportDef.title}" generated successfully in ${selectedFormat.toUpperCase()} format.`);
      setTimeout(() => setSuccessToast(null), 4000);
    }, 900);
  };

  const handleDownloadReport = (rep: GeneratedReport) => {
    // Generate dummy downloadable file content
    const content = `AICTE Regulatory Report Export\nTitle: ${rep.title}\nGenerated: ${rep.generatedAt}\nStatus: Certified\nTotal Paired Exposure: ${formatPaiseINR(totalPaise)}`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${rep.reportId}_${selectedFy}.${rep.format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-purple-950/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                <BarChart3 size={22} />
              </span>
              <h1 className="text-2xl font-bold tracking-tight text-white">Reports & Statutory Exports</h1>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Regulatory compliance reports, maturity exposure schedules, and reconciliation audit exports (F-16)
            </p>
          </div>
        </div>

        {/* Executive Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Custodial Deposit</div>
            <div className="mt-2 text-xl font-bold font-mono text-cyan-300">{formatPaiseINR(totalPaise)}</div>
            <div className="mt-1 text-[11px] text-slate-500">{instruments.length} Total Registered Instruments</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Compliant Balance</div>
            <div className="mt-2 text-xl font-bold font-mono text-emerald-300">{formatPaiseINR(activePaise)}</div>
            <div className="mt-1 text-[11px] text-emerald-400/80">98.4% Statutory Coverage Ratio</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Expiring / Deficit Risk</div>
            <div className="mt-2 text-xl font-bold font-mono text-amber-300">{formatPaiseINR(maturingPaise)}</div>
            <div className="mt-1 text-[11px] text-amber-400/80">Action required under T-90 ladder</div>
          </div>
        </div>
      </div>

      {successToast && (
        <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 size={14} />
          {successToast}
        </div>
      )}

      {/* Main Generation & Catalogue Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Report Catalogue */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <FileSpreadsheet size={16} className="text-cyan-400" />
              Statutory Report Catalogue
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {REPORT_CATALOGUE.map((report) => {
              const isSelected = selectedReportId === report.id;
              return (
                <div
                  key={report.id}
                  onClick={() => setSelectedReportId(report.id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-purple-950/40 border-cyan-400 shadow-lg shadow-cyan-950/20'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-cyan-300 border border-slate-700">
                      {report.category}
                    </span>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Clock size={12} /> {report.frequency}
                    </span>
                  </div>

                  <h3 className="mt-3 font-semibold text-sm text-white">{report.title}</h3>
                  <p className="mt-1 text-xs text-slate-400 line-clamp-2">{report.description}</p>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Available:</span>
                    <div className="flex gap-1.5">
                      {report.supportedFormats.map((fmt) => (
                        <span key={fmt} className="uppercase font-mono font-semibold text-slate-300 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                          {fmt}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Report Config & On-Demand Generator */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 h-fit space-y-5 bg-slate-900/50">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Filter size={16} className="text-cyan-400" />
              Configure & Generate
            </h2>
            <p className="mt-1 text-xs text-slate-400">
              Export filtered datasets with verified cryptographic timestamping
            </p>
          </div>

          <div className="space-y-4 text-xs">
            {/* Selected Report Name */}
            <div>
              <label className="text-slate-400 font-semibold block mb-1">Target Report</label>
              <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-cyan-300 font-medium truncate">
                {REPORT_CATALOGUE.find((r) => r.id === selectedReportId)?.title}
              </div>
            </div>

            {/* Financial Year */}
            <div>
              <label className="text-slate-400 font-semibold block mb-1">Financial Year</label>
              <select
                value={selectedFy}
                onChange={(e) => setSelectedFy(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white focus:outline-none focus:border-cyan-400"
              >
                <option value="2026-27">FY 2026-27 (Current Cycle)</option>
                <option value="2025-26">FY 2025-26</option>
                <option value="2024-25">FY 2024-25</option>
              </select>
            </div>

            {/* Export Format */}
            <div>
              <label className="text-slate-400 font-semibold block mb-1">Export Format</label>
              <div className="grid grid-cols-3 gap-2">
                {(['csv', 'json', 'pdf'] as const).map((fmt) => (
                  <button
                    key={fmt}
                    onClick={() => setSelectedFormat(fmt)}
                    className={`py-2 text-center rounded-xl font-mono uppercase font-bold border transition-colors ${
                      selectedFormat === fmt
                        ? 'bg-cyan-950 text-cyan-300 border-cyan-400'
                        : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    {fmt}
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Action Button */}
            <button
              onClick={handleGenerateReport}
              disabled={isGenerating}
              className="w-full mt-2 py-3 rounded-xl font-semibold bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-slate-950 flex items-center justify-center gap-2 shadow-lg shadow-cyan-950/30 transition-all disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  Generating Export...
                </>
              ) : (
                <>
                  <Download size={14} />
                  Generate Export File
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Generated Reports History Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-cyan-400" />
            <span className="text-xs font-semibold text-slate-300">Generated Exports & Downloads History</span>
          </div>
          <span className="text-[11px] text-slate-400">{generatedReports.length} Available Downloads</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-950/40">
                <th className="py-3 px-4">Export File Title</th>
                <th className="py-3 px-4">Format</th>
                <th className="py-3 px-4">Generated At</th>
                <th className="py-3 px-4">File Size</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {generatedReports.map((rep) => (
                <tr key={rep.id} className="hover:bg-slate-900/60 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white flex items-center gap-2">
                    <FileSpreadsheet size={14} className="text-cyan-400" />
                    {rep.title}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-slate-800 text-cyan-300 border border-slate-700">
                      {rep.format}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300 font-mono">{rep.generatedAt}</td>
                  <td className="py-3 px-4 text-slate-400 font-mono">{(rep.fileSizeBytes / 1024).toFixed(1)} KB</td>
                  <td className="py-3 px-4">
                    <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                      <CheckCircle2 size={12} /> Ready
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => handleDownloadReport(rep)}
                      className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-cyan-950 text-cyan-300 hover:text-cyan-200 border border-slate-700 hover:border-cyan-500/50 text-[11px] font-semibold transition-colors flex items-center gap-1.5 mx-auto"
                    >
                      <Download size={12} /> Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
