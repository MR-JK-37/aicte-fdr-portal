import React, { useState } from 'react';
import { BarChart3, Download, Filter, FileSpreadsheet, Clock, FileText, ShieldAlert } from 'lucide-react';
import { Instrument, ReportDefinition, GeneratedReport } from '../types';
import { formatPaiseINR } from '@aicte-fdr/shared';

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
  const [notice, setNotice] = useState<string | null>(null);

  // No fabricated export history — the async export_jobs API (GET /v1/export-jobs,
  // revalidated-on-download) does not exist yet (stream R4).
  const generatedReports: GeneratedReport[] = [];

  const totalPaise = instruments.reduce((sum, i) => sum + i.amount, 0);
  const activePaise = instruments.filter((i) => i.status === 'ACTIVE').reduce((sum, i) => sum + i.amount, 0);
  const maturingPaise = instruments.filter((i) => i.status === 'EXPIRING' || i.status === 'MATURED').reduce((sum, i) => sum + i.amount, 0);

  const handleGenerateReport = () => {
    setNotice(
      'Not yet connected to the API. Report generation needs stream R4’s async export_jobs ' +
        'pipeline (scope/reason/row-count/file-hash tracked, permission revalidated at download) — ' +
        'nothing is generated or downloadable yet.'
    );
    setTimeout(() => setNotice(null), 5000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '24px', padding: '28px', boxShadow: 'var(--shadow-card)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: 40, height: 40, borderRadius: '12px', background: 'var(--primary-container)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <BarChart3 size={20} color="var(--azure)" />
              </div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '22px', fontWeight: 800, color: 'var(--text1)' }}>Reports & Statutory Exports</h1>
            </div>
            <p style={{ marginTop: '4px', fontSize: '13px', color: 'var(--text3)' }}>
              Regulatory compliance reports, maturity exposure schedules, and reconciliation audit exports (F-16)
            </p>
          </div>
        </div>

        {/* Executive Metric Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginTop: '24px' }}>
          <div style={{ padding: '18px 20px', borderRadius: '16px', background: 'var(--field)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Total Custodial Deposit</div>
            <div style={{ marginTop: '6px', fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--text1)' }}>{formatPaiseINR(totalPaise)}</div>
            <div style={{ marginTop: '4px', fontSize: '11px', color: 'var(--text3)' }}>{instruments.length} Total Registered Instruments</div>
          </div>

          <div style={{ padding: '18px 20px', borderRadius: '16px', background: 'var(--field)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Active Compliant Balance</div>
            <div style={{ marginTop: '6px', fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#059669' }}>{formatPaiseINR(activePaise)}</div>
            <div style={{ marginTop: '4px', fontSize: '11px', color: '#059669' }}>Verified active status</div>
          </div>

          <div style={{ padding: '18px 20px', borderRadius: '16px', background: 'var(--field)', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Expiring / Deficit Risk</div>
            <div style={{ marginTop: '6px', fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#D97706' }}>{formatPaiseINR(maturingPaise)}</div>
            <div style={{ marginTop: '4px', fontSize: '11px', color: '#D97706' }}>Action required under T-90 ladder</div>
          </div>
        </div>
      </div>

      {notice && (
        <div style={{ padding: '14px 18px', borderRadius: '14px', background: '#FEF3C7', border: '1px solid #FCD34D', color: '#92400E', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={16} color="#B45309" />
          {notice}
        </div>
      )}

      {/* Main Generation & Catalogue Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {/* Left 2 Cols: Report Catalogue */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '14px', fontWeight: 700, color: 'var(--text1)', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileSpreadsheet size={16} color="var(--azure)" />
              Statutory Report Catalogue
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            {REPORT_CATALOGUE.map((report) => {
              const isSelected = selectedReportId === report.id;
              return (
                <div
                  key={report.id}
                  onClick={() => setSelectedReportId(report.id)}
                  style={{
                    padding: '18px',
                    borderRadius: '18px',
                    border: isSelected ? '2px solid var(--azure)' : '1px solid var(--border)',
                    background: isSelected ? 'var(--primary-container)' : 'var(--surface)',
                    boxShadow: isSelected ? '0 4px 16px rgba(59, 130, 246, 0.12)' : 'var(--shadow-card)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ padding: '3px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', background: isSelected ? '#FFFFFF' : 'var(--field)', color: 'var(--azure)' }}>
                      {report.category}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text3)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} /> {report.frequency}
                    </span>
                  </div>

                  <h3 style={{ marginTop: '12px', fontWeight: 700, fontSize: '14px', color: 'var(--text1)' }}>{report.title}</h3>
                  <p style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text3)', lineHeight: 1.4 }}>{report.description}</p>

                  <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
                    <span style={{ color: 'var(--text3)' }}>Available:</span>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {report.supportedFormats.map((fmt) => (
                        <span key={fmt} style={{ textTransform: 'uppercase', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text2)', background: 'var(--surface)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '10px' }}>
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
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '20px', padding: '24px', boxShadow: 'var(--shadow-card)', height: 'fit-content', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '14px', fontWeight: 700, color: 'var(--text1)', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Filter size={16} color="var(--azure)" />
              Configure & Generate
            </h2>
            <p style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text3)' }}>
              Export filtered datasets with verified cryptographic timestamping
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '12px' }}>
            {/* Selected Report Name */}
            <div>
              <label style={{ color: 'var(--text2)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Target Report</label>
              <div style={{ padding: '10px 12px', borderRadius: '12px', background: 'var(--field)', border: '1px solid var(--border)', color: 'var(--text1)', fontWeight: 600 }}>
                {REPORT_CATALOGUE.find((r) => r.id === selectedReportId)?.title}
              </div>
            </div>

            {/* Financial Year */}
            <div>
              <label style={{ color: 'var(--text2)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Financial Year</label>
              <select
                value={selectedFy}
                onChange={(e) => setSelectedFy(e.target.value)}
                style={{ width: '100%', padding: '10px 12px', borderRadius: '12px', background: 'var(--field)', border: '1px solid var(--border)', color: 'var(--text1)', fontSize: '12px' }}
              >
                <option value="2026-27">FY 2026-27 (Current Cycle)</option>
                <option value="2025-26">FY 2025-26</option>
                <option value="2024-25">FY 2024-25</option>
              </select>
            </div>

            {/* Export Format */}
            <div>
              <label style={{ color: 'var(--text2)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Export Format</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                {(['csv', 'json', 'pdf'] as const).map((fmt) => (
                  <button
                    key={fmt}
                    onClick={() => setSelectedFormat(fmt)}
                    style={{
                      padding: '8px',
                      textAlign: 'center',
                      borderRadius: '10px',
                      fontFamily: 'var(--font-mono)',
                      textTransform: 'uppercase',
                      fontWeight: 700,
                      cursor: 'pointer',
                      border: selectedFormat === fmt ? '1px solid var(--azure)' : '1px solid var(--border)',
                      background: selectedFormat === fmt ? 'var(--primary-container)' : 'var(--field)',
                      color: selectedFormat === fmt ? 'var(--azure)' : 'var(--text3)',
                    }}
                  >
                    {fmt}
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Action Button */}
            <button
              onClick={handleGenerateReport}
              style={{
                width: '100%',
                marginTop: '8px',
                padding: '12px',
                borderRadius: '9999px',
                fontWeight: 700,
                background: 'var(--ink)',
                color: '#FFFFFF',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 14px rgba(17, 24, 39, 0.2)',
                fontSize: '13px',
              }}
            >
              <Download size={15} />
              Generate Export File
            </button>
          </div>
        </div>
      </div>

      {/* Generated Reports History Table */}
      <div style={{ background: 'var(--surface)', borderRadius: '20px', border: '1px solid var(--border)', overflow: 'hidden', boxShadow: 'var(--shadow-card)' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={16} color="var(--azure)" />
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text1)' }}>Generated Exports & Downloads History</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text3)' }}>{generatedReports.length} Available Downloads</span>
        </div>

        <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text3)', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <FileText size={16} />
          Nothing here yet — exports will appear once stream R4's async export_jobs API exists and
          this screen is wired to it (stream R3).
        </div>
      </div>
    </div>
  );
};
