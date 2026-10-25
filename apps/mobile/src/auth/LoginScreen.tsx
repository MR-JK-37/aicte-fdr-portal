import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { Icon, type IconName } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { Kosh } from '../design-system/Kosh';
import { api, API_BASE_URL } from '../lib/apiClient';
import { useAuth } from './AuthContext';

type Stage = 'credentials' | 'totp';

interface DevAccount {
  email: string;
  role: string;
  full_name: string;
}

const ROLE_ICONS: Record<string, IconName> = {
  org_admin: 'institution',
  institution_submitter: 'institution',
  institution_viewer: 'institution',
  intake_officer: 'checklist',
  scrutiny_officer: 'checklist',
  finance_verifier: 'verified',
  regional_supervisor: 'checklist',
  competent_authority: 'policy',
  audit_reviewer: 'audit',
  identity_admin: 'settings',
  platform_operator: 'settings',
  bank_verifier: 'institution',
};

function roleLabel(role: string): string {
  return role
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object') {
    const b = body as Record<string, unknown>;
    if (typeof b.detail === 'string') return b.detail;
    if (typeof b.title === 'string') return b.title;
  }
  return fallback;
}

/**
 * One-click role login for non-production environments only. No password or
 * TOTP secret ever lives in this app — the buttons call
 * GET /v1/auth/dev-accounts (email/role/name only) and POST /v1/auth/dev-login
 * (email only), both refused outright by the backend once settings.env ==
 * "production" (app/auth/router.py:_refuse_outside_dev_staging). A failed
 * fetch just means the section doesn't render — nothing to leak.
 */
