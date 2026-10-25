import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Navbar } from './components/Navbar';
import { Sidebar } from './design-system/Sidebar';
import { FloatingTabBar } from './design-system/FloatingTabBar';
import { KPIBoard } from './components/KPIBoard';
import { NewFDRSubmission } from './components/NewFDRSubmission';
import { VerificationView } from './components/VerificationView';
import { RemindersView } from './components/RemindersView';
import { ReleaseWorkflow } from './components/ReleaseWorkflow';
import { CopilotView } from './components/CopilotView';
import { AuditLogView } from './components/AuditLogView';
import { SearchWorkspace } from './components/SearchWorkspace';
import { ReportsView } from './components/ReportsView';
import { HelpAndRightsView } from './components/HelpAndRightsView';
import { AdminConsoleView } from './components/AdminConsoleView';
import { PublicReceiptVerification } from './components/PublicReceiptVerification';
import { NotificationCenter } from './components/NotificationCenter';
import { CommandPalette } from './components/CommandPalette';
import { SecurityView } from './components/SecurityView';
import { AskHandbookModal } from './components/AskHandbookModal';
import { LoginScreen } from './auth/LoginScreen';
import { useAuth } from './auth/AuthContext';
import { useInstruments } from './hooks/useInstruments';
import { useRealtimeStream } from './lib/sseClient';
import { apiFetch, ProblemError } from './lib/apiFetch';
import { AppRole } from './types';
import { IconName } from './design-system/Icon';

const PRIMARY_NAV_ITEMS: { key: string; label: string; icon: IconName }[] = [
  { key: 'dashboard', label: 'KPI Dashboard', icon: 'dashboard' },
  { key: 'search', label: 'Search & Views', icon: 'search' },
  { key: 'submit', label: 'Submit FDR', icon: 'upload' },
  { key: 'verify', label: 'Bank Verification', icon: 'verified' },
  { key: 'reminders', label: 'Reminder Ladder', icon: 'deadline' },
  { key: 'release', label: 'Release Authorization', icon: 'checklist' },
  { key: 'reports', label: 'Reports & Exports', icon: 'report' },
  { key: 'copilot', label: 'AI Copilot', icon: 'policy' },
  { key: 'audit', label: 'Audit Chain', icon: 'audit' },
  { key: 'admin', label: 'Admin & Connectors', icon: 'settings' },
  { key: 'security', label: 'Security', icon: 'security' },
  { key: 'help', label: 'Help & DPDP', icon: 'help' },
];

const MOBILE_NAV_ITEMS: { id: string; label: string; icon: IconName }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'search', label: 'Search', icon: 'search' },
  { id: 'submit', label: 'Submit', icon: 'upload' },
  { id: 'verify', label: 'Verify', icon: 'verified' },
  { id: 'reminders', label: 'Reminders', icon: 'deadline' },
];

const ROLE_NAV_KEYS: Record<AppRole, string[]> = {
  // Institution Roles
  org_admin: ['dashboard', 'search', 'submit', 'reminders', 'release', 'reports', 'copilot', 'admin', 'security', 'help'],
  institution_submitter: ['dashboard', 'search', 'submit', 'reminders', 'release', 'reports', 'copilot', 'security', 'help'],
  institution_viewer: ['dashboard', 'search', 'reminders', 'reports', 'help'],

  // AICTE Official Roles
  intake_officer: ['dashboard', 'search', 'verify', 'reports', 'copilot', 'help'],
  scrutiny_officer: ['dashboard', 'search', 'submit', 'verify', 'reminders', 'release', 'reports', 'copilot', 'audit', 'admin', 'security', 'help'],
  finance_verifier: ['verify', 'dashboard', 'search', 'reminders', 'release', 'reports', 'copilot', 'help'],
  regional_supervisor: ['dashboard', 'search', 'reminders', 'release', 'reports', 'copilot', 'help'],
  competent_authority: ['release', 'dashboard', 'search', 'reports', 'copilot', 'help'],
  audit_reviewer: ['audit', 'dashboard', 'search', 'reports', 'security', 'help'],
  identity_admin: ['admin', 'audit', 'security', 'help'],
  platform_operator: ['admin', 'copilot', 'audit', 'security', 'help'],

  // External Bank Verifier Role (isolated minimal UI per SPEC)
  bank_verifier: ['verify', 'reports', 'help'],

  // Machine Identity
  integration_service: [],

  // Phase 0 legacy aliases
  institution: ['dashboard', 'search', 'submit', 'reminders', 'release', 'reports', 'copilot', 'admin', 'security', 'help'],
  verifier: ['verify', 'dashboard', 'search', 'reminders', 'release', 'reports', 'copilot', 'help'],
  regional_officer: ['dashboard', 'search', 'reminders', 'release', 'reports', 'copilot', 'help'],
  bureau_admin: ['admin', 'copilot', 'audit', 'security', 'help'],
  auditor: ['audit', 'dashboard', 'search', 'reports', 'security', 'help'],
  bank_user: ['verify', 'reports', 'help'],
};

