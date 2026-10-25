import React, { useEffect, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Modal, ScrollView, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { api } from '../lib/apiClient';
import { useAuth } from './AuthContext';

type Step = 'loading' | 'confirm' | 'recovery-codes' | 'error';

export const MfaEnrolmentWizard: React.FC<{ visible: boolean; onClose: () => void }> = ({
  visible,
  onClose,
}) => {
  const { refresh } = useAuth();
  const { tone, isDark } = useAppTheme();
  const [step, setStep] = useState<Step>('loading');
  const [secret, setSecret] = useState('');
  const [provisioningUri, setProvisioningUri] = useState('');
  const [code, setCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const cardBg = isDark ? tone.surface : '#ffffff';

  useEffect(() => {
    if (!visible) return;
    setStep('loading');
    setCode('');
    setError(null);
    api.POST('/v1/auth/mfa/enrol/start').then(({ data }) => {
      if (!data) {
        setStep('error');
        return;
      }
      setSecret(data.secret);
      setProvisioningUri(data.provisioning_uri);
      setStep('confirm');
    });
  }, [visible]);

  const confirm = async () => {
    setBusy(true);
    setError(null);
    const { data } = await api.POST('/v1/auth/mfa/enrol/confirm', {
      body: { secret, totp_code: code },
    });
    setBusy(false);
    if (!data) {
      setError('That code did not match — check your authenticator app and try again.');
      return;
    }
    setRecoveryCodes(data.recovery_codes);
    setStep('recovery-codes');
  };

  const finish = async () => {
    await refresh();
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.backdrop}>
        <View style={[styles.sheet, { backgroundColor: cardBg }]}>
          <View style={styles.header}>
            <Icon name="security" size={20} color={tone.accent} />
            <Text style={[styles.title, { color: tone.text1 }]}>Set up two-step verification</Text>
          </View>

          {error && <Text style={styles.errorText}>{error}</Text>}

          {step === 'loading' && <Text style={[styles.helpText, { color: tone.text3 }]}>Loading…</Text>}
          {step === 'error' && <Text style={styles.errorText}>Could not start enrolment.</Text>}

          {step === 'confirm' && (
            <ScrollView>
              <Text style={[styles.helpText, { color: tone.text2 }]}>
                Add this account to your authenticator app, then enter the 6-digit code it shows.
              </Text>
              <View
                style={[
                  styles.secretBox,
                  {
                    backgroundColor: isDark ? tone.surfaceMuted : '#f8fafc',
                    borderColor: isDark ? tone.outline : '#e2e8f0',
                  },
                ]}
              >
                <Text selectable style={[styles.secretText, { color: tone.text1 }]}>
                  {secret}
                </Text>
              </View>
              <Text style={[styles.uriText, { color: tone.text3 }]} selectable>
                {provisioningUri}
              </Text>
              <TextInput
                style={[
                  styles.codeInput,
                  {
                    backgroundColor: isDark ? tone.surfaceMuted : '#f8fafc',
                    borderColor: isDark ? tone.outline : '#e2e8f0',
                    color: tone.text1,
                  },
                ]}
                value={code}
                onChangeText={(v) => setCode(v.replace(/\D/g, ''))}
                keyboardType="number-pad"
                maxLength={6}
                placeholder="000000"
                placeholderTextColor="#94a3b8"
                autoFocus
              />
              <View style={styles.row}>
                <TouchableOpacity
                  style={[styles.secondaryButton, { backgroundColor: isDark ? tone.surfaceMuted : '#f1f5f9' }]}
                  onPress={onClose}
                >
                  <Text style={[styles.secondaryButtonText, { color: tone.text2 }]}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.primaryButton,
                    { backgroundColor: isDark ? '#ffffff' : tone.ink },
                    busy && styles.disabled,
                  ]}
                  onPress={confirm}
                  disabled={busy || code.length !== 6}
                >
                  <Text style={[styles.primaryButtonText, { color: isDark ? '#0f172a' : '#ffffff' }]}>
                    {busy ? 'Verifying…' : 'Confirm'}
                  </Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          )}

          {step === 'recovery-codes' && (
            <View>
              <View style={styles.successRow}>
                <Icon name="success" size={16} color="#059669" />
                <Text style={styles.successText}>Two-step verification active</Text>
              </View>
              <Text style={[styles.helpText, { color: tone.text2 }]}>
                Save these recovery codes somewhere safe. Each code can only be used once.
              </Text>
              <View
                style={[
                  styles.codesGrid,
                  {
                    backgroundColor: isDark ? tone.surfaceMuted : '#f8fafc',
                    borderColor: isDark ? tone.outline : '#e2e8f0',
                  },
                ]}
              >
                {recoveryCodes.map((rc, idx) => (
                  <Text key={idx} style={[styles.codeText, { color: tone.text1 }]} selectable>
                    {rc}
                  </Text>
                ))}
              </View>
              <TouchableOpacity
                style={[styles.primaryButton, { backgroundColor: isDark ? '#ffffff' : tone.ink }]}
                onPress={finish}
              >
                <Text style={[styles.primaryButtonText, { color: isDark ? '#0f172a' : '#ffffff' }]}>
                  Done
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(15, 23, 42, 0.45)', justifyContent: 'flex-end' },
  sheet: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    maxHeight: '85%',
    shadowColor: '#1e1b4b',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 10,
  },
  header: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  title: { fontSize: 16, fontWeight: '700' },
  helpText: { fontSize: 13, marginBottom: 12, lineHeight: 18 },
  errorText: { fontSize: 12, color: '#dc2626', marginBottom: 12, fontWeight: '600' },
  secretBox: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  secretText: { fontSize: 13, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace', fontWeight: '600' },
  uriText: { fontSize: 10, marginBottom: 14 },
  codeInput: {
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 12,
    fontSize: 18,
    textAlign: 'center',
    letterSpacing: 4,
    marginBottom: 14,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  row: { flexDirection: 'row', gap: 10 },
  primaryButton: { flex: 1, borderRadius: 999, paddingVertical: 14, alignItems: 'center' },
  primaryButtonText: { fontWeight: '700', fontSize: 13 },
  secondaryButton: { flex: 1, borderRadius: 999, paddingVertical: 14, alignItems: 'center' },
  secondaryButtonText: { fontSize: 13, fontWeight: '600' },
  disabled: { opacity: 0.5 },
  successRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 },
  successText: { color: '#059669', fontSize: 14, fontWeight: '700' },
  codesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },
  codeText: { fontSize: 12, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace', width: '45%' },
});
