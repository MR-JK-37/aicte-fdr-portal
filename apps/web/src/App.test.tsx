import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { App } from './App';

describe('AICTE Security Deposit Portal - 6 Scenarios Acceptance Tests', () => {
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

    expect(screen.getByText(/AICTE Autonomous Voice Bot/i)).toBeDefined();
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
});
