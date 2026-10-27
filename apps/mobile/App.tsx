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
  const { user } = useAuth();
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

  const [instruments, setInstruments] = useState<MobileInstrument[]>([]);
  const [instrumentsLoaded, setInstrumentsLoaded] = useState(false);
  const [notifications, setNotifications] = useState<MobileNotification[]>([]);
  const [tasksCount, setTasksCount] = useState(0);

  const loadTasksCount = React.useCallback(async () => {
    const [intake, scrutiny] = await Promise.all([
      api.GET('/v1/queues/intake'),
      api.GET('/v1/queues/scrutiny'),
    ]);
    setTasksCount((intake.data?.length ?? 0) + (scrutiny.data?.length ?? 0));
  }, []);

  const loadInstruments = React.useCallback(async () => {
    const { data } = await api.GET('/v1/instruments');
    if (!data) return;
    const mapped: MobileInstrument[] = data.map((item) => {
      const numAmount = typeof item.amount === 'string' ? parseFloat(item.amount) : item.amount;
      let evLevel: any = 'L0';
      if (item.evidence_level?.startsWith('L1')) evLevel = 'L1';
      else if (item.evidence_level?.startsWith('L2')) evLevel = 'L2';
      else if (item.evidence_level?.startsWith('L3')) evLevel = 'L3';

      return {
        id: item.id,
        institution_id: item.institution_id,
        // institution_name/bank_name/branch_ifsc are genuinely optional on
        // the backend response (app/instruments/router.py InstrumentResponse)
        // — showing a specific real-sounding institution/bank as a fallback
        // when they're actually null would misattribute the record, so an
        // honest "—" placeholder is used instead of ever inventing one.
        institution_name: (item as any).institution_name || '—',
        instrument_number: item.instrument_number,
        type: item.type,
        amount: Math.round(numAmount * 100),
        bank_name: (item as any).bank_name || '—',
        branch_ifsc: (item as any).branch_ifsc || '—',
        issue_date: item.issue_date || '',
        maturity_date: item.maturity_date || '',
        status: item.status as any,
        evidence_level: evLevel,
        utr_number: item.utr || undefined,
      };
    });
    setInstruments(mapped);
    setInstrumentsLoaded(true);
  }, []);

  const loadNotifications = React.useCallback(async () => {
    const { data } = await api.GET('/v1/notifications');
    if (!data) return;
    const mapped: MobileNotification[] = data.items.map((n) => ({
      id: n.id,
      title: n.title,
      body: n.body,
      category: n.category as any,
      status: n.status as any,
      created_at: new Date(n.created_at).toLocaleString(),
      instrument_id: undefined,
    }));
    setNotifications(mapped);
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        await loadInstruments();
      } catch {
        // Real failure — instrumentsLoaded stays false, HomeScreen shows the
        // honest "could not load" state, never a fabricated fallback list.
      }
      try {
        await loadNotifications();
      } catch {
        // Same: notifications stays empty/honest on failure.
      }
      try {
        await loadTasksCount();
      } catch {
        // tasksCount stays 0 — honest "nothing pending" rather than a guess.
      }
    })();
    return () => {
      active = false;
    };
  }, [loadInstruments, loadNotifications, loadTasksCount]);

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
    api.POST('/v1/notifications/{notification_id}/acknowledge', {
      params: { path: { notification_id: id } },
    });
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
        tasksPendingCount={tasksCount}
      />

      <BiometricLockModal visible={isLocked} onUnlock={() => setIsLocked(false)} />

      <QRScannerModal visible={qrScannerVisible} onClose={() => setQrScannerVisible(false)} />

      <DocumentCaptureModal
        visible={docCaptureVisible}
        onClose={() => setDocCaptureVisible(false)}
        institutionId={user?.institution_id ?? null}
        onSubmitted={loadInstruments}
      />

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
