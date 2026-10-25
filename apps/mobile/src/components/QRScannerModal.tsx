import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Modal, TextInput, ActivityIndicator, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { api } from '../lib/apiClient';

interface QRScannerModalProps {
  visible: boolean;
  onClose: () => void;
  onVerifyReceipt?: (receiptNumber: string) => void;
}

interface VerificationSuccess {
  verified: boolean;
  receipt_id: string;
  institution_code: string;
  version_number: number;
  version_hash_prefix: string;
  issued_at: string;
  message: string;
}

export const QRScannerModal: React.FC<QRScannerModalProps> = ({ visible, onClose, onVerifyReceipt }) => {
  const { tone, isDark } = useAppTheme();
  const [manualCode, setManualCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<VerificationSuccess | null>(null);

  const cardBg = isDark ? tone.surface : '#ffffff';

  const handleVerify = async () => {
    if (!manualCode.trim()) return;
    setLoading(true);
    setErrorMessage(null);

    try {
      let queryParams: Record<string, string> = {};
      if (manualCode.includes('?')) {
        const queryStr = manualCode.split('?')[1];
        const searchParams = new URLSearchParams(queryStr);
        searchParams.forEach((val, key) => {
          queryParams[key] = val;
        });
      }

      if (!queryParams.rid || !queryParams.sig) {
        setErrorMessage(
          'Cryptographic verification requires the complete QR verification payload (parameters: rid, iid, inst, ver, h, ts, sig) as generated on official AICTE receipts.'
        );
        setLoading(false);
        return;
      }

      const { data, error } = await api.GET('/v1/public/receipts/verify', {
        params: {
          query: {
            rid: queryParams.rid,
            iid: queryParams.iid || '',
            inst: queryParams.inst || '',
            ver: parseInt(queryParams.ver || '1', 10),
            h: queryParams.h || '',
            ts: queryParams.ts || '',
            sig: queryParams.sig,
          },
        },
      });

      setLoading(false);

      if (error || !data) {
        setErrorMessage('Verification failed. The cryptographic signature did not match the ledger or payload.');
        return;
      }

      const res: VerificationSuccess = {
        verified: data.verified,
        receipt_id: data.receipt_id,
        institution_code: data.institution_code,
        version_number: data.version_number,
        version_hash_prefix: data.version_hash_prefix,
        issued_at: data.issued_at,
        message: data.message,
      };

      setScanResult(res);
      if (onVerifyReceipt) onVerifyReceipt(data.receipt_id);
    } catch {
      setLoading(false);
      setErrorMessage('Network or server error during cryptographic verification.');
    }
  };

  const handleReset = () => {
    setScanResult(null);
    setManualCode('');
    setErrorMessage(null);
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={false}>
      <View style={[styles.container, { backgroundColor: tone.bg }]}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => {
              handleReset();
              onClose();
            }}
            style={styles.closeBtn}
          >
            <Text style={[styles.closeBtnText, { color: tone.accent }]}>Close</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: tone.text1 }]}>Verify Receipt QR (M-09)</Text>
          <View style={{ width: 40 }} />
        </View>

        {!scanResult ? (
          <View style={styles.body}>
            {/* Viewfinder Frame / Camera Frame */}
            <View style={[styles.viewfinder, { backgroundColor: isDark ? 'rgba(0,0,0,0.5)' : '#f8fafc', borderColor: tone.outline }]}>
              <View style={[styles.corner, styles.cornerTL, { borderColor: tone.accent }]} />
              <View style={[styles.corner, styles.cornerTR, { borderColor: tone.accent }]} />
              <View style={[styles.corner, styles.cornerBL, { borderColor: tone.accent }]} />
              <View style={[styles.corner, styles.cornerBR, { borderColor: tone.accent }]} />

              <Icon name="scan" size={48} color={tone.accent} />
              <Text style={[styles.reticleText, { color: tone.text3 }]}>
                Point camera at signed AICTE QR code or enter raw payload below
              </Text>
            </View>

            {/* Manual Payload / URL Input Fallback */}
            <View style={styles.manualEntry}>
              <Text style={[styles.manualLabel, { color: tone.text2 }]}>Paste Signed Verification URL or Payload:</Text>
              <TextInput
                value={manualCode}
                onChangeText={setManualCode}
                placeholder="https://fdr.aicte-india.org/verify?rid=...&sig=..."
                placeholderTextColor="#94a3b8"
                style={[
                  styles.textInput,
                  {
                    backgroundColor: cardBg,
                    borderColor: isDark ? tone.outline : '#e2e8f0',
                    color: tone.text1,
                  },
                ]}
                multiline
                numberOfLines={3}
              />

              {errorMessage && (
                <View style={styles.errorBox}>
                  <Text style={styles.errorText}>{errorMessage}</Text>
                </View>
              )}

              <TouchableOpacity
                style={[styles.scanButton, { backgroundColor: isDark ? '#ffffff' : tone.ink }]}
                onPress={handleVerify}
                disabled={loading || !manualCode.trim()}
              >
                {loading ? (
                  <ActivityIndicator color={isDark ? '#0f172a' : '#ffffff'} size="small" />
                ) : (
                  <>
                    <Icon name="verified" size={16} color={isDark ? '#0f172a' : '#ffffff'} />
                    <Text style={[styles.scanButtonText, { color: isDark ? '#0f172a' : '#ffffff' }]}>
                      Verify Cryptographic Signature
                    </Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <View style={styles.resultContainer}>
            <View style={styles.successBadge}>
              <Icon name="success" size={54} color="#059669" />
              <Text style={styles.successTitle}>SIGNATURE VALID</Text>
              <Text style={[styles.successSubtitle, { color: tone.text3 }]}>
                Ed25519 signature cryptographically verified against AICTE Bureau Root
              </Text>
            </View>

            <View style={[styles.cardDetails, { backgroundColor: cardBg }]}>
              <View style={styles.detailRow}>
                <Text style={[styles.detailLabel, { color: tone.text3 }]}>Receipt Ref ID</Text>
                <Text style={[styles.detailValueMono, { color: tone.accent }]}>{scanResult.receipt_id}</Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={[styles.detailLabel, { color: tone.text3 }]}>Institution Code</Text>
                <Text style={[styles.detailValue, { color: tone.text1 }]}>{scanResult.institution_code}</Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={[styles.detailLabel, { color: tone.text3 }]}>Format Version</Text>
                <Text style={[styles.detailValue, { color: tone.text1 }]}>v{scanResult.version_number}</Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={[styles.detailLabel, { color: tone.text3 }]}>Integrity Hash Prefix</Text>
                <Text style={[styles.detailValueMono, { color: tone.accent }]}>
                  {scanResult.version_hash_prefix}
                </Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={[styles.detailLabel, { color: tone.text3 }]}>Issued Timestamp</Text>
                <Text style={[styles.detailValue, { color: tone.text1 }]}>{scanResult.issued_at}</Text>
              </View>
            </View>

            <TouchableOpacity
              style={[styles.scanAgainBtn, { backgroundColor: tone.accentContainer }]}
              onPress={handleReset}
            >
              <Text style={[styles.scanAgainText, { color: tone.accent }]}>Scan Another Receipt</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: tone.text3 }]}>
            Parity with F-17/F-28 • Offline validation uses verified local public keys per M-09.
          </Text>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 48 : 24,
    paddingBottom: 24,
    justifyContent: 'space-between',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  closeBtn: {
    padding: 8,
  },
  closeBtnText: {
    fontSize: 15,
    fontWeight: '700',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  body: {
    alignItems: 'center',
    gap: 20,
  },
  viewfinder: {
    width: 240,
    height: 240,
    borderWidth: 1,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 20,
    height: 20,
  },
  cornerTL: {
    top: -2,
    left: -2,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderTopLeftRadius: 8,
  },
  cornerTR: {
    top: -2,
    right: -2,
    borderTopWidth: 3,
    borderRightWidth: 3,
    borderTopRightRadius: 8,
  },
  cornerBL: {
    bottom: -2,
    left: -2,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
    borderBottomLeftRadius: 8,
  },
  cornerBR: {
    bottom: -2,
    right: -2,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderBottomRightRadius: 8,
  },
  reticleText: {
    fontSize: 11,
    textAlign: 'center',
    marginTop: 12,
    paddingHorizontal: 16,
    lineHeight: 16,
  },
  manualEntry: {
    width: '100%',
    gap: 10,
  },
  manualLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 13,
  },
  errorBox: {
    padding: 10,
    borderRadius: 8,
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
  },
  errorText: {
    color: '#dc2626',
    fontSize: 12,
    fontWeight: '500',
  },
  scanButton: {
    borderRadius: 999,
    paddingVertical: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  scanButtonText: {
    fontSize: 13,
    fontWeight: '700',
  },
  resultContainer: {
    alignItems: 'center',
    gap: 20,
  },
  successBadge: {
    alignItems: 'center',
    gap: 8,
  },
  successTitle: {
    color: '#059669',
    fontSize: 18,
    fontWeight: '800',
    letterSpacing: 1,
  },
  successSubtitle: {
    fontSize: 12,
    textAlign: 'center',
    paddingHorizontal: 16,
  },
  cardDetails: {
    width: '100%',
    borderRadius: 20,
    padding: 16,
    gap: 12,
    shadowColor: '#1e1b4b',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 3,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  detailValue: {
    fontSize: 13,
    fontWeight: '600',
  },
  detailValueMono: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontWeight: '600',
  },
  scanAgainBtn: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 999,
  },
  scanAgainText: {
    fontSize: 13,
    fontWeight: '700',
  },
  footer: {
    alignItems: 'center',
  },
  footerText: {
    fontSize: 11,
    textAlign: 'center',
    lineHeight: 16,
  },
});
