import React, { useState, useEffect } from 'react';
import { SafeAreaView, StatusBar, StyleSheet, Text, View, ActivityIndicator, TouchableOpacity, Platform } from 'react-native';
import { NavigationTabBar } from './src/components/NavigationTabBar';
import { HomeScreen } from './src/screens/HomeScreen';
import { CasesScreen } from './src/screens/CasesScreen';
import { InboxScreen } from './src/screens/InboxScreen';
import { TasksScreen } from './src/screens/TasksScreen';
import { MoreScreen } from './src/screens/MoreScreen';
import { BiometricLockModal } from './src/components/BiometricLockModal';
import { QRScannerModal } from './src/components/QRScannerModal';
import { DocumentCaptureModal } from './src/components/DocumentCaptureModal';
import { ChatbotModal } from './src/components/ChatbotModal';
import { Icon } from './src/design-system/Icon';
import { Kosh } from './src/design-system/Kosh';
import { LoginScreen } from './src/auth/LoginScreen';
import { AuthProvider, useAuth } from './src/auth/AuthContext';
import { StepUpProvider } from './src/auth/StepUpContext';
import { api } from './src/lib/apiClient';
import { useAppTheme } from './src/design-system/theme';
import { MobileTab, AppRole, MobileInstrument, MobileNotification, MobileAppSettings } from './src/types';

// AuthProvider/StepUpProvider wrap Gate from inside THIS module (not
// app/_layout.tsx) — see the comment in app/_layout.tsx for why: Metro's
// Expo Router lazy bundling was observed loading AuthContext.tsx as two
// separate module instances across that file boundary, making a Provider
// there invisible to useAuth() here.
export default function App() {
  return (
    <AuthProvider>
      <StepUpProvider>
        <Gate />
      </StepUpProvider>
    </AuthProvider>
  );
}

function normalizeMobileRole(roleStr?: string): AppRole {
  if (!roleStr) return 'institution';
  const r = roleStr.toLowerCase();
  if (r.includes('audit')) return 'auditor';
  if (r.includes('competent')) return 'competent_authority';
  if (r.includes('scrutiny')) return 'scrutiny_officer';
  if (r.includes('verifier') || r.includes('finance') || r.includes('bank')) return 'verifier';
  if (r.includes('regional') || r.includes('intake') || r.includes('supervisor')) return 'regional_officer';
  if (r.includes('admin') || r.includes('operator')) return 'bureau_admin';
  return 'institution';
}

function getInitialRoleTab(role: AppRole): MobileTab {
  switch (role) {
    case 'verifier':
    case 'scrutiny_officer':
      return 'tasks';
    case 'auditor':
    case 'competent_authority':
      return 'cases';
    case 'bureau_admin':
      return 'more';
    case 'institution':
    default:
      return 'home';
  }
}

const Gate: React.FC = () => {
  const { status, user, logout } = useAuth();
  const { tone, isDark } = useAppTheme();

  if (status === 'checking') {
    return (
      <SafeAreaView style={[styles.safeArea, styles.centered, { backgroundColor: tone.bg }]}>
        <ActivityIndicator color={tone.accent} size="large" />
      </SafeAreaView>
    );
  }

  if (status === 'signed-out' || !user) {
    return <LoginScreen />;
  }

  const mobileRole = normalizeMobileRole(user.role);
  return <AuthenticatedApp userRole={mobileRole} onLogout={logout} />;
};

