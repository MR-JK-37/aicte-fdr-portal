import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
  StatusBar,
} from 'react-native';

export default function App() {
  const [callActive, setCallActive] = useState(false);
  const [pin, setPin] = useState('');
  const [pinVerified, setPinVerified] = useState(false);
  const [attempts, setAttempts] = useState(3);
  const [acknowledged, setAcknowledged] = useState(false);

  const handleKeyPress = (num: string) => {
    if (pin.length < 4) {
      const next = pin + num;
      setPin(next);
      if (next.length === 4) {
        if (next === '1234') {
          setPinVerified(true);
        } else {
          setAttempts((prev) => prev - 1);
          setPin('');
        }
      }
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Incoming Call Screen Overlay */}
      {callActive ? (
        <View style={styles.callScreen}>
          <View style={styles.callHeader}>
            <View style={styles.callAvatar}>
              <Text style={styles.callAvatarText}>AICTE</Text>
            </View>
            <Text style={styles.callerName}>AICTE Automated Voice Assistant</Text>
            <Text style={styles.callSub}>Security Deposit Renewal Desk</Text>
            <Text style={styles.callTimer}>00:32 • Encrypted WebRTC</Text>
          </View>

          {!pinVerified ? (
            <View style={styles.pinContainer}>
              <Text style={styles.pinInstruction}>
                Enter 4-Digit Voice Security PIN (Demo: 1234)
              </Text>
              <Text style={styles.pinAttempts}>
                {attempts > 0 ? `${attempts} attempts remaining` : 'CHANNEL LOCKED (24h)'}
              </Text>

              {/* PIN Dots */}
              <View style={styles.pinDots}>
                {[0, 1, 2, 3].map((i) => (
                  <View
                    key={i}
                    style={[styles.pinDot, pin.length > i && styles.pinDotFilled]}
                  />
                ))}
              </View>

              {/* Keypad */}
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
            </View>
          ) : (
            <View style={styles.dialogueBox}>
              <Text style={styles.dialogueHeading}>FDR Briefing (Post-PIN)</Text>
              <Text style={styles.dialogueText}>
                FDR #AXIS-FDR-99201 for ₹35,00,000 matures on 2026-11-20.
              </Text>

              {!acknowledged ? (
                <TouchableOpacity
                  style={styles.ackButton}
                  onPress={() => setAcknowledged(true)}
                >
                  <Text style={styles.ackButtonText}>1 - Acknowledge Maturity</Text>
                </TouchableOpacity>
              ) : (
                <View style={styles.hashBadge}>
                  <Text style={styles.hashText}>✓ Cryptographic Ack Committed to Audit Ledger</Text>
                  <Text style={styles.hashSub}>sha256:7f83b1657ff1... recorded</Text>
                </View>
              )}
            </View>
          )}

          <TouchableOpacity
            style={styles.hangupButton}
            onPress={() => {
              setCallActive(false);
              setPin('');
              setPinVerified(false);
              setAcknowledged(false);
            }}
          >
            <Text style={styles.hangupText}>End Call</Text>
          </TouchableOpacity>
        </View>
      ) : (
        /* Main Mobile App Screen */
        <ScrollView contentContainerStyle={styles.scroll}>
          <View style={styles.header}>
            <Text style={styles.title}>AICTE FDR Mobile</Text>
            <Text style={styles.subtitle}>Institution Signatory Companion</Text>
          </View>

          {/* Quick Incoming Call Trigger Banner */}
          <TouchableOpacity
            style={styles.incomingBanner}
            onPress={() => setCallActive(true)}
          >
            <Text style={styles.bannerTitle}>📞 Simulate Incoming AI Voice Call</Text>
            <Text style={styles.bannerSubtitle}>Tap to test CallStyle notification & PIN unlock</Text>
          </TouchableOpacity>

          {/* Deposit Card */}
          <View style={styles.card}>
            <View style={styles.cardRow}>
              <Text style={styles.instNumber}>AXIS-FDR-99201</Text>
              <View style={styles.badgeL3}>
                <Text style={styles.badgeL3Text}>L3 Confirmed</Text>
              </View>
            </View>
            <Text style={styles.bankName}>Axis Bank • UTIB0002948</Text>
            <Text style={styles.amountText}>₹35,00,000</Text>
            <Text style={styles.metaText}>Maturity Date: 20 Nov 2026 (T-28 Days)</Text>

            <View style={styles.ladderProgress}>
              <View style={[styles.ladderStep, styles.stepCompleted]} />
              <View style={[styles.ladderStep, styles.stepCompleted]} />
              <View style={[styles.ladderStep, styles.stepActive]} />
              <View style={styles.ladderStep} />
              <View style={styles.ladderStep} />
            </View>
            <Text style={styles.stepLabel}>Step 3: T-30 Window In-App Voice Call Active</Text>
          </View>

          {/* Compliance Info */}
          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>Statutory Lock-in Compliance</Text>
            <Text style={styles.infoDesc}>
              Under AICTE APH Clause 6.46, this FDR is held jointly with Regional Officer, AICTE. Auto-renewal instruction is recorded on bank CBS.
            </Text>
          </View>
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  scroll: {
    padding: 20,
    gap: 16,
  },
  header: {
    marginBottom: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#f8fafc',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 12,
    color: '#00eeff',
    marginTop: 2,
    textTransform: 'uppercase',
    letterSpacing: 1.5,
    fontWeight: '600',
  },
  incomingBanner: {
    backgroundColor: '#3b0a6b',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.5)',
    shadowColor: '#00eeff',
    shadowOpacity: 0.35,
    shadowRadius: 12,
  },
  bannerTitle: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 15,
  },
  bannerSubtitle: {
    color: '#00eeff',
    fontSize: 12,
    marginTop: 4,
  },
  card: {
    backgroundColor: '#0c0716',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.2)',
  },
  cardRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  instNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: '#f1f5f9',
  },
  badgeL3: {
    backgroundColor: 'rgba(0, 238, 255, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.5)',
  },
  badgeL3Text: {
    color: '#00eeff',
    fontSize: 11,
    fontWeight: '700',
  },
  bankName: {
    color: '#c4b5fd',
    fontSize: 12,
    marginTop: 4,
  },
  amountText: {
    color: '#00eeff',
    fontSize: 24,
    fontWeight: '800',
    marginTop: 12,
  },
  metaText: {
    color: '#8b7ca8',
    fontSize: 12,
    marginTop: 4,
  },
  ladderProgress: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 14,
  },
  ladderStep: {
    flex: 1,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#1e293b',
  },
  stepCompleted: {
    backgroundColor: '#10b981',
  },
  stepActive: {
    backgroundColor: '#6366f1',
  },
  stepLabel: {
    color: '#a5b4fc',
    fontSize: 11,
    marginTop: 8,
  },
  infoCard: {
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  infoTitle: {
    color: '#e2e8f0',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
  },
  infoDesc: {
    color: '#94a3b8',
    fontSize: 12,
    lineHeight: 18,
  },
  callScreen: {
    flex: 1,
    backgroundColor: '#090d16',
    padding: 24,
    justifyContent: 'space-between',
  },
  callHeader: {
    alignItems: 'center',
    marginTop: 20,
  },
  callAvatar: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#4f46e5',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  callAvatarText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '800',
  },
  callerName: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
  },
  callSub: {
    color: '#94a3b8',
    fontSize: 13,
    marginTop: 4,
  },
  callTimer: {
    color: '#34d399',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 6,
  },
  pinContainer: {
    alignItems: 'center',
  },
  pinInstruction: {
    color: '#cbd5e1',
    fontSize: 13,
    textAlign: 'center',
  },
  pinAttempts: {
    color: '#f59e0b',
    fontSize: 11,
    marginTop: 4,
  },
  pinDots: {
    flexDirection: 'row',
    gap: 12,
    marginVertical: 16,
  },
  pinDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 1.5,
    borderColor: '#475569',
  },
  pinDotFilled: {
    backgroundColor: '#6366f1',
    borderColor: '#818cf8',
  },
  keypad: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    width: 240,
    justifyContent: 'center',
    gap: 12,
  },
  keypadKey: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  keypadText: {
    color: '#f8fafc',
    fontSize: 20,
    fontWeight: '700',
  },
  dialogueBox: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
  },
  dialogueHeading: {
    color: '#38bdf8',
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 8,
  },
  dialogueText: {
    color: '#e2e8f0',
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 16,
  },
  ackButton: {
    backgroundColor: '#10b981',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  ackButtonText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 13,
  },
  hashBadge: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)',
    alignItems: 'center',
  },
  hashText: {
    color: '#34d399',
    fontSize: 12,
    fontWeight: '700',
  },
  hashSub: {
    color: '#94a3b8',
    fontSize: 10,
    marginTop: 4,
    fontFamily: 'monospace',
  },
  hangupButton: {
    backgroundColor: '#ef4444',
    borderRadius: 30,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 20,
  },
  hangupText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 15,
  },
});
