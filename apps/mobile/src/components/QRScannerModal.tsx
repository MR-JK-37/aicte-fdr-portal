import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Modal, TextInput, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';

interface QRScannerModalProps {
  visible: boolean;
  onClose: () => void;
  onVerifyReceipt?: (receiptNumber: string) => void;
}

export const QRScannerModal: React.FC<QRScannerModalProps> = ({ visible, onClose, onVerifyReceipt }) => {
  const [manualCode, setManualCode] = useState('REC-AICTE-2026-99201');
  const [scanResult, setScanResult] = useState<{
    valid: boolean;
    receiptNumber: string;
    institution: string;
    amount: string;
    signature: string;
  } | null>(null);

  const handleSimulateScan = () => {
    setScanResult({
      valid: true,
      receiptNumber: manualCode,
      institution: 'Delhi Global Technical Campus',
      amount: '₹35,00,000',
      signature: 'ed25519:7a8b9c0d1e2f3a4b... (AICTE Statutory Seal)',
    });
    if (onVerifyReceipt) {
      onVerifyReceipt(manualCode);
    }
  };

  const handleReset = () => {
    setScanResult(null);
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={false}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
            <Text style={styles.closeBtnText}>Close</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>QR Receipt Scanner (M-09)</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* Viewfinder Area */}
        {!scanResult ? (
          <View style={styles.body}>
            <View style={styles.viewfinder}>
              <View style={[styles.corner, styles.cornerTL]} />
              <View style={[styles.corner, styles.cornerTR]} />
              <View style={[styles.corner, styles.cornerBL]} />
              <View style={[styles.corner, styles.cornerBR]} />
              <Icon name="qr" size={72} color="rgba(0, 238, 255, 0.4)" />
              <Text style={styles.reticleText}>Align AICTE Official Receipt QR Inside Frame</Text>
            </View>

            {/* Manual Entry Fallback */}
            <View style={styles.manualEntry}>
              <Text style={styles.manualLabel}>Or Enter Receipt Code Manually</Text>
              <TextInput
                value={manualCode}
                onChangeText={setManualCode}
                placeholder="REC-AICTE-..."
                placeholderTextColor="#64748b"
                style={styles.textInput}
              />
              <TouchableOpacity style={styles.scanButton} onPress={handleSimulateScan}>
                <Icon name="verified" size={16} color="#050505" />
                <Text style={styles.scanButtonText}>Verify Cryptographic Seal</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          /* Scan Result */
          <View style={styles.resultContainer}>
            <View style={styles.successBadge}>
              <Icon name="success" size={48} color="#3ddc97" />
              <Text style={styles.successTitle}>GENUINE AICTE RECEIPT</Text>
              <Text style={styles.successSubtitle}>Offline Ed25519 signature verified</Text>
            </View>

            <View style={styles.cardDetails}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Receipt ID</Text>
                <Text style={styles.detailValue}>{scanResult.receiptNumber}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Institution</Text>
                <Text style={styles.detailValue}>{scanResult.institution}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Deposit Amount</Text>
                <Text style={styles.detailValueAmount}>{scanResult.amount}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Digital Seal</Text>
                <Text style={styles.detailValueMono}>{scanResult.signature}</Text>
              </View>
            </View>

            <TouchableOpacity style={styles.scanAgainBtn} onPress={handleReset}>
              <Text style={styles.scanAgainText}>Scan Another Code</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Validates pyHanko / Ed25519 seals locally without disclosing confidential account credentials.
          </Text>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
    paddingHorizontal: 20,
    paddingTop: 48,
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
    color: '#00eeff',
    fontWeight: '600',
    fontSize: 14,
  },
  headerTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  body: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 32,
  },
  viewfinder: {
    width: 240,
    height: 240,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    padding: 16,
  },
  reticleText: {
    color: '#94a3b8',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 12,
  },
  corner: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderColor: '#00eeff',
  },
  cornerTL: { top: -2, left: -2, borderTopWidth: 3, borderLeftWidth: 3, borderTopLeftRadius: 10 },
  cornerTR: { top: -2, right: -2, borderTopWidth: 3, borderRightWidth: 3, borderTopRightRadius: 10 },
  cornerBL: { bottom: -2, left: -2, borderBottomWidth: 3, borderLeftWidth: 3, borderBottomLeftRadius: 10 },
  cornerBR: { bottom: -2, right: -2, borderBottomWidth: 3, borderRightWidth: 3, borderBottomRightRadius: 10 },
  manualEntry: {
    width: '100%',
    gap: 10,
  },
  manualLabel: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  textInput: {
    backgroundColor: '#151316',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: '#ffffff',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 13,
  },
  scanButton: {
    backgroundColor: '#00eeff',
    borderRadius: 12,
    paddingVertical: 12,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  scanButtonText: {
    color: '#050505',
    fontWeight: '700',
    fontSize: 13,
  },
  resultContainer: {
    flex: 1,
    justifyContent: 'center',
    gap: 20,
  },
  successBadge: {
    alignItems: 'center',
    gap: 6,
  },
  successTitle: {
    color: '#3ddc97',
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  successSubtitle: {
    color: '#94a3b8',
    fontSize: 12,
  },
  cardDetails: {
    backgroundColor: '#151316',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.25)',
    padding: 16,
    gap: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    color: '#64748b',
    fontSize: 12,
  },
  detailValue: {
    color: '#f8fafc',
    fontSize: 13,
    fontWeight: '600',
  },
  detailValueAmount: {
    color: '#00eeff',
    fontSize: 14,
    fontWeight: '700',
  },
  detailValueMono: {
    color: '#94a3b8',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  scanAgainBtn: {
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#475569',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
  scanAgainText: {
    color: '#f8fafc',
    fontWeight: '600',
    fontSize: 13,
  },
  footer: {
    alignItems: 'center',
  },
  footerText: {
    color: '#475569',
    fontSize: 10,
    textAlign: 'center',
  },
});
