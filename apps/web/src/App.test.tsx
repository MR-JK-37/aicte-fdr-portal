import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { App } from './App';
import { AuthProvider } from './auth/AuthContext';
import { StepUpProvider } from './auth/StepUpContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Unit-test fetch mock — NOT an e2e test (no real backend/DB here, this is a
// jsdom component test). Only /v1/me and /v1/me/navigation are stubbed, with
// a fixed signed-in scrutiny_officer, so the app shell can be exercised
// without a running API; every screen under test still gets zero fabricated
// business data — see each component's own "not yet connected" states.
const MOCK_USER = {
  id: 'test-user-1',
  email: 'officer@example.com',
  full_name: 'Test Officer',
  role: 'scrutiny_officer',
  institution_id: null,
  region_id: null,
  mfa_enrolled: false,
  step_up_valid: false,
  step_up_valid_until: null,
  delegation_limit: null,
};

const MOCK_NAVIGATION = {
  landing_route: '/my-queue',
  web_sidebar: [],
  mobile_tabs: [],
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') return input;
  if (input instanceof Request) return input.url;
  return input.toString();
}

function mockFetch(input: RequestInfo | URL): Promise<Response> {
  const url = requestUrl(input);
  const path = new URL(url, 'http://localhost').pathname;
  if (path === '/v1/me/navigation') return Promise.resolve(jsonResponse(MOCK_NAVIGATION));
  if (path === '/v1/me/profile-completion') {
    return Promise.resolve(
      jsonResponse({
        percent: 40,
        items: [
          { key: 'name', label_key: 'profile.name', complete: true, optional: false },
          { key: 'mfa_enrolled', label_key: 'profile.mfa_enrolled', complete: false, optional: false },
        ],
      })
    );
  }
  if (path === '/v1/auth/sessions') return Promise.resolve(jsonResponse([]));
  if (path === '/v1/me') return Promise.resolve(jsonResponse(MOCK_USER));
  if (path === '/v1/instruments') return Promise.resolve(jsonResponse([]));
  return Promise.resolve(jsonResponse({ detail: 'not mocked in this test' }, 404));
}

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

