import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { App } from './App';

describe('AICTE Security Deposit Portal - Acceptance Tests & Phase 6 Web Screens', () => {
  it('Scenario 2: Renders KPI Dashboard and Active Instrument Register', () => {
    render(<App />);
    expect(screen.getByText(/AICTE FDR Portal/i)).toBeDefined();
    expect(screen.getByText(/Active Security Deposit Register/i)).toBeDefined();
    expect(screen.getByText(/AXIS-FDR-99201/i)).toBeDefined();
    expect(screen.getByText(/Apex Institute of Technology/i)).toBeDefined();
  });

  it('Scenario 1: Navigates to Submit FDR (L1 Intake & OCR)', () => {
    render(<App />);
    const submitTab = screen.getByRole('button', { name: /Submit FDR \(L1\)/i });
    fireEvent.click(submitTab);

    expect(screen.getByText(/New FDR Submission & OCR Intelligence/i)).toBeDefined();
    expect(screen.getByText(/Drag and drop FDR PDF or Scanned Image/i)).toBeDefined();
  });

  it('Scenario 3: Navigates to Bank Verification & Statement Reconciliation (L2/L3)', () => {
    render(<App />);
    const verifyTab = screen.getByRole('button', { name: /Bank Verification \(L2\/L3\)/i });
    fireEvent.click(verifyTab);

    expect(screen.getByText(/Verification & Statement Reconciliation/i)).toBeDefined();
    expect(screen.getByText(/Upload AICTE Statement CSV/i)).toBeDefined();
    expect(screen.getByText(/Live Bank Statement Matching Queue/i)).toBeDefined();
  });

  it('Scenario 4: Navigates to Reminder Ladder & Maturity Timeline', () => {
    render(<App />);
    const remindersTab = screen.getByRole('button', { name: /Reminder Ladder/i });
    fireEvent.click(remindersTab);

    expect(screen.getByText(/Maturity Ladder & Reminders Inbox/i)).toBeDefined();
    expect(screen.getByText(/Statutory Escalation Ladder/i)).toBeDefined();
    expect(screen.getByText(/T - 90 Days/i)).toBeDefined();
    expect(screen.getByText(/T - 30 Days/i)).toBeDefined();
  });

  it('Scenario 5: Opens Voice Assistant Modal and checks WebRTC call initialization', () => {
    render(<App />);
    const voiceBtn = screen.getByRole('button', { name: /AI Voice Call/i });
    fireEvent.click(voiceBtn);

    expect(screen.getByText(/AICTE Autonomous Voice Assistant/i)).toBeDefined();
    expect(screen.getByText(/Sarvam AI \(WebRTC\)/i)).toBeDefined();
    expect(screen.getByText(/Establishing WebRTC Audio Link/i)).toBeDefined();
  });

  it('Scenario 6: Navigates to Release Authorization and Dual Maker-Checker Workflow', () => {
    render(<App />);
    const releaseTab = screen.getByRole('button', { name: /Release Authorization/i });
    fireEvent.click(releaseTab);

    expect(screen.getByText(/Security Deposit Release & Dual Maker-Checker Workflow/i)).toBeDefined();
    expect(screen.getByText(/Automated Statutory Eligibility Checklist/i)).toBeDefined();
    expect(screen.getByText(/Step 1 • Maker/i)).toBeDefined();
    expect(screen.getByText(/Step 2 • Checker/i)).toBeDefined();
    expect(screen.getByText(/Step 3 • Sign-Off/i)).toBeDefined();
  });

  it('Scenario 7: Navigates to AI Copilot & Natural Language Text-to-SQL Analytics', () => {
    render(<App />);
    const copilotTab = screen.getByRole('button', { name: /AI Copilot & SQL/i });
    fireEvent.click(copilotTab);

    expect(screen.getByText(/AICTE Regulatory Copilot & Text-to-SQL Analytics/i)).toBeDefined();
    expect(screen.getByText(/Ask Approval Process Handbook \(APH\) Assistant/i)).toBeDefined();
  });

  it('Audit Chain: Displays SHA-256 Ledger and Tamper Detection Button', () => {
    render(<App />);
    const auditTab = screen.getByRole('button', { name: /Audit Chain/i });
    fireEvent.click(auditTab);

    expect(screen.getByText(/Cryptographic Audit Ledger & Tamper Detection/i)).toBeDefined();
    expect(screen.getByText(/Block #1/i)).toBeDefined();
    expect(screen.getByText(/Chain Integrity:/i)).toBeDefined();
  });

  it('Phase 6 (F-17): Navigates to Universal Search & Saved Views', () => {
    render(<App />);
    const searchTab = screen.getByRole('button', { name: /Search & Views/i });
    fireEvent.click(searchTab);

    expect(screen.getByText(/Universal Search & Saved Views/i)).toBeDefined();
    expect(screen.getByPlaceholderText(/Search by FDR Number, Institution Name/i)).toBeDefined();
    expect(screen.getByText(/Expiring in ≤ 30 Days/i)).toBeDefined();
    expect(screen.getByText(/Export Result/i)).toBeDefined();
  });

  it('Phase 6 (F-16): Navigates to Reports & Statutory Exports', () => {
    render(<App />);
    const reportsTab = screen.getByRole('button', { name: /Reports & Exports/i });
    fireEvent.click(reportsTab);

    expect(screen.getByText(/Reports & Statutory Exports/i)).toBeDefined();
    expect(screen.getByText(/Statutory Report Catalogue/i)).toBeDefined();
    expect(screen.getAllByText(/Monthly Security Deposit Position \(Table 1.4\)/i).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /Generate Export File/i })).toBeDefined();
  });

  it('Phase 6 (F-19): Navigates to Admin Console & Connector Registry', () => {
    render(<App />);
    const adminTab = screen.getByRole('button', { name: /Admin & Connectors/i });
    fireEvent.click(adminTab);

    expect(screen.getByText(/System Admin & Connector Registry/i)).toBeDefined();
    expect(screen.getByText(/Scheduled Commercial Banks Direct API Gateway/i)).toBeDefined();
    expect(screen.getByText(/Dead-Letter Queue \(DLQ\) Inspector & Manual Replay/i)).toBeDefined();
  });

  it('Phase 6 (F-21, F-22): Navigates to Help & DPDP Rights', () => {
    render(<App />);
    const helpTab = screen.getByRole('button', { name: /Help & DPDP/i });
    fireEvent.click(helpTab);

    expect(screen.getByText(/Help, Support & DPDP Rights/i)).toBeDefined();
    expect(screen.getByText(/What are the statutory security deposit requirements under APH Table 1.4\?/i)).toBeDefined();
  });

  it('Phase 6 (F-20): Navigates to Public Receipt Verification Portal', () => {
    render(<App />);
    const publicVerifyBtn = screen.getByTitle(/Public Verification Gateway/i);
    fireEvent.click(publicVerifyBtn);

    expect(screen.getByText(/Public Receipt Verification Service \(F-20\)/i)).toBeDefined();
    expect(screen.getByText(/Rate-Limited Statutory Verification Gateway/i)).toBeDefined();
    expect(screen.getByText(/GENUINE AICTE CRYPTOGRAPHIC RECEIPT SEAL/i)).toBeDefined();
  });

  it('Phase 6 (F-14, F-15): Opens Notification Center Drawer & Delivery Preferences', () => {
    render(<App />);
    const notifBtn = screen.getByTitle(/Notifications/i);
    fireEvent.click(notifBtn);

    expect(screen.getByText(/Notification Center/i)).toBeDefined();
    expect(screen.getByText(/In-App Inbox & Realtime Push \(SPEC §10\)/i)).toBeDefined();
    expect(screen.getByText(/T-30 Statutory Renewal Reminder Issued/i)).toBeDefined();
    expect(screen.getByText(/Delivery Preferences/i)).toBeDefined();
  });

  it('Phase 6: Opens Command Palette Modal (⌘K)', () => {
    render(<App />);
    const cmdPaletteBtn = screen.getByTitle(/Press ⌘K or Ctrl\+K/i);
    fireEvent.click(cmdPaletteBtn);

    expect(screen.getByPlaceholderText(/Type a command or screen name/i)).toBeDefined();
    expect(screen.getByText(/⌘K Command Palette/i)).toBeDefined();
    expect(screen.getByText(/Go to KPI Dashboard & Register/i)).toBeDefined();
  });
});
