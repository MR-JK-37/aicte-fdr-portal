import React, { createContext, useCallback, useContext, useRef, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Modal, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { api } from '../lib/apiClient';

type Resolver = (ok: boolean) => void;

interface StepUpContextValue {
  /** Mirrors apps/web/src/auth/StepUpContext.tsx — see that file's doc comment.
   * Resolves true only once a real TOTP code is verified server-side. */
  requestStepUp: () => Promise<boolean>;
}

const StepUpContext = createContext<StepUpContextValue | null>(null);

export const StepUpProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { tone, isDark } = useAppTheme();
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const resolverRef = useRef<Resolver | null>(null);

  const cardBg = isDark ? tone.surface : '#ffffff';

  const requestStepUp = useCallback(() => {
    setOpen(true);
    setCode('');
    setError(null);
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
    });
  }, []);

  const close = (ok: boolean) => {
    setOpen(false);
    resolverRef.current?.(ok);
    resolverRef.current = null;
  };

  const submit = async () => {
    setBusy(true);
    setError(null);
    const { data } = await api.POST('/v1/auth/step-up', { body: { otp_code: code } });
    setBusy(false);
    if (!data) {
      setError('Invalid code — re-enter the current code from your authenticator app.');
      return;
    }
    close(true);
  };

  return (
    <StepUpContext.Provider value={{ requestStepUp }}>
      {children}
      <Modal visible={open} animationType="fade" transparent>
        <View style={styles.backdrop}>
          <View style={[styles.card, { backgroundColor: cardBg }]}>
            <View style={styles.header}>
              <Icon name="warning" size={18} color="#d97706" />
              <Text style={[styles.title, { color: tone.text1 }]}>Confirm it's you</Text>
            </View>
            <Text style={[styles.helpText, { color: tone.text3 }]}>This action needs a fresh verification code.</Text>
            {error && <Text style={styles.errorText}>{error}</Text>}
            <TextInput
              style={[
                styles.input,
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
                onPress={() => close(false)}
              >
                <Text style={[styles.secondaryButtonText, { color: tone.text2 }]}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.primaryButton,
                  { backgroundColor: isDark ? '#ffffff' : tone.ink },
                  busy && styles.disabled,
                ]}
                onPress={submit}
                disabled={busy || code.length !== 6}
              >
                <Text style={[styles.primaryButtonText, { color: isDark ? '#0f172a' : '#ffffff' }]}>
                  {busy ? 'Verifying…' : 'Verify'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </StepUpContext.Provider>
  );
};

export function useStepUp(): StepUpContextValue {
  const ctx = useContext(StepUpContext);
  if (!ctx) throw new Error('useStepUp must be used inside StepUpProvider');
  return ctx;
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.45)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  card: {
    width: '100%',
    maxWidth: 340,
    borderRadius: 20,
    padding: 20,
    shadowColor: '#1e1b4b',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 8,
  },
  header: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  title: { fontSize: 16, fontWeight: '700' },
  helpText: { fontSize: 13, marginBottom: 12 },
  errorText: { fontSize: 12, color: '#dc2626', marginBottom: 10, fontWeight: '600' },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 12,
    fontSize: 18,
    textAlign: 'center',
    letterSpacing: 4,
    marginBottom: 16,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  row: { flexDirection: 'row', gap: 10 },
  primaryButton: { flex: 1, borderRadius: 999, paddingVertical: 13, alignItems: 'center' },
  primaryButtonText: { fontWeight: '700', fontSize: 13 },
  secondaryButton: { flex: 1, borderRadius: 999, paddingVertical: 13, alignItems: 'center' },
  secondaryButtonText: { fontSize: 13, fontWeight: '600' },
  disabled: { opacity: 0.5 },
});
