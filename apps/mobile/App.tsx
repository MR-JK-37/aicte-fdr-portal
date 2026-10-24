import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  SafeAreaView,
  StatusBar,
  Platform,
} from 'react-native';
import { NavigationTabBar } from './src/components/NavigationTabBar';
import { HomeScreen } from './src/screens/HomeScreen';
import { CasesScreen } from './src/screens/CasesScreen';
import { InboxScreen } from './src/screens/InboxScreen';
import { TasksScreen } from './src/screens/TasksScreen';
import { MoreScreen } from './src/screens/MoreScreen';
import { BiometricLockModal } from './src/components/BiometricLockModal';
import { QRScannerModal } from './src/components/QRScannerModal';
import { DocumentCaptureModal } from './src/components/DocumentCaptureModal';
import {
  MobileTab,
  AppRole,
  MobileInstrument,
  MobileNotification,
  MobileAppSettings,
} from './src/types';

export default function App() {
  const [activeTab, setActiveTab] = useState<MobileTab>('home');
  const [role, setRole] = useState<AppRole>('institution');

  // Modals state
  const [isLocked, setIsLocked] = useState(false);
  const [qrScannerVisible, setQrScannerVisible] = useState(false);
  const [docCaptureVisible, setDocCaptureVisible] = useState(false);
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
    dark_theme: true,
    active_language: 'en',
  });

  // Instruments data
  const [instruments, setInstruments] = useState<MobileInstrument[]>([
    {
      id: 'inst-1',
      institution_id: 'AICTE-ENGG-001',
      institution_name: 'Delhi Global Technical Campus',
      instrument_number: 'AXIS-FDR-99201',
      type: 'FDR',
      amount: 350000000, // ₹35,00,000
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
      amount: 250000000, // ₹25,00,000
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

  // Notifications data
  const [notifications, setNotifications] = useState<MobileNotification[]>([
    {
      id: 'notif-m-1',
      title: 'T-30 Statutory Renewal Reminder Issued',
      body: 'Deposit AXIS-FDR-99201 is maturing on 2026-11-20. Predecessor renewal submission or replacement is required within 30 days.',
      category: 'deadline',
      status: 'DEVICE_RECEIVED',
      created_at: '2026-10-24 10:00 IST',
      action_target: 'cases',
      instrument_id: 'AXIS-FDR-99201',
    },
    {
      id: 'notif-m-2',
      title: 'Shortfall Casework Assigned',
      body: 'FDR PNB-771829 has a registered deposit of ₹25,00,000 against statutory requirement of ₹35,00,000. Scrutiny observation created.',
      category: 'critical_workflow',
      status: 'OPENED',
      created_at: '2026-10-24 09:30 IST',
      action_target: 'tasks',
      instrument_id: 'PNB-771829',
    },
  ]);

  const handleUpdateSettings = (newSettings: Partial<MobileAppSettings>) => {
    setSettings((prev) => ({ ...prev, ...newSettings }));
  };

  const handleAcknowledgeNotification = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === id
          ? {
              ...n,
              status: 'ACKNOWLEDGED',
              acknowledged_at: new Date().toLocaleTimeString(),
            }
          : n
      )
    );
  };

  const handleTriggerTestPush = () => {
    const testNotice: MobileNotification = {
      id: `notif-m-${Date.now().toString().slice(-4)}`,
      title: 'AICTE FDR Portal — Action Needed',
      body: 'TEST ALERT: Statutory event committed to transactional outbox and delivered to mobile companion.',
      category: 'critical_workflow',
      status: 'DEVICE_RECEIVED',
      created_at: new Date().toLocaleTimeString(),
    };
    setNotifications((prev) => [testNotice, ...prev]);
    setPushToast('Instant push delivered via FCM/APNs pipeline (M-01/M-16)');
    setTimeout(() => setPushToast(null), 4000);
  };

  const unreadCount = notifications.filter(
    (n) => n.status !== 'ACKNOWLEDGED' && n.status !== 'ACTIONED'
  ).length;

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" />

      {/* Offline Status Warning Banner (M-12/M-13) */}
      {!isOnline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>
            OFFLINE MODE • Serving from encrypted read cache (M-12). Write actions queued with idempotency keys.
          </Text>
        </View>
      )}

      {/* Test Push Delivered Toast */}
      {pushToast && (
        <View style={styles.pushToastBanner}>
          <Text style={styles.pushToastText}>{pushToast}</Text>
        </View>
      )}

      {/* Primary Screen Views */}
      <View style={styles.screenContainer}>
        {activeTab === 'home' && (
          <HomeScreen
            instruments={instruments}
            onNavigateTab={setActiveTab}
            onSelectInstrument={(inst) => setActiveTab('cases')}
            onOpenQRScanner={() => setQrScannerVisible(true)}
            onOpenDocCapture={() => setDocCaptureVisible(true)}
          />
        )}

        {activeTab === 'cases' && (
          <CasesScreen
            instruments={instruments}
          />
        )}

        {activeTab === 'inbox' && (
          <InboxScreen
            notifications={notifications}
            onAcknowledgeNotification={handleAcknowledgeNotification}
            onTriggerTestPush={handleTriggerTestPush}
          />
        )}

        {activeTab === 'tasks' && (
          <TasksScreen />
        )}

        {activeTab === 'more' && (
          <MoreScreen
            role={role}
            setRole={setRole}
            settings={settings}
            onUpdateSettings={handleUpdateSettings}
            onOpenQRScanner={() => setQrScannerVisible(true)}
            onOpenDocCapture={() => setDocCaptureVisible(true)}
            onLockAppNow={() => setIsLocked(true)}
            onTriggerTestPush={handleTriggerTestPush}
            isOnline={isOnline}
            onToggleOnline={() => setIsOnline((prev) => !prev)}
          />
        )}
      </View>

      {/* Platform Navigation Tab Bar */}
      <NavigationTabBar
        currentTab={activeTab}
        onSelectTab={setActiveTab}
        inboxUnreadCount={unreadCount}
        tasksPendingCount={3}
      />

      {/* Biometric App Lock Modal (M-03) */}
      <BiometricLockModal
        visible={isLocked}
        onUnlock={() => setIsLocked(false)}
        institutionName={instruments[0].institution_name}
      />

      {/* QR Scanner Modal (M-09) */}
      <QRScannerModal
        visible={qrScannerVisible}
        onClose={() => setQrScannerVisible(false)}
      />

      {/* Document Capture Modal (M-05) */}
      <DocumentCaptureModal
        visible={docCaptureVisible}
        onClose={() => setDocCaptureVisible(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#050505',
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
    backgroundColor: '#00eeff',
    paddingVertical: 6,
    paddingHorizontal: 16,
  },
  pushToastText: {
    color: '#050505',
    fontSize: 11,
    fontWeight: '800',
    textAlign: 'center',
  },
});