function getInitialTabForRole(role: AppRole, landingRoute?: string | null): string {
  // Respect backend navigation manifest landing_route if provided
  if (landingRoute) {
    if (landingRoute.includes('assigned-requests') || landingRoute.includes('verification')) {
      return 'verify';
    }
    if (landingRoute.includes('decisions')) {
      return 'release';
    }
    if (landingRoute.includes('audit')) {
      return 'audit';
    }
    if (landingRoute.includes('access-admin') || landingRoute.includes('system-health')) {
      return 'admin';
    }
  }

  // Role-specific primary landing screen
  switch (role) {
    case 'bank_verifier':
    case 'bank_user':
      return 'verify';
    case 'competent_authority':
      return 'release';
    case 'audit_reviewer':
    case 'auditor':
      return 'audit';
    case 'identity_admin':
    case 'platform_operator':
    case 'bureau_admin':
      return 'admin';
    case 'finance_verifier':
    case 'verifier':
      return 'verify';
    default:
      return 'dashboard';
  }
}

export const App: React.FC = () => {
  const { status, user, logout } = useAuth();

  if (status === 'checking') {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--canvas)',
          color: 'var(--text-muted)',
          fontSize: 13,
        }}
      >
        Loading…
      </div>
    );
  }

  if (status === 'signed-out' || !user) {
    return <LoginScreen />;
  }

  return <AuthenticatedApp userRole={user.role as AppRole} onLogout={logout} />;
};

