import React from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Modal } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';

interface BiometricLockModalProps {
  visible: boolean;
  onUnlock: () => void;
  institutionName?: string;
}

export const BiometricLockModal: React.FC<BiometricLockModalProps> = ({
  visible,
  onUnlock,
  institutionName = 'AICTE Signatory',
}) => {
  const { tone, isDark } = useAppTheme();
  const cardBg = isDark ? tone.surface : '#ffffff';

  // Real Face ID / fingerprint / PIN unlock (expo-local-authentication) is not wired yet —
  // tracked for stream R6 (M-03). This never fakes a biometric check that didn't happen.
  return (
    <Modal visible={visible} animationType="fade" transparent={false}>
      <View style={[styles.container, { backgroundColor: tone.bg }]}>
        <View style={styles.header}>
          <View style={[styles.shieldBadge, { backgroundColor: cardBg }]}>
            <Icon name="security" size={32} color={tone.accent} />
          </View>
          <Text style={[styles.title, { color: tone.text1 }]}>AICTE FDR Portal</Text>
          <Text style={[styles.subtitle, { color: tone.accent }]}>App Lock</Text>
          <Text style={[styles.orgText, { color: tone.text3 }]}>{institutionName}</Text>
        </View>

        <View style={[styles.notConfiguredBox, { backgroundColor: cardBg }]}>
          <Text style={[styles.notConfiguredText, { color: tone.text2 }]}>
            Biometric / PIN app lock is not implemented yet (stream R6, M-03). This screen never
            fakes a successful unlock check.
          </Text>
        </View>

        <TouchableOpacity
          style={[styles.bioButton, { backgroundColor: isDark ? '#ffffff' : tone.ink }]}
          onPress={onUnlock}
        >
          <Text style={[styles.bioButtonText, { color: isDark ? '#0f172a' : '#ffffff' }]}>Dismiss</Text>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={[styles.footerNotice, { color: tone.text3 }]}>
            Statutory confidentiality under DPDP Act 2023. Does not replace step-up MFA for release decisions.
          </Text>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'space-between',
    paddingVertical: 48,
  },
  header: {
    alignItems: 'center',
    marginTop: 20,
  },
  shieldBadge: {
    width: 64,
    height: 64,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: '#1e1b4b',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 3,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: 4,
  },
  orgText: {
    fontSize: 13,
    marginTop: 6,
  },
  notConfiguredBox: {
    marginHorizontal: 8,
    padding: 20,
    borderRadius: 18,
    shadowColor: '#1e1b4b',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  notConfiguredText: {
    fontSize: 13,
    lineHeight: 20,
    textAlign: 'center',
  },
  bioButton: {
    alignSelf: 'center',
    borderRadius: 999,
    paddingVertical: 14,
    paddingHorizontal: 36,
    alignItems: 'center',
  },
  bioButtonText: {
    fontSize: 14,
    fontWeight: '700',
  },
  footer: {
    alignItems: 'center',
  },
  footerNotice: {
    fontSize: 11,
    textAlign: 'center',
    lineHeight: 16,
  },
});
