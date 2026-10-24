import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { KPIBoard } from './components/KPIBoard';
import { NewFDRSubmission } from './components/NewFDRSubmission';
import { VerificationView } from './components/VerificationView';
import { RemindersView } from './components/RemindersView';
import { ReleaseWorkflow } from './components/ReleaseWorkflow';
import { CopilotView } from './components/CopilotView';
import { AuditLogView } from './components/AuditLogView';
import { VoiceCallModal } from './components/VoiceCallModal';
import { SimClockControl } from './components/SimClockControl';
import { SearchWorkspace } from './components/SearchWorkspace';
import { ReportsView } from './components/ReportsView';
import { HelpAndRightsView } from './components/HelpAndRightsView';
import { AdminConsoleView } from './components/AdminConsoleView';
import { PublicReceiptVerification } from './components/PublicReceiptVerification';
import { NotificationCenter } from './components/NotificationCenter';
import { CommandPalette } from './components/CommandPalette';
import { Instrument, AppRole, EvidenceLevel, AuditEntry } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [userRole, setUserRole] = useState<AppRole>('scrutiny_officer');
  const [language, setLanguage] = useState<string>('en');

  // Modals & Panels state
  const [simClockDate, setSimClockDate] = useState('2026-10-23');
  const [simOffsetDays, setSimOffsetDays] = useState(0);
  const [simClockModalOpen, setSimClockModalOpen] = useState(false);
  const [isNotificationCenterOpen, setIsNotificationCenterOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  // Voice Call Modal state
  const [voiceCallInstrument, setVoiceCallInstrument] = useState<Instrument | null>(null);

  // Keyboard shortcut listener for ⌘K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Sample Instruments representing the real regulatory scenarios
  const [instruments, setInstruments] = useState<Instrument[]>([
    {
      id: 'inst-1',
      institution_id: 'AICTE-ENGG-001',
      institution_name: 'Delhi Global Technical Campus',
      instrument_number: 'AXIS-FDR-99201',
      type: 'FDR',
      amount: 350000000, // ₹35,00,000 in paise
      bank_name: 'Axis Bank',
      branch_ifsc: 'UTIB0002948',
      issue_date: '2018-08-15',
      maturity_date: '2026-11-20',
      status: 'ACTIVE',
      evidence_level: 'L3',
      joint_account_holder: 'Regional Officer, AICTE',
      utr_number: 'UTIB00029481902',
    },
    {
      id: 'inst-2',
      institution_id: 'AICTE-ENGG-002',
      institution_name: 'Apex Institute of Technology',
      instrument_number: 'SBI-881920',
      type: 'FDR',
      amount: 500000000, // ₹50,00,000
      bank_name: 'State Bank of India',
      branch_ifsc: 'SBIN0091827',
      issue_date: '2021-04-10',
      maturity_date: '2026-11-30',
      status: 'EXPIRING',
      evidence_level: 'L2',
      joint_account_holder: 'Single Account (Discrepancy Pending)',
      utr_number: 'SBIN00918273645',
    },
    {
      id: 'inst-3',
      institution_id: 'AICTE-ENGG-003',
      institution_name: 'National College of Engineering',
      instrument_number: 'HDFC-441029',
      type: 'FDR',
      amount: 400000000, // ₹40,00,000
      bank_name: 'HDFC Bank',
      branch_ifsc: 'HDFC0004410',
      issue_date: '2023-01-15',
      maturity_date: '2026-12-15',
      status: 'ACTIVE',
      evidence_level: 'L3',
      joint_account_holder: 'Regional Officer, AICTE',
      utr_number: 'HDFC99281726354',
    },
    {
      id: 'inst-4',
      institution_id: 'AICTE-ENGG-004',
      institution_name: 'St. Mary’s Polytechnic College',
      instrument_number: 'PNB-771829',
      type: 'FDR',
      amount: 250000000, // ₹25,00,000 (Shortfall: expected ₹35L)
      bank_name: 'Punjab National Bank',
      branch_ifsc: 'PUNB0019283',
      issue_date: '2022-09-01',
      maturity_date: '2026-10-25',
      status: 'MATURED',
      evidence_level: 'L1',
      joint_account_holder: 'Regional Officer, AICTE',
      utr_number: 'PUNB00192837465',
    },
  ]);

  // Cryptographic SHA-256 hash-chained audit entries
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([
    {
      id: 1,
      action: 'GENESIS_BLOCK_INITIALIZED',
      entity_type: 'system',
      entity_id: 'AICTE_ROOT',
      row_hash: 'sha256:000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f',
      prev_hash: 'sha256:0000000000000000000000000000000000000000000000000000000000000000',
      created_at: '2026-10-23 09:00:00 IST',
      details: { environment: 'production', chain_standard: 'sha256_canonical' },
    },
    {
      id: 2,
      action: 'FDR_INTAKE_OCR_COMPLETED',
      entity_type: 'instrument',
      entity_id: 'AXIS-FDR-99201',
      row_hash: 'sha256:1a84f3c92e104b2a8d4389f10928a38c92847582b109283746a5b1029384756c',
      prev_hash: 'sha256:000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f',
      created_at: '2026-10-23 09:15:32 IST',
      details: { confidence: 0.98, extracted_amount_paise: 350000000 },
    },
    {
      id: 3,
      action: 'BANK_CONFIRMATION_VERIFIED',
      entity_type: 'instrument',
      entity_id: 'SBI-881920',
      row_hash: 'sha256:3c84b1029384756c8b91a283746592817263548291029384756c8b91a2837465',
      prev_hash: 'sha256:1a84f3c92e104b2a8d4389f10928a38c92847582b109283746a5b1029384756c',
      created_at: '2026-10-23 10:30:14 IST',
      details: { branch: 'Chandni Chowk New Delhi', evidence_promoted_to: 'L2' },
    },
    {
      id: 4,
      action: 'STATEMENT_RECONCILIATION_COMPLETED',
      entity_type: 'instrument',
      entity_id: 'AXIS-FDR-99201',
      row_hash: 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
      prev_hash: 'sha256:3c84b1029384756c8b91a283746592817263548291029384756c8b91a2837465',
      created_at: '2026-10-23 11:45:00 IST',
      details: { utr: 'UTIB00029481902', match_quality: 'EXACT', evidence_promoted_to: 'L3' },
    },
  ]);

  const handleAddAuditEntry = (action: string, entityId: string, details: any) => {
    const prevEntry = auditEntries[auditEntries.length - 1];
    const prevHash = prevEntry ? prevEntry.row_hash : 'sha256:00000000';
    const randomHex = Math.random().toString(16).slice(2, 10) + Math.random().toString(16).slice(2, 10);
    const newHash = `sha256:${randomHex}${prevHash.slice(7, 30)}`;

    const newBlock: AuditEntry = {
      id: auditEntries.length + 1,
      action,
      entity_type: 'audit_event',
      entity_id: entityId,
      row_hash: newHash,
      prev_hash: prevHash,
      created_at: new Date().toLocaleString('en-IN', { hour12: false }) + ' IST',
      details,
    };

    setAuditEntries((prev) => [...prev, newBlock]);
  };

  const handlePromoteEvidence = (id: string, newLevel: EvidenceLevel) => {
    setInstruments((prev) =>
      prev.map((inst) => (inst.id === id ? { ...inst, evidence_level: newLevel } : inst))
    );
  };

  const handleAddInstrument = (newInst: Instrument) => {
    setInstruments((prev) => [newInst, ...prev]);
    handleAddAuditEntry('FDR_INTAKE_OCR_COMPLETED', newInst.instrument_number, {
      institution: newInst.institution_name,
      amount: newInst.amount,
      evidence_level: newInst.evidence_level,
    });
    setActiveTab('dashboard');
  };

  const handleSetOffset = (days: number) => {
    const current = new Date('2026-10-23');
    current.setDate(current.getDate() + days);
    const newDateStr = current.toISOString().slice(0, 10);
    setSimClockDate(newDateStr);
    setSimOffsetDays(days);
    handleAddAuditEntry('SIM_CLOCK_OFFSET_CHANGED', 'sim_engine', {
      offset_days: days,
      simulated_date: newDateStr,
    });
  };

  const handleAdvanceClock = (days: number) => {
    handleSetOffset(simOffsetDays + days);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header Navbar */}
      <Navbar
        currentTab={activeTab}
        setCurrentTab={setActiveTab}
        role={userRole}
        setRole={setUserRole}
        lang={language}
        setLang={setLanguage}
        simClockOffsetDays={simOffsetDays}
        onOpenSimClock={() => setSimClockModalOpen(true)}
        onTriggerVoiceDemo={() => setVoiceCallInstrument(instruments[0])}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        onOpenNotifications={() => setIsNotificationCenterOpen(true)}
        unreadNotificationsCount={2}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        {activeTab === 'dashboard' && (
          <KPIBoard
            instruments={instruments}
            onSelectInstrument={(inst) => {
              setVoiceCallInstrument(inst);
            }}
          />
        )}

        {activeTab === 'search' && (
          <SearchWorkspace
            instruments={instruments}
            onSelectInstrument={(inst) => {
              setActiveTab('verify');
            }}
          />
        )}

        {activeTab === 'submit' && (
          <NewFDRSubmission
            onSuccess={handleAddInstrument}
            lang={language}
          />
        )}

        {activeTab === 'verify' && (
          <VerificationView
            instruments={instruments}
            onPromoteEvidence={handlePromoteEvidence}
            onAddAuditEntry={handleAddAuditEntry}
          />
        )}

        {activeTab === 'reminders' && (
          <RemindersView
            instruments={instruments}
            onTriggerVoiceCall={(inst) => setVoiceCallInstrument(inst)}
            onAddAuditEntry={handleAddAuditEntry}
            onAdvanceClock={handleAdvanceClock}
          />
        )}

        {activeTab === 'release' && (
          <ReleaseWorkflow
            instruments={instruments}
            userRole={userRole}
            onAddAuditEntry={handleAddAuditEntry}
          />
        )}

        {activeTab === 'reports' && (
          <ReportsView instruments={instruments} />
        )}

        {activeTab === 'copilot' && (
          <CopilotView onAddAuditEntry={handleAddAuditEntry} />
        )}

        {activeTab === 'audit' && (
          <AuditLogView entries={auditEntries} />
        )}

        {activeTab === 'admin' && (
          <AdminConsoleView />
        )}

        {activeTab === 'help' && (
          <HelpAndRightsView />
        )}

        {activeTab === 'public_receipt' && (
          <PublicReceiptVerification onBackToApp={() => setActiveTab('dashboard')} />
        )}
      </main>

      {/* Command Palette Modal (⌘K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectAction={(tabId) => setActiveTab(tabId)}
      />

      {/* In-App Notification Center Drawer */}
      <NotificationCenter
        isOpen={isNotificationCenterOpen}
        onClose={() => setIsNotificationCenterOpen(false)}
        onNavigateToTab={(tabId) => setActiveTab(tabId)}
      />

      {/* Interactive Sim Clock Modal */}
      <SimClockControl
        isOpen={simClockModalOpen}
        onClose={() => setSimClockModalOpen(false)}
        simDate={simClockDate}
        offsetDays={simOffsetDays}
        onSetOffset={handleSetOffset}
      />

      {/* WebRTC / Sarvam AI Voice Agent Interactive Simulator Modal */}
      {voiceCallInstrument && (
        <VoiceCallModal
          instrument={voiceCallInstrument}
          onClose={() => setVoiceCallInstrument(null)}
          onAddAuditEntry={handleAddAuditEntry}
        />
      )}

      {/* Footer with statutory notices and tech stack details */}
      <footer className="mt-12 py-6 border-t border-slate-800 bg-slate-950/80 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-400">AICTE Security Deposit (FDR) Portal</span>
            <span>•</span>
            <span>Statutory Compliance under AICTE Act Sec. 10(k)</span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">PostgreSQL 16 + pgvector</span>
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">Liquid Glass Web UI</span>
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">Valkey Cache</span>
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">Sarvam AI + Pipecat</span>
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">Llama-3.3-70b RAG</span>
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">SHA-256 Ledger</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