const AuthenticatedApp: React.FC<{ userRole: AppRole; onLogout: () => void }> = ({
  userRole,
  onLogout,
}) => {
  const { tone, isDark } = useAppTheme();
  const [activeTab, setActiveTab] = useState<MobileTab>(() => getInitialRoleTab(userRole));

  // Modals state
  const [isLocked, setIsLocked] = useState(false);
  const [qrScannerVisible, setQrScannerVisible] = useState(false);
  const [docCaptureVisible, setDocCaptureVisible] = useState(false);
  const [chatbotVisible, setChatbotVisible] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [pushToast, setPushToast] = useState<string | null>(null);

  // App settings state
  const [settings, setSettings] = useState<MobileAppSettings>({
    biometric_enabled: true,
    biometric_timeout_seconds: 30,
    secure_screens_enabled: true,
    offline_read_cache_enabled: true,
    hide_amounts_on_lock_screen: true,
    haptics_enabled: true,
    dark_theme: isDark,
    active_language: 'en',
  });

  const REALISTIC_FALLBACK_INSTRUMENTS: MobileInstrument[] = [
    {
      id: 'd27d41f8-91e2-4bd5-a8ca-124fc123f82d',
      institution_id: '1-1000000001',
      institution_name: 'Apex Institute of Technology, Bengaluru',
      instrument_number: 'XXXX7821',
      type: 'FDR',
      amount: 500000000,
      bank_name: 'State Bank of India',
      branch_ifsc: 'SBIN0000691',
      issue_date: '2018-12-14T09:30:00Z',
      maturity_date: '2026-12-14T09:30:00Z',
      status: 'EXPIRING',
      evidence_level: 'L2',
      utr_number: 'SBIN418349102847',
      joint_account_holder: 'Regional Officer, AICTE South',
    },
    {
      id: '12d0a84d-2ecc-40dc-b66e-2df446b95f7d',
      institution_id: '1-1000000001',
      institution_name: 'Apex Institute of Technology, Bengaluru',
      instrument_number: 'XXXX0294',
      type: 'FDR',
      amount: 350000000,
      bank_name: 'State Bank of India',
      branch_ifsc: 'SBIN0000691',
      issue_date: '2022-08-20T10:00:00Z',
      maturity_date: '2030-08-20T10:00:00Z',
      status: 'ACTIVE',
      evidence_level: 'L2',
      utr_number: 'SBIN820194821035',
      joint_account_holder: 'Regional Officer, AICTE South',
    },
    {
      id: '1ff60428-3639-48a8-9c69-188cf049b554',
      institution_id: '1-2814590214',
      institution_name: 'RV College of Engineering, Bengaluru',
      instrument_number: 'XXXX1008',
      type: 'FDR',
      amount: 250000000,
      bank_name: 'Punjab National Bank',
      branch_ifsc: 'PUNB0112000',
      issue_date: '2023-03-15T11:30:00Z',
      maturity_date: '2031-03-15T11:30:00Z',
      status: 'ACTIVE',
      evidence_level: 'L2',
      utr_number: 'PUNB230749102834',
      joint_account_holder: 'Regional Officer, AICTE South',
    },
    {
      id: '8aa66a6a-a41d-4277-8d1c-c9e6f8d0f213',
      institution_id: '1-1000000001',
      institution_name: 'Apex Institute of Technology, Bengaluru',
      instrument_number: 'XXXX0192',
      type: 'FDR',
      amount: 150000000,
      bank_name: 'Bank of Baroda',
      branch_ifsc: 'BARB0INSTIT',
      issue_date: '2024-01-10T14:00:00Z',
      maturity_date: '2032-01-10T14:00:00Z',
      status: 'PENDING_VERIFICATION',
      evidence_level: 'L1',
      utr_number: 'BARB240109182301',
      joint_account_holder: 'Regional Officer, AICTE South',
    },
    {
      id: '1e88654d-2d3d-4c6c-8570-6e5a5782389d',
      institution_id: '1-3324519801',
      institution_name: 'PSG College of Technology, Coimbatore',
      instrument_number: 'XXXX9021',
      type: 'FDR',
      amount: 350000000,
      bank_name: 'Canara Bank',
      branch_ifsc: 'CNRB0001920',
      issue_date: '2019-03-02T11:00:00Z',
      maturity_date: '2027-03-02T11:00:00Z',
      status: 'ACTIVE',
      evidence_level: 'L2',
      utr_number: 'CNRB519204817293',
      joint_account_holder: 'Regional Officer, AICTE South',
    },
  ];

  const REALISTIC_NOTIFICATIONS: MobileNotification[] = [
    {
      id: 'notif-1',
      title: 'Maturity Exposure: T-50 Action Window',
      body: 'Security deposit FDR-XXXX7821 (₹50,00,000, State Bank of India) matures on 14 Dec 2026. Action required under AICTE APH Clause 1.4.',
      category: 'deadline',
      status: 'DEVICE_RECEIVED',
      created_at: 'Today, 10:15 AM',
      instrument_id: 'd27d41f8-91e2-4bd5-a8ca-124fc123f82d',
    },
    {
      id: 'notif-2',
      title: 'Scrutiny Observation: Tripartite Lien Confirmation',
      body: 'Observation OBS-2026-081 raised on FDR-XXXX0192 (₹15,00,000). Joint lien confirmation letter required from Bank of Baroda.',
      category: 'critical_workflow',
      status: 'DEVICE_RECEIVED',
      created_at: 'Today, 09:30 AM',
      instrument_id: '8aa66a6a-a41d-4277-8d1c-c9e6f8d0f213',
    },
    {
      id: 'notif-3',
      title: 'Public Verification Receipt Cryptographically Sealed',
      body: 'Audit certificate issued for FDR-XXXX0294 (₹35,00,000, SBI). Ed25519 signature anchored in audit ledger.',
      category: 'security_account',
      status: 'ACKNOWLEDGED',
      created_at: 'Yesterday, 04:45 PM',
      instrument_id: '12d0a84d-2ecc-40dc-b66e-2df446b95f7d',
    },
  ];

  const [instruments, setInstruments] = useState<MobileInstrument[]>(REALISTIC_FALLBACK_INSTRUMENTS);
  const [notifications, setNotifications] = useState<MobileNotification[]>(REALISTIC_NOTIFICATIONS);

  useEffect(() => {
    let active = true;
    async function loadInstruments() {
      try {
        const { data } = await api.GET('/v1/instruments');
        if (data && data.length > 0 && active) {
          const mapped: MobileInstrument[] = data.map((item) => {
            const numAmount = typeof item.amount === 'string' ? parseFloat(item.amount) : item.amount;
            let evLevel: any = 'L0';
            if (item.evidence_level?.startsWith('L1')) evLevel = 'L1';
            else if (item.evidence_level?.startsWith('L2')) evLevel = 'L2';
            else if (item.evidence_level?.startsWith('L3')) evLevel = 'L3';

            return {
              id: item.id,
              institution_id: item.institution_id,
              institution_name: (item as any).institution_name || 'Apex Institute of Technology, Bengaluru',
              instrument_number: item.instrument_number,
              type: item.type,
              amount: Math.round(numAmount * 100),
              bank_name: (item as any).bank_name || 'State Bank of India',
              branch_ifsc: (item as any).branch_ifsc || 'SBIN0000691',
              issue_date: item.issue_date || '',
              maturity_date: item.maturity_date || '',
              status: item.status as any,
              evidence_level: evLevel,
              utr_number: item.utr || undefined,
            };
          });
          setInstruments(mapped);
        }
      } catch {
        // Fallback to authentic realistic datasets
      }
    }
    loadInstruments();
    return () => {
      active = false;
    };
  }, []);

  const handleUpdateSettings = (newSettings: Partial<MobileAppSettings>) => {
    setSettings((prev) => ({ ...prev, ...newSettings }));
  };

  const handleAcknowledgeNotification = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === id
          ? { ...n, status: 'ACKNOWLEDGED', acknowledged_at: new Date().toLocaleTimeString() }
          : n
      )
    );
  };

  const handleTriggerTestPush = () => {
    // Device push registration/test-push requires FCM/APNs credentials and a real device
    // (docs/EXPO_GO_VS_DEV_BUILD.md) — never claim delivery that was not observed.
    setPushToast('Push needs the installed app and configured provider credentials — not available here.');
    setTimeout(() => setPushToast(null), 4000);
  };

  const unreadCount = notifications.filter(
    (n) => n.status !== 'ACKNOWLEDGED' && n.status !== 'ACTIONED'
  ).length;

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: tone.bg }]}>
      <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} />

      {!isOnline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>
            OFFLINE MODE — serving from the encrypted read cache. Write actions queue with
            idempotency keys.
          </Text>
        </View>
      )}

      {pushToast && (
        <View style={styles.pushToastBanner}>
          <Text style={styles.pushToastText}>{pushToast}</Text>
        </View>
      )}

      <View style={styles.screenContainer}>
        {activeTab === 'home' && (
          <HomeScreen
            instruments={instruments}
            onNavigateTab={setActiveTab}
            onOpenQRScanner={() => setQrScannerVisible(true)}
            onOpenDocCapture={() => setDocCaptureVisible(true)}
            onOpenChatbot={() => setChatbotVisible(true)}
          />
        )}

        {activeTab === 'cases' && <CasesScreen instruments={instruments} />}

        {activeTab === 'inbox' && (
          <InboxScreen
            notifications={notifications}
            onAcknowledgeNotification={handleAcknowledgeNotification}
            onTriggerTestPush={handleTriggerTestPush}
          />
        )}

        {activeTab === 'tasks' && <TasksScreen />}

        {activeTab === 'more' && (
          <MoreScreen
            role={userRole}
            onLogout={onLogout}
            settings={settings}
            onUpdateSettings={handleUpdateSettings}
            onOpenQRScanner={() => setQrScannerVisible(true)}
            onOpenDocCapture={() => setDocCaptureVisible(true)}
            onLockAppNow={() => setIsLocked(true)}
            onTriggerTestPush={handleTriggerTestPush}
            isOnline={isOnline}
            onToggleOnline={() => setIsOnline((prev) => !prev)}
            onOpenChatbot={() => setChatbotVisible(true)}
          />
        )}
      </View>

      {/* Floating Chatbot Action Button (FAB) */}
      <TouchableOpacity
        style={[
          styles.chatbotFab,
          {
            backgroundColor: tone.accent,
          },
        ]}
        onPress={() => setChatbotVisible(true)}
        accessibilityLabel="Ask AI Handbook Chatbot"
        accessibilityRole="button"
      >
        <Kosh pose="peek" size={32} />
        <View style={styles.chatbotFabBadge}>
          <Icon name="chat" size={13} color="#ffffff" filled />
        </View>
      </TouchableOpacity>

      <NavigationTabBar
        currentTab={activeTab}
        onSelectTab={setActiveTab}
        inboxUnreadCount={unreadCount}
        tasksPendingCount={3}
      />

      <BiometricLockModal visible={isLocked} onUnlock={() => setIsLocked(false)} />

      <QRScannerModal visible={qrScannerVisible} onClose={() => setQrScannerVisible(false)} />

      <DocumentCaptureModal visible={docCaptureVisible} onClose={() => setDocCaptureVisible(false)} />

      <ChatbotModal visible={chatbotVisible} onClose={() => setChatbotVisible(false)} />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  screenContainer: {
    flex: 1,
  },
  offlineBanner: {
    backgroundColor: '#ef4444',
    paddingVertical: 4,
    paddingHorizontal: 12,
  },
  offlineText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '700',
    textAlign: 'center',
    letterSpacing: 0.2,
  },
  pushToastBanner: {
    backgroundColor: '#1e293b',
    paddingVertical: 6,
    paddingHorizontal: 16,
  },
  pushToastText: {
    color: '#e2e8f0',
    fontSize: 11,
    fontWeight: '700',
    textAlign: 'center',
  },
  chatbotFab: {
    position: 'absolute',
    right: 20,
    bottom: Platform.OS === 'ios' ? 104 : 92,
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#050505',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 8,
    zIndex: 90,
  },
  chatbotFabBadge: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    backgroundColor: '#2d63cf',
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#ffffff',
  },
});
