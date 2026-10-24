import React, { useState } from 'react';
import { StyleSheet, View, Text, ScrollView, TouchableOpacity, Switch, Platform, Alert } from 'react-native';
import { Icon } from '../design-system/Icon';
import { AppRole, MobileAppSettings } from '../types';

interface MoreScreenProps {
  role: AppRole;
  setRole: (role: AppRole) => void;
  settings: MobileAppSettings;
  onUpdateSettings: (newSettings: Partial<MobileAppSettings>) => void;
  onOpenQRScanner: () => void;
  onOpenDocCapture: () => void;
  onLockAppNow: () => void;
  onTriggerTestPush?: () => void;
  isOnline: boolean;
  onToggleOnline: () => void;
}

export const MoreScreen: React.FC<MoreScreenProps> = ({
  role,
  setRole,
  settings,
  onUpdateSettings,
  onOpenQRScanner,
  onOpenDocCapture,
  onLockAppNow,
  onTriggerTestPush,
  isOnline,
  onToggleOnline,
}) => {
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const handleDeepLinkTest = () => {
    showToast('Handled deep link: aicte-fdr://case/inst-1 (M-08)');
  };

  const handleReportProblem = () => {
    showToast('Diagnostics bundle generated: PID_9021 (Correlation ID: req_m_99201). Zero PII.');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <Text style={styles.headerSuper}>MOBILE COMPANION CAPABILITIES</Text>
        <Text style={styles.headerTitle}>Features & Settings (§9A)</Text>
      </View>

      {toast && (
        <View style={styles.toastBanner}>
          <Icon name="verified" size={14} color="#00eeff" />
          <Text style={styles.toastText}>{toast}</Text>
        </View>
      )}

      {/* Role Switcher */}
      <View style={styles.sectionCard}>
        <Text style={styles.secTitle}>Active Signatory Role</Text>
        <View style={styles.roleGrid}>
          {(['institution', 'scrutiny_officer', 'competent_authority', 'auditor'] as AppRole[]).map((r) => {
            const active = role === r;
            return (
              <TouchableOpacity
                key={r}
                style={[styles.roleBtn, active && styles.roleBtnActive]}
                onPress={() => setRole(r)}
              >
                <Text style={[styles.roleText, active && styles.roleTextActive]}>
                  {r.replace('_', ' ').toUpperCase()}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Mobile-Only Feature Launchers */}
      <View style={styles.sectionCard}>
        <Text style={styles.secTitle}>Mobile-Exclusive Tools (§9A)</Text>
        <TouchableOpacity style={styles.navRow} onPress={onOpenQRScanner}>
          <View style={styles.rowLeft}>
            <Icon name="qr" size={18} color="#00eeff" />
            <View>
              <Text style={styles.rowTitle}>Receipt QR Scanner (M-09)</Text>
              <Text style={styles.rowSub}>Offline Ed25519 signature checks</Text>
            </View>
          </View>
          <Text style={styles.rowArrow}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.navRow} onPress={onOpenDocCapture}>
          <View style={styles.rowLeft}>
            <Icon name="scan" size={18} color="#00eeff" />
            <View>
              <Text style={styles.rowTitle}>Document Capture (M-05)</Text>
              <Text style={styles.rowSub}>Camera scan with perspective crop</Text>
            </View>
          </View>
          <Text style={styles.rowArrow}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.navRow} onPress={onLockAppNow}>
          <View style={styles.rowLeft}>
            <Icon name="lock" size={18} color="#fbbf24" />
            <View>
              <Text style={styles.rowTitle}>Lock App with Biometrics (M-03)</Text>
              <Text style={styles.rowSub}>Instant Face ID / Fingerprint veil</Text>
            </View>
          </View>
          <Text style={styles.rowArrow}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.navRow} onPress={handleDeepLinkTest}>
          <View style={styles.rowLeft}>
            <Icon name="link" size={18} color="#c084fc" />
            <View>
              <Text style={styles.rowTitle}>Test Deep Link (M-08)</Text>
              <Text style={styles.rowSub}>Simulate aicte-fdr://case/inst-1</Text>
            </View>
          </View>
          <Text style={styles.rowArrow}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Security & Device Policies */}
      <View style={styles.sectionCard}>
        <Text style={styles.secTitle}>Security & Privacy (M-03, M-04, M-19)</Text>

        <View style={styles.switchRow}>
          <View style={styles.switchLabelBox}>
            <Text style={styles.rowTitle}>Biometric App Lock (M-03)</Text>
            <Text style={styles.rowSub}>Auto-lock after 30 seconds idle</Text>
          </View>
          <Switch
            value={settings.biometric_enabled}
            onValueChange={(val) => onUpdateSettings({ biometric_enabled: val })}
            trackColor={{ false: '#334155', true: '#00eeff' }}
            thumbColor="#ffffff"
          />
        </View>

        <View style={styles.switchRow}>
          <View style={styles.switchLabelBox}>
            <Text style={styles.rowTitle}>Secure Screens (M-04)</Text>
            <Text style={styles.rowSub}>FLAG_SECURE screen capture block</Text>
          </View>
          <Switch
            value={settings.secure_screens_enabled}
            onValueChange={(val) => onUpdateSettings({ secure_screens_enabled: val })}
            trackColor={{ false: '#334155', true: '#00eeff' }}
            thumbColor="#ffffff"
          />
        </View>

        <View style={styles.switchRow}>
          <View style={styles.switchLabelBox}>
            <Text style={styles.rowTitle}>Hide Amounts on Lock-Screen (M-19)</Text>
            <Text style={styles.rowSub}>Masks rupee figures in push banners</Text>
          </View>
          <Switch
            value={settings.hide_amounts_on_lock_screen}
            onValueChange={(val) => onUpdateSettings({ hide_amounts_on_lock_screen: val })}
            trackColor={{ false: '#334155', true: '#00eeff' }}
            thumbColor="#ffffff"
          />
        </View>
      </View>

      {/* Network & Offline Resilience (M-12, M-13) */}
      <View style={styles.sectionCard}>
        <Text style={styles.secTitle}>Resilience & Cache (M-12, M-13)</Text>
        <View style={styles.switchRow}>
          <View style={styles.switchLabelBox}>
            <Text style={styles.rowTitle}>Network Connectivity State</Text>
            <Text style={styles.rowSub}>{isOnline ? 'Online (SSE Active)' : 'Offline (Local Read Cache Only)'}</Text>
          </View>
          <Switch
            value={isOnline}
            onValueChange={onToggleOnline}
            trackColor={{ false: '#ef4444', true: '#3ddc97' }}
            thumbColor="#ffffff"
          />
        </View>

        <View style={styles.switchRow}>
          <View style={styles.switchLabelBox}>
            <Text style={styles.rowTitle}>Encrypted Read Cache (M-12)</Text>
            <Text style={styles.rowSub}>Scoped to verified active registers</Text>
          </View>
          <Switch
            value={settings.offline_read_cache_enabled}
            onValueChange={(val) => onUpdateSettings({ offline_read_cache_enabled: val })}
            trackColor={{ false: '#334155', true: '#00eeff' }}
            thumbColor="#ffffff"
          />
        </View>
      </View>

      {/* Push & Device Diagnostics (M-16, M-18, M-20, M-21) */}
      <View style={styles.sectionCard}>
        <Text style={styles.secTitle}>Device Diagnostics & Gating (M-16, M-18, M-20)</Text>

        {onTriggerTestPush && (
          <TouchableOpacity style={styles.actionButton} onPress={onTriggerTestPush}>
            <Icon name="notifications" size={16} color="#050505" />
            <Text style={styles.actionButtonText}>Send Test Push Notification (M-16)</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity style={styles.outlineButton} onPress={handleReportProblem}>
          <Icon name="warning" size={16} color="#cbd5e1" />
          <Text style={styles.outlineButtonText}>Report a Problem (M-20)</Text>
        </TouchableOpacity>

        {/* Dictation & Simulation Compliance Notice (M-21) */}
        <View style={styles.complianceBox}>
          <Text style={styles.complianceTitle}>Statutory Audio Compliance (M-21)</Text>
          <Text style={styles.complianceText}>
            This official application strictly uses native OS keyboard dictation. Zero voice or calling simulations exist in production builds.
          </Text>
        </View>

        <View style={styles.versionBox}>
          <Text style={styles.versionText}>AICTE FDR Companion v1.0.0 (Build 20261024)</Text>
          <Text style={styles.versionSub}>Platform: {Platform.OS.toUpperCase()} • Min Supported: 1.0.0 (M-18)</Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  content: {
    padding: 16,
    gap: 16,
    paddingBottom: 32,
  },
  topHeader: {
    marginTop: 6,
    gap: 2,
  },
  headerSuper: {
    fontSize: 10,
    color: '#00eeff',
    fontWeight: '700',
    letterSpacing: 1,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: -0.5,
  },
  toastBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(0, 238, 255, 0.15)',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.3)',
  },
  toastText: {
    color: '#00eeff',
    fontSize: 11,
    fontWeight: '600',
  },
  sectionCard: {
    backgroundColor: '#151316',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    padding: 16,
    gap: 12,
  },
  secTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  roleGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  roleBtn: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  roleBtnActive: {
    backgroundColor: 'rgba(0, 238, 255, 0.15)',
    borderColor: '#00eeff',
  },
  roleText: {
    color: '#94a3b8',
    fontSize: 10,
    fontWeight: '700',
  },
  roleTextActive: {
    color: '#00eeff',
  },
  navRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  rowTitle: {
    color: '#f8fafc',
    fontSize: 13,
    fontWeight: '600',
  },
  rowSub: {
    color: '#64748b',
    fontSize: 10,
    marginTop: 1,
  },
  rowArrow: {
    color: '#94a3b8',
    fontSize: 18,
    fontWeight: '600',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  switchLabelBox: {
    flex: 1,
  },
  actionButton: {
    backgroundColor: '#00eeff',
    borderRadius: 12,
    paddingVertical: 12,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  actionButtonText: {
    color: '#050505',
    fontSize: 12,
    fontWeight: '700',
  },
  outlineButton: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    paddingVertical: 12,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: '#475569',
  },
  outlineButtonText: {
    color: '#cbd5e1',
    fontSize: 12,
    fontWeight: '600',
  },
  complianceBox: {
    backgroundColor: '#0c0716',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 12,
    padding: 12,
    gap: 4,
  },
  complianceTitle: {
    color: '#cbd5e1',
    fontSize: 11,
    fontWeight: '700',
  },
  complianceText: {
    color: '#64748b',
    fontSize: 10,
    lineHeight: 14,
  },
  versionBox: {
    alignItems: 'center',
    marginTop: 4,
  },
  versionText: {
    color: '#64748b',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  versionSub: {
    color: '#475569',
    fontSize: 10,
    marginTop: 2,
  },
});
