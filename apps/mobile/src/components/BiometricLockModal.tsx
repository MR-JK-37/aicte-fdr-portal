import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Modal, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';

interface BiometricLockModalProps {
  visible: boolean;
  onUnlock: () => void;
  institutionName?: string;
}

export const BiometricLockModal: React.FC<BiometricLockModalProps> = ({ visible, onUnlock, institutionName = 'AICTE Signatory' }) => {
  const [pin, setPin] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleKeyPress = (digit: string) => {
    if (pin.length < 4) {
      const nextPin = pin + digit;
      setPin(nextPin);
      if (nextPin.length === 4) {
        if (nextPin === '1234') {
          setErrorMsg(null);
          setPin('');
          onUnlock();
        } else {
          setErrorMsg('Invalid Security PIN. Try 1234');
          setTimeout(() => {
            setPin('');
            setErrorMsg(null);
          }, 1000);
        }
      }
    }
  };

  const handleBiometricSimulate = () => {
    // Face ID / Android Biometric instant prompt
    onUnlock();
  };

  return (
    <Modal visible={visible} animationType="fade" transparent={false}>
      <View style={styles.container}>
        <View style={styles.header}>
          <View style={styles.shieldBadge}>
            <Icon name="security" size={32} color="#00eeff" />
          </View>
          <Text style={styles.title}>AICTE FDR Portal</Text>
          <Text style={styles.subtitle}>Biometric Security Lock (M-03)</Text>
          <Text style={styles.orgText}>{institutionName}</Text>
        </View>

        {/* Biometric Instant Action Button */}
        <TouchableOpacity style={styles.bioButton} onPress={handleBiometricSimulate}>
          <Icon name="biometric" size={36} color="#00eeff" />
          <Text style={styles.bioButtonText}>
            {Platform.OS === 'ios' ? 'Unlock with Face ID' : 'Unlock with Fingerprint'}
          </Text>
        </TouchableOpacity>

        <Text style={styles.orText}>— OR ENTER 4-DIGIT PIN (DEMO: 1234) —</Text>

        {/* PIN Indicators */}
        <View style={styles.pinDotsRow}>
          {[0, 1, 2, 3].map((i) => (
            <View
              key={i}
              style={[styles.pinDot, pin.length > i && styles.pinDotFilled, errorMsg && styles.pinDotError]}
            />
          ))}
        </View>

        {errorMsg && <Text style={styles.errorText}>{errorMsg}</Text>}

        {/* Numeric Keypad */}
        <View style={styles.keypad}>
          {['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', 'DEL'].map((val, idx) => {
            if (val === '') return <View key={idx} style={styles.keypadKey} />;
            return (
              <TouchableOpacity
                key={idx}
                style={styles.keypadKey}
                onPress={() => (val === 'DEL' ? setPin(pin.slice(0, -1)) : handleKeyPress(val))}
              >
                <Text style={styles.keypadText}>{val}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerNotice}>
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
    backgroundColor: '#050505',
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
    backgroundColor: '#151316',
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#00eeff',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: 4,
  },
  orgText: {
    fontSize: 13,
    color: '#94a3b8',
    marginTop: 6,
  },
  bioButton: {
    alignSelf: 'center',
    backgroundColor: 'rgba(0, 238, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.4)',
    borderRadius: 20,
    paddingVertical: 14,
    paddingHorizontal: 28,
    alignItems: 'center',
    gap: 8,
  },
  bioButtonText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  orText: {
    textAlign: 'center',
    fontSize: 11,
    fontWeight: '700',
    color: '#64748b',
    letterSpacing: 1,
  },
  pinDotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 18,
    marginVertical: 10,
  },
  pinDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 1.5,
    borderColor: '#475569',
    backgroundColor: 'transparent',
  },
  pinDotFilled: {
    backgroundColor: '#00eeff',
    borderColor: '#00eeff',
  },
  pinDotError: {
    backgroundColor: '#ef4444',
    borderColor: '#ef4444',
  },
  errorText: {
    color: '#f87171',
    textAlign: 'center',
    fontSize: 12,
    fontWeight: '600',
  },
  keypad: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    maxWidth: 280,
    alignSelf: 'center',
    gap: 12,
  },
  keypadKey: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#151316',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  keypadText: {
    color: '#f8fafc',
    fontSize: 22,
    fontWeight: '600',
  },
  footer: {
    alignItems: 'center',
  },
  footerNotice: {
    color: '#64748b',
    fontSize: 10,
    textAlign: 'center',
    lineHeight: 14,
  },
});