function renderAuthed() {
  const result = render(
    <QueryClientProvider client={createTestQueryClient()}>
      <AuthProvider>
        <StepUpProvider>
          <App />
        </StepUpProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
  return result;
}

describe('AICTE Security Deposit Portal — honest-state web shell', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => mockFetch(input)));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows the login screen when signed out', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(jsonResponse({ detail: 'Authentication credential missing' }, 401)))
    );
    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <AuthProvider>
          <StepUpProvider>
            <App />
          </StepUpProvider>
        </AuthProvider>
      </QueryClientProvider>
    );
    expect(await screen.findByText(/Sign in/i)).toBeDefined();
    expect(screen.getByLabelText(/E-mail/i)).toBeDefined();
  });

  it('renders the KPI dashboard with zero fabricated instruments once signed in', async () => {
    renderAuthed();
    expect(await screen.findByText(/AICTE FDR Portal/i)).toBeDefined();
    expect(screen.queryByText(/AXIS-FDR-99201/i)).toBeNull();
    expect(screen.queryByText(/SBI-881920/i)).toBeNull();
  });

  it('shows the real signed-in role, not a client-side role switcher', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    expect(screen.getAllByText(/scrutiny officer/i).length).toBeGreaterThan(0);
    // The role <select> is gone (scripts/forbidden-strings.mjs also checks this at
    // the source level) — only the language selector combobox remains.
    expect(screen.getAllByRole('combobox').length).toBe(1);
  });

  it('never renders removed simulation/voice features', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    expect(screen.queryByText(/AI Voice Call/i)).toBeNull();
    expect(screen.queryByText(/Clock Live/i)).toBeNull();
    expect(screen.queryByText(/SIMULATION/i)).toBeNull();
    expect(screen.queryByText(/Simulate Statement Ingestion/i)).toBeNull();
    expect(screen.queryByText(/Simulate Tamper/i)).toBeNull();
    expect(screen.queryByText(/Demo FDR/i)).toBeNull();
    expect(screen.queryByText(/Text-to-SQL/i)).toBeNull();
    expect(screen.queryByText(/Eligible for Release/i)).toBeNull();
    expect(screen.queryByText(/Chain Integrity: 100%/i)).toBeNull();
  });

  it('navigates to Submit FDR and shows the honest not-yet-wired upload state', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /^Submit FDR$/i }));
    expect(screen.getByText(/New FDR Submission/i)).toBeDefined();
    expect(screen.getByText(/Choose file/i)).toBeDefined();
  });

  it('navigates to Bank Verification and shows pending-source-response states', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /^Bank Verification$/i }));
    expect(screen.getByText(/Verification & Statement Reconciliation/i)).toBeDefined();
    expect(screen.getAllByText(/Not yet connected to the API/i).length).toBeGreaterThan(0);
  });

  it('navigates to Reminder Ladder and shows the no-approved-schedule banner', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /Reminder Ladder/i }));
    expect(screen.getByText(/Maturity Ladder & Reminders Inbox/i)).toBeDefined();
    expect(screen.getByText(/No approved reminder schedule/i)).toBeDefined();
  });

  it('navigates to Release Authorization with no automatic eligibility claim', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /Release Authorization/i }));
    expect(screen.getByText(/Security Deposit Release/i)).toBeDefined();
    expect(screen.queryByText(/Eligible for Release/i)).toBeNull();
  });

  it('navigates to AI Copilot with Text-to-SQL removed', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /^AI Copilot$/i }));
    expect(screen.getByText(/AICTE Regulatory Copilot/i)).toBeDefined();
    expect(screen.queryByText(/Text-to-SQL/i)).toBeNull();
  });

  it('navigates to Audit Chain with no fabricated hash chain', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /Audit Chain/i }));
    expect(screen.getByText(/Cryptographic Audit Ledger/i)).toBeDefined();
    expect(screen.queryByText(/Block #1/i)).toBeNull();
    expect(screen.queryByText(/Chain Integrity:/i)).toBeNull();
  });

  it('navigates to Search & Views and computes preset counts from real (empty) data', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /Search & Views/i }));
    expect(screen.getByText(/Expiring in ≤ 30 Days/i)).toBeDefined();
  });

  it('navigates to Reports & Exports with no fabricated export history', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /Reports & Exports/i }));
    expect(screen.getByText(/Reports & Statutory Exports/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /Generate Export File/i })).toBeDefined();
  });

  it('navigates to Admin & Connectors with no fabricated HEALTHY statuses', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /Admin & Connectors/i }));
    expect(screen.getByText(/System Admin & Connector Registry/i)).toBeDefined();
    expect(screen.queryByText(/healthy/i)).toBeNull();
  });

  it('navigates to Security and shows real profile/session data, not a fake percentage', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByRole('button', { name: /^Security$/i }));
    await waitFor(() => expect(screen.getByText(/officer@example.com/i)).toBeDefined());
  });

  it('opens the notification center with an empty, honest inbox', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByTitle(/Notifications/i));
    expect(screen.getByText(/In-App Inbox \(0\)/i)).toBeDefined();
  });

  it('opens the public receipt verification page with no fabricated seal', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByTitle(/Public Verification Gateway/i));
    expect(screen.getByText(/Public Receipt Verification Service/i)).toBeDefined();
    expect(screen.queryByText(/GENUINE AICTE CRYPTOGRAPHIC RECEIPT SEAL/i)).toBeNull();
  });

  it('opens the command palette modal (⌘K)', async () => {
    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);
    fireEvent.click(screen.getByTitle(/Press ⌘K or Ctrl\+K/i));
    expect(screen.getByPlaceholderText(/Type a command or screen name/i)).toBeDefined();
  });

  it('hits /v1/* endpoints on render and displays the realtime SSE status indicator (R3.4 / Exit Gate R3)', async () => {
    const requestedUrls: string[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = requestUrl(input);
        requestedUrls.push(new URL(url, 'http://localhost').pathname);
        return mockFetch(input);
      })
    );

    renderAuthed();
    await screen.findByText(/AICTE FDR Portal/i);

    // Verify /v1/* contract endpoints were called
    await waitFor(() => {
      expect(requestedUrls).toContain('/v1/me');
      expect(requestedUrls).toContain('/v1/me/navigation');
      expect(requestedUrls).toContain('/v1/instruments');
    });

    // Verify realtime SSE status indicator is rendered in the Navbar
    expect(screen.getByTestId('sse-status-indicator')).toBeDefined();
  });
});