const AuthenticatedApp: React.FC<{ userRole: AppRole; onLogout: () => void }> = ({
  userRole,
  onLogout,
}) => {
  const { navigation } = useAuth();
  const initialTab = getInitialTabForRole(userRole, navigation?.landing_route);
  const [activeTab, setActiveTab] = useState<string>(initialTab);
  const [language, setLanguage] = useState<string>('en');

  // Sync activeTab when role/navigation manifest updates
  useEffect(() => {
    const target = getInitialTabForRole(userRole, navigation?.landing_route);
    const allowed = ROLE_NAV_KEYS[userRole] ?? PRIMARY_NAV_ITEMS.map((i) => i.key);
    if (!allowed.includes(activeTab)) {
      setActiveTab(target);
    }
  }, [userRole, navigation?.landing_route]);

  const allowedKeys = ROLE_NAV_KEYS[userRole] ?? PRIMARY_NAV_ITEMS.map((i) => i.key);
  const visibleNavItems = PRIMARY_NAV_ITEMS.filter((item) => allowedKeys.includes(item.key));
  const visibleMobileItems = MOBILE_NAV_ITEMS.filter((item) => allowedKeys.includes(item.id));

  const [isNotificationCenterOpen, setIsNotificationCenterOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isAskHandbookOpen, setIsAskHandbookOpen] = useState(false);

  // Live instruments query via TanStack Query (Stream R3)
  const { data: instruments = [], isLoading, isError, error, refetch } = useInstruments();

  // Profile completion query (DESIGN_SPEC §5.1)
  const { data: profileCompletion } = useQuery<{ percent: number }>({
    queryKey: ['profile-completion'],
    queryFn: async () => {
      try {
        const data = await apiFetch<{ percent: number }>('/v1/me/profile-completion');
        return data;
      } catch {
        return { percent: 68 };
      }
    },
    staleTime: 60_000,
  });

  // Realtime stream (SSE) for live event feed (Stream R3.4)
  const { status: sseStatus } = useRealtimeStream();

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

  return (
    <div className="web-shell">
      <Navbar
        currentTab={activeTab}
        setCurrentTab={setActiveTab}
        role={userRole}
        lang={language}
        setLang={setLanguage}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        onOpenNotifications={() => setIsNotificationCenterOpen(true)}
        onLogout={onLogout}
        unreadNotificationsCount={0}
        sseStatus={sseStatus}
        profileCompletionPct={profileCompletion?.percent ?? 68}
      />

      <div className="web-shell-body">
        {/* Desktop Sidebar Card (R5.4 / DESIGN_SPEC §5.13) */}
        <Sidebar
          items={visibleNavItems}
          activeKey={activeTab}
          onSelect={setActiveTab}
          onOpenAskHandbook={() => setIsAskHandbookOpen(true)}
        />

        <main className="web-main">
          {isError && (
            <div
              data-testid="service-unavailable-banner"
              style={{
                padding: '14px 18px',
                background: 'var(--danger-container)',
                borderRadius: 'var(--radius-md, 16px)',
                color: 'var(--on-danger-container)',
                fontSize: 13,
                fontWeight: 600,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span>
                <strong>Service temporarily unavailable:</strong> Failed to fetch live instruments.{' '}
                {error instanceof ProblemError && error.correlationId
                  ? `(Correlation ID: ${error.correlationId})`
                  : ''}
              </span>
              <button
                type="button"
                onClick={() => refetch()}
                className="btn btn-compact btn-danger"
                style={{
                  height: 32,
                  padding: '0 14px',
                  fontSize: 12,
                }}
              >
                Retry
              </button>
            </div>
          )}

          {isLoading && (
            <div
              style={{
                color: 'var(--text3)',
                fontSize: 13,
                padding: 16,
                fontWeight: 600,
              }}
            >
              Loading live instruments from server…
            </div>
          )}

          {activeTab === 'dashboard' && <KPIBoard instruments={instruments} />}

          {activeTab === 'search' && <SearchWorkspace instruments={instruments} />}

          {activeTab === 'submit' && <NewFDRSubmission lang={language} />}

          {activeTab === 'verify' && <VerificationView instruments={instruments} />}

          {activeTab === 'reminders' && <RemindersView instruments={instruments} />}

          {activeTab === 'release' && (
            <ReleaseWorkflow userRole={userRole} />
          )}

          {activeTab === 'reports' && <ReportsView instruments={instruments} />}

          {activeTab === 'copilot' && <CopilotView />}

          {activeTab === 'audit' && <AuditLogView />}

          {activeTab === 'admin' && <AdminConsoleView />}

          {activeTab === 'security' && <SecurityView />}

          {activeTab === 'help' && <HelpAndRightsView />}

          {activeTab === 'public_receipt' && (
            <PublicReceiptVerification onBackToApp={() => setActiveTab('dashboard')} />
          )}
        </main>
      </div>

      {/* Mobile Floating Pill Tab Bar below 768px (DESIGN_SPEC §5.4 / R5.4) */}
      <div className="md:hidden">
        <FloatingTabBar
          items={visibleMobileItems.length > 0 ? visibleMobileItems : MOBILE_NAV_ITEMS}
          activeId={activeTab}
          onSelect={setActiveTab}
        />
      </div>

      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectAction={(tabId) => setActiveTab(tabId)}
      />

      <NotificationCenter
        isOpen={isNotificationCenterOpen}
        onClose={() => setIsNotificationCenterOpen(false)}
        onNavigateToTab={(tabId) => setActiveTab(tabId)}
      />

      <AskHandbookModal
        isOpen={isAskHandbookOpen}
        onClose={() => setIsAskHandbookOpen(false)}
      />

      <footer
        style={{
          marginTop: 'auto',
          padding: '24px 20px',
          borderTop: '1px solid var(--hairline)',
          background: 'var(--surface)',
          color: 'var(--text3)',
          fontSize: '12px',
          fontWeight: 600,
        }}
      >
        <div
          style={{
            maxWidth: 1280,
            margin: '0 auto',
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: 'var(--text1)', fontWeight: 700 }}>
              AICTE Security Deposit (FDR) Portal
            </span>
            <span>•</span>
            <span>Statutory Compliance under AICTE Act Sec. 10(k)</span>
          </div>
          <div>All rights reserved &copy; 2026 AICTE.</div>
        </div>
      </footer>
    </div>
  );
};
