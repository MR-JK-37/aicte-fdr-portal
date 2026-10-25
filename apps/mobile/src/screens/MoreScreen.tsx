import React, { useState } from 'react';
import { StyleSheet, View, Text, ScrollView, TouchableOpacity, Switch, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { AppRole, MobileAppSettings } from '../types';
import { MfaEnrolmentWizard } from '../auth/MfaEnrolmentWizard';

interface MoreScreenProps {
  role: AppRole;
  onLogout: () => void;
  settings: MobileAppSettings;
  onUpdateSettings: (newSettings: Partial<MobileAppSettings>) => void;
  onOpenQRScanner: () => void;
  onOpenDocCapture: () => void;
  onLockAppNow: () => void;
  onTriggerTestPush?: () => void;
  isOnline: boolean;
  onToggleOnline: () => void;
  onOpenChatbot?: () => void;
}

/**
 * Mobile Profile & Settings Screen
 * Mirrors Screen 4 from ui-refrence.png:
 * - Topbar: fdr@portal, progress 56%, bell, Scrutiny Officer role pill
 * - Region chip: Region: South
 * - Avatar circle XL: AK
 * - Name: Anil Kumar / Scrutiny Officer
 * - Switch row: Show my name to institutions
 * - Section "Main" grouped card:
 *   - Two-step verification -> On ›
 *   - Passkeys -> 1 ›
 *   - Devices and sessions -> ›
 *   - Language -> English ›
 * - Grouped item: Privacy policy -> ›
 * - Mobile companion tools & Sign out
 */
import { useAuth } from '../auth/AuthContext';

export const MoreScreen: React.FC<MoreScreenProps> = ({
  role,
  onLogout,
  settings,
  onUpdateSettings,
  onOpenQRScanner,
  onOpenDocCapture,
  onLockAppNow,
  onTriggerTestPush,
  isOnline,
  onToggleOnline,
  onOpenChatbot,
}) => {
  const { tone, isDark } = useAppTheme();
  const { user } = useAuth();
  const [mfaWizardVisible, setMfaWizardVisible] = useState(false);
  const [showNameToInstitutions, setShowNameToInstitutions] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  const cardBg = isDark ? tone.surface : '#ffffff';

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const roleFormatted = role.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const userName = user?.full_name || 'Official User';
  const userInitials = userName
    .split(' ')
    .filter(Boolean)
    .map((p) => p[0].toUpperCase())
    .slice(0, 2)
    .join('') || 'OU';

  return (
    <View style={[styles.container, { backgroundColor: tone.bg }]}>
      {/* 1. TopBar Header matching reference */}
      <View style={styles.topbar}>
        <View style={styles.topbarLeft}>
          <Text style={[styles.wordmark, { color: tone.text1 }]}>
            fdr<Text style={{ color: tone.accent }}>@</Text>portal
          </Text>
        </View>

        <View style={styles.topbarRight}>
          <View style={styles.progressMiniWrap}>
            <View style={[styles.progressTrack, { backgroundColor: isDark ? tone.surfaceMuted : '#e2e8f0' }]}>
              <View style={[styles.progressFill, { width: '56%', backgroundColor: tone.ink }]} />
            </View>
            <Text style={[styles.progressText, { color: tone.text1 }]}>56%</Text>
          </View>

          <TouchableOpacity style={[styles.bellBtn, { backgroundColor: cardBg }]}>
            <Icon name="notifications" size={18} color={tone.text1} />
          </TouchableOpacity>

          <View style={[styles.rolePill, { backgroundColor: tone.accentContainer }]}>
            <Text style={[styles.rolePillText, { color: tone.accent }]}>{roleFormatted}</Text>
          </View>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {toast && (
          <View style={styles.toastBanner}>
            <Icon name="verified" size={14} color="#059669" />
            <Text style={styles.toastText}>{toast}</Text>
          </View>
        )}

        {/* Profile Card with Avatar XL and Region Chip */}
        <View style={styles.profileHeader}>
          {/* Region Chip */}
          <View style={styles.regionChip}>
            <Text style={styles.regionChipText}>Region: South</Text>
          </View>

          {/* Avatar XL */}
          <View style={[styles.avatarXL, { backgroundColor: tone.accentContainer }]}>
            <Text style={[styles.avatarXLText, { color: tone.accent }]}>{userInitials}</Text>
          </View>

          {/* Full Name & Designation */}
          <Text style={[styles.profileName, { color: tone.text1 }]}>{userName}</Text>
          <Text style={[styles.profileRole, { color: tone.text3 }]}>{roleFormatted}</Text>
        </View>

        {/* Switch Row: Show my name to institutions */}
        <View style={[styles.toggleCard, { backgroundColor: cardBg }]}>
          <Text style={[styles.toggleLabel, { color: tone.text1 }]}>
            Show my name to institutions
          </Text>
          <Switch
            value={showNameToInstitutions}
            onValueChange={setShowNameToInstitutions}
            trackColor={{ false: '#cbd5e1', true: tone.accent }}
            thumbColor="#ffffff"
          />
        </View>

        {/* Section: Main */}
        <View style={styles.sectionWrap}>
          <Text style={[styles.sectionLabel, { color: tone.text3 }]}>Main</Text>
          <View style={[styles.groupedCard, { backgroundColor: cardBg }]}>
            {/* Two-step verification */}
            <TouchableOpacity
              style={[styles.row, styles.rowBorder]}
              onPress={() => setMfaWizardVisible(true)}
            >
              <View style={styles.rowLeft}>
                <Icon name="security" size={18} color={tone.accent} />
                <Text style={[styles.rowTitle, { color: tone.text1 }]}>Two-step verification</Text>
              </View>
              <View style={styles.rowRight}>
                <Text style={[styles.rowValue, { color: tone.text3 }]}>On</Text>
                <Text style={[styles.chevron, { color: tone.text3 }]}>›</Text>
              </View>
            </TouchableOpacity>

            {/* Passkeys */}
            <TouchableOpacity
              style={[styles.row, styles.rowBorder]}
              onPress={() => showToast('Passkeys registered: 1 on current device.')}
            >
              <View style={styles.rowLeft}>
                <Icon name="biometric" size={18} color={tone.accent} />
                <Text style={[styles.rowTitle, { color: tone.text1 }]}>Passkeys</Text>
              </View>
              <View style={styles.rowRight}>
                <Text style={[styles.rowValue, { color: tone.text3 }]}>1</Text>
                <Text style={[styles.chevron, { color: tone.text3 }]}>›</Text>
              </View>
            </TouchableOpacity>

            {/* Devices and sessions */}
            <TouchableOpacity
              style={[styles.row, styles.rowBorder]}
              onPress={() => showToast('Active session authenticated via Keycloak OIDC.')}
            >
              <View style={styles.rowLeft}>
                <Icon name="devices" size={18} color={tone.accent} />
                <Text style={[styles.rowTitle, { color: tone.text1 }]}>Devices and sessions</Text>
              </View>
              <View style={styles.rowRight}>
                <Text style={[styles.chevron, { color: tone.text3 }]}>›</Text>
              </View>
            </TouchableOpacity>

            {/* Language */}
            <TouchableOpacity
              style={styles.row}
              onPress={() => showToast('Language selection: English (Statutory default).')}
            >
              <View style={styles.rowLeft}>
                <Icon name="language" size={18} color={tone.accent} />
                <Text style={[styles.rowTitle, { color: tone.text1 }]}>Language</Text>
              </View>
              <View style={styles.rowRight}>
                <Text style={[styles.rowValue, { color: tone.text3 }]}>English</Text>
                <Text style={[styles.chevron, { color: tone.text3 }]}>›</Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>

        {/* Section: Privacy Policy & Tools */}
        <View style={styles.sectionWrap}>
          <View style={[styles.groupedCard, { backgroundColor: cardBg }]}>
            {/* Ask AI Handbook Chatbot */}
            <TouchableOpacity
              style={[styles.row, styles.rowBorder]}
              onPress={onOpenChatbot}
            >
              <View style={styles.rowLeft}>
                <Icon name="chat" size={18} color={tone.accent} />
                <Text style={[styles.rowTitle, { color: tone.text1 }]}>Ask Handbook Chatbot (Kosh AI)</Text>
              </View>
              <View style={styles.rowRight}>
                <Text style={[styles.chevron, { color: tone.text3 }]}>›</Text>
              </View>
            </TouchableOpacity>

            {/* Privacy Policy */}
            <TouchableOpacity
              style={[styles.row, styles.rowBorder]}
              onPress={() => showToast('Privacy Policy: Protected under DPDP Act 2023 Section 11-13.')}
            >
              <View style={styles.rowLeft}>
                <Icon name="policy" size={18} color={tone.accent} />
                <Text style={[styles.rowTitle, { color: tone.text1 }]}>Privacy policy</Text>
              </View>
              <View style={styles.rowRight}>
                <Text style={[styles.chevron, { color: tone.text3 }]}>›</Text>
              </View>
            </TouchableOpacity>

            {/* Receipt QR Scanner */}
            <TouchableOpacity
              style={[styles.row, styles.rowBorder]}
              onPress={onOpenQRScanner}
            >
              <View style={styles.rowLeft}>
                <Icon name="qr" size={18} color={tone.accent} />
                <Text style={[styles.rowTitle, { color: tone.text1 }]}>Receipt QR scanner</Text>
              </View>
              <View style={styles.rowRight}>
                <Text style={[styles.chevron, { color: tone.text3 }]}>›</Text>
              </View>
            </TouchableOpacity>

            {/* Document Capture */}
            <TouchableOpacity
              style={[styles.row, styles.rowBorder]}
              onPress={onOpenDocCapture}
            >
              <View style={styles.rowLeft}>
                <Icon name="scan" size={18} color={tone.accent} />
                <Text style={[styles.rowTitle, { color: tone.text1 }]}>Document capture</Text>
              </View>
              <View style={styles.rowRight}>
                <Text style={[styles.chevron, { color: tone.text3 }]}>›</Text>
              </View>
            </TouchableOpacity>

            {/* Sign out */}
            <TouchableOpacity style={styles.row} onPress={onLogout}>
              <View style={styles.rowLeft}>
                <Icon name="sign_out" size={18} color="#ef4444" />
                <Text style={[styles.rowTitle, { color: '#ef4444' }]}>Sign out</Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>

      <MfaEnrolmentWizard visible={mfaWizardVisible} onClose={() => setMfaWizardVisible(false)} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  topbar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 54 : 20,
    paddingBottom: 14,
  },
  topbarLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  wordmark: {
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  topbarRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  progressMiniWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  progressTrack: {
    width: 32,
    height: 4,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 11,
    fontWeight: '700',
  },
  bellBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  rolePill: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 9999,
  },
  rolePillText: {
    fontSize: 11,
    fontWeight: '700',
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  toastBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 14,
    backgroundColor: '#ecfdf5',
    marginBottom: 16,
  },
  toastText: {
    fontSize: 12,
    color: '#065f46',
    fontWeight: '600',
  },
  profileHeader: {
    alignItems: 'center',
    paddingTop: 8,
    paddingBottom: 24,
  },
  regionChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 9999,
    backgroundColor: '#ffffff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
    marginBottom: 20,
  },
  regionChipText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
  },
  avatarXL: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  avatarXLText: {
    fontSize: 32,
    fontWeight: '800',
  },
  profileName: {
    fontSize: 20,
    fontWeight: '800',
  },
  profileRole: {
    fontSize: 13,
    marginTop: 2,
  },
  toggleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderRadius: 22,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
    marginBottom: 24,
  },
  toggleLabel: {
    fontSize: 14,
    fontWeight: '700',
  },
  sectionWrap: {
    marginBottom: 20,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 10,
  },
  groupedCard: {
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
  },
  rowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  rowTitle: {
    fontSize: 14,
    fontWeight: '600',
  },
  rowRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  rowValue: {
    fontSize: 13,
    fontWeight: '500',
  },
  chevron: {
    fontSize: 18,
    fontWeight: '400',
  },
});