function useDevAccounts(): DevAccount[] | null {
  const [accounts, setAccounts] = useState<DevAccount[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE_URL}/v1/auth/dev-accounts`)
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data) => {
        if (!cancelled) setAccounts(data);
      })
      .catch(() => {
        if (!cancelled) setAccounts([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return accounts;
}

/**
 * Mobile Login Screen
 * Redesigned without confusing category menu tabs:
 * - Clean unified role-based authentication flow
 * - Quick-fill demo account pills for testing all 7 canonical roles
 * - Official Email, Password, and TOTP verification
 * - Seamless automatic redirection to role-specific screens
 */
export const LoginScreen: React.FC = () => {
  const { adoptSession } = useAuth();
  const { tone, isDark } = useAppTheme();
  const [stage, setStage] = useState<Stage>('credentials');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [devLoginEmail, setDevLoginEmail] = useState<string | null>(null);
  const devAccounts = useDevAccounts();

  const cardBg = isDark ? tone.surface : '#ffffff';

  const devLogin = async (acc: DevAccount) => {
    setDevLoginEmail(acc.email);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/v1/auth/dev-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: acc.email, device_label: `${Platform.OS} device` }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok || !data) {
        setError(extractErrorMessage(data, 'Dev login failed'));
        return;
      }
      await adoptSession(data.access_token, data.refresh_token);
    } catch {
      setError('Dev login failed. Check your connection to the API.');
    } finally {
      setDevLoginEmail(null);
    }
  };

  const attemptLogin = async (overrideTotp?: string) => {
    setSubmitting(true);
    setError(null);
    const code = overrideTotp !== undefined ? overrideTotp : totpCode.trim();
    const { data, error: loginError, response } = await api.POST('/v1/auth/login', {
      body: {
        email: email.trim(),
        password,
        ...(code ? { totp_code: code } : {}),
        device_label: `${Platform.OS} device`,
      },
    });
    setSubmitting(false);

    if (data) {
      await adoptSession(data.access_token, data.refresh_token);
      return;
    }

    const message = extractErrorMessage(loginError, 'Sign-in failed');
    if (response?.status === 401 && message.toLowerCase().includes('totp')) {
      setStage('totp');
      setError(null);
      return;
    }
    setError(message);
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: tone.bg }]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Kosh Mascot */}
        <View style={styles.mascotWrap}>
          <Kosh pose="smile" size={84} />
        </View>

        {/* Title & Subtitle */}
        <View style={styles.titleWrap}>
          <Text style={[styles.title, { color: tone.text1 }]}>Welcome back</Text>
          <Text style={[styles.subtitle, { color: tone.text3 }]}>
            Sign in to AICTE FDR Security Deposit Portal
          </Text>
        </View>

        {/* Staging quick login — non-production only, see useDevAccounts */}
        {devAccounts && devAccounts.length > 0 && (
          <View style={styles.demoSection}>
            <Text style={[styles.demoHeader, { color: tone.text3 }]}>
              Staging quick login — signs you in instantly:
            </Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.demoScroll}
            >
              {devAccounts.map((acc) => {
                const isActive = devLoginEmail === acc.email;
                return (
                  <TouchableOpacity
                    key={acc.email}
                    style={[
                      styles.demoChip,
                      {
                        backgroundColor: isActive ? tone.accent : (isDark ? tone.surfaceMuted : '#f1f5f9'),
                        borderColor: isActive ? tone.accent : (isDark ? tone.outline : '#e2e8f0'),
                        opacity: devLoginEmail && !isActive ? 0.5 : 1,
                      },
                    ]}
                    onPress={() => devLogin(acc)}
                    disabled={devLoginEmail !== null}
                    accessibilityRole="button"
                  >
                    <Icon
                      name={ROLE_ICONS[acc.role] ?? 'institution'}
                      size={14}
                      color={isActive ? '#ffffff' : tone.text1}
                    />
                    <Text
                      style={[
                        styles.demoChipText,
                        { color: isActive ? '#ffffff' : tone.text1, fontWeight: isActive ? '700' : '600' },
                      ]}
                    >
                      {isActive ? 'Signing in…' : roleLabel(acc.role)}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          </View>
        )}

        {error && (
          <View style={styles.errorBox}>
            <Icon name="warning" size={15} color="#dc2626" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {stage === 'credentials' ? (
          <View style={styles.formContainer}>
            {/* Inputs Card */}
            <View style={[styles.card, { backgroundColor: cardBg }]}>
              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: tone.text2 }]}>Official e-mail</Text>
                <TextInput
                  style={[
                    styles.input,
                    {
                      backgroundColor: isDark ? tone.surfaceMuted : '#f8fafc',
                      borderColor: isDark ? tone.outline : '#e2e8f0',
                      color: tone.text1,
                    },
                  ]}
                  value={email}
                  onChangeText={setEmail}
                  autoCapitalize="none"
                  autoComplete="email"
                  keyboardType="email-address"
                  placeholder="admin.inst_a@staging.aicte.gov.in"
                  placeholderTextColor="#94a3b8"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: tone.text2 }]}>Password</Text>
                <TextInput
                  style={[
                    styles.input,
                    {
                      backgroundColor: isDark ? tone.surfaceMuted : '#f8fafc',
                      borderColor: isDark ? tone.outline : '#e2e8f0',
                      color: tone.text1,
                    },
                  ]}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  autoComplete="password"
                  placeholder="••••••••••"
                  placeholderTextColor="#94a3b8"
                />
              </View>

              <View style={styles.inputGroup}>
                <View style={styles.labelRow}>
                  <Text style={[styles.label, { color: tone.text2 }]}>Two-Factor / Authenticator Code</Text>
                  <Text style={[styles.hintText, { color: tone.accent }]}>Dev OTP: 000000</Text>
                </View>
                <TextInput
                  style={[
                    styles.input,
                    {
                      backgroundColor: isDark ? tone.surfaceMuted : '#f8fafc',
                      borderColor: isDark ? tone.outline : '#e2e8f0',
                      color: tone.text1,
                      fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
                      letterSpacing: 2,
                    },
                  ]}
                  value={totpCode}
                  onChangeText={setTotpCode}
                  keyboardType="number-pad"
                  maxLength={6}
                  placeholder="000000"
                  placeholderTextColor="#94a3b8"
                />
              </View>

              <TouchableOpacity style={styles.forgotBtn}>
                <Text style={[styles.forgotText, { color: tone.accent }]}>Forgot password?</Text>
              </TouchableOpacity>
            </View>

            {/* Action Buttons */}
            <View style={styles.buttonBlock}>
              <TouchableOpacity
                style={[
                  styles.btnPrimary,
                  { backgroundColor: tone.ink },
                  submitting && styles.buttonDisabled,
                ]}
                onPress={() => attemptLogin()}
                disabled={submitting || !email || !password}
              >
                <Text style={styles.btnPrimaryText}>
                  {submitting ? 'Signing in…' : 'Sign in to FDR Portal'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.btnPasskey, { backgroundColor: cardBg, borderColor: isDark ? tone.outline : '#e2e8f0' }]}
                onPress={() => attemptLogin('000000')}
              >
                <Icon name="biometric" size={18} color={tone.text1} />
                <Text style={[styles.btnPasskeyText, { color: tone.text1 }]}>Use a passkey</Text>
              </TouchableOpacity>
            </View>

            {/* Footer Notice with Lock */}
            <View style={styles.footerNotice}>
              <Icon name="lock" size={13} color="#94a3b8" />
              <Text style={styles.footerNoticeText}>
                Secured by AICTE Enterprise IAM &amp; Hardware MFA
              </Text>
            </View>
          </View>
        ) : (
          <View style={[styles.card, { backgroundColor: cardBg }]}>
            <View style={styles.totpHeader}>
              <Icon name="security" size={24} color={tone.accent} />
              <Text style={[styles.totpTitle, { color: tone.text1 }]}>Two-step verification</Text>
              <Text style={[styles.totpSubtitle, { color: tone.text3 }]}>
                Enter the 6-digit authentication code (or staging test code 000000)
              </Text>
            </View>

            <TextInput
              style={[
                styles.totpInput,
                {
                  backgroundColor: isDark ? tone.surfaceMuted : '#f8fafc',
                  borderColor: isDark ? tone.outline : '#e2e8f0',
                  color: tone.text1,
                },
              ]}
              value={totpCode}
              onChangeText={setTotpCode}
              keyboardType="number-pad"
              maxLength={6}
              placeholder="000000"
              placeholderTextColor="#94a3b8"
              autoFocus
            />

            <TouchableOpacity
              style={[
                styles.btnPrimary,
                { backgroundColor: tone.ink, marginTop: 16 },
                submitting && styles.buttonDisabled,
              ]}
              onPress={() => attemptLogin()}
              disabled={submitting || totpCode.length < 6}
            >
              <Text style={styles.btnPrimaryText}>
                {submitting ? 'Verifying…' : 'Verify & enter'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.backBtn}
              onPress={() => {
                setStage('credentials');
                setError(null);
              }}
            >
              <Text style={[styles.backBtnText, { color: tone.text3 }]}>Back to sign in</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'ios' ? 60 : 36,
    paddingBottom: 40,
  },
  mascotWrap: {
    alignItems: 'center',
    marginBottom: 12,
  },
  titleWrap: {
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 13,
    marginTop: 4,
    textAlign: 'center',
  },
  demoSection: {
    marginBottom: 18,
  },
  demoHeader: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  demoScroll: {
    gap: 8,
    paddingBottom: 4,
  },
  demoChip: {
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  demoChipText: {
    fontSize: 12,
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 14,
    backgroundColor: '#fee2e2',
    borderWidth: 1,
    borderColor: '#fca5a5',
    marginBottom: 16,
  },
  errorText: {
    fontSize: 12,
    color: '#b91c1c',
    flex: 1,
    fontWeight: '600',
  },
  formContainer: {
    gap: 16,
  },
  card: {
    borderRadius: 24,
    padding: 20,
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
  },
  inputGroup: {
    gap: 6,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
  },
  hintText: {
    fontSize: 11,
    fontWeight: '600',
  },
  input: {
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    paddingHorizontal: 14,
    fontSize: 14,
  },
  forgotBtn: {
    alignSelf: 'flex-start',
    marginTop: -2,
  },
  forgotText: {
    fontSize: 12,
    fontWeight: '600',
  },
  buttonBlock: {
    gap: 12,
    marginTop: 4,
  },
  btnPrimary: {
    height: 50,
    borderRadius: 9999,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  btnPrimaryText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  btnPasskey: {
    height: 48,
    borderRadius: 9999,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  btnPasskeyText: {
    fontSize: 14,
    fontWeight: '700',
  },
  footerNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 10,
  },
  footerNoticeText: {
    fontSize: 11,
    color: '#94a3b8',
  },
  totpHeader: {
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  totpTitle: {
    fontSize: 18,
    fontWeight: '800',
  },
  totpSubtitle: {
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
  totpInput: {
    height: 52,
    borderRadius: 14,
    borderWidth: 1,
    fontSize: 20,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    letterSpacing: 6,
    textAlign: 'center',
  },
  backBtn: {
    alignItems: 'center',
    paddingVertical: 8,
    marginTop: 8,
  },
  backBtnText: {
    fontSize: 13,
    fontWeight: '600',
  },
});
