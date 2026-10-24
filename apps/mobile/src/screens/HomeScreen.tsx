import React from 'react';
import { StyleSheet, View, Text, ScrollView, TouchableOpacity, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { MobileInstrument, MobileTab } from '../types';

interface HomeScreenProps {
  instruments: MobileInstrument[];
  onNavigateTab: (tab: MobileTab) => void;
  onSelectInstrument?: (inst: MobileInstrument) => void;
  onOpenQRScanner?: () => void;
  onOpenDocCapture?: () => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  instruments,
  onNavigateTab,
  onSelectInstrument,
  onOpenQRScanner,
  onOpenDocCapture,
}) => {
  const totalAmountPaise = instruments.reduce((sum, i) => sum + i.amount, 0);
  const activeAmountPaise = instruments
    .filter((i) => i.status === 'ACTIVE')
    .reduce((sum, i) => sum + i.amount, 0);

  const formatINR = (paise: number) => {
    return `₹${(paise / 10000000).toFixed(2)} Cr`;
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header Profile Title */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerSuper}>AICTE REGULATION BUREAU</Text>
          <Text style={styles.headerTitle}>Security Deposit Companion</Text>
        </View>
        <TouchableOpacity
          style={styles.notifBadge}
          onPress={() => onNavigateTab('inbox')}
        >
          <Icon name="notifications" size={20} color="#00eeff" />
          <View style={styles.badgeDot} />
        </TouchableOpacity>
      </View>

      {/* KPI Balance Banner */}
      <View style={styles.kpiCard}>
        <Text style={styles.kpiLabel}>TOTAL CUSTODIAL EXPOSURE</Text>
        <Text style={styles.kpiAmount}>{formatINR(totalAmountPaise)}</Text>
        <View style={styles.kpiSubRow}>
          <Text style={styles.kpiSubText}>Active Compliant: {formatINR(activeAmountPaise)}</Text>
          <View style={styles.kpiPill}>
            <Text style={styles.kpiPillText}>Table 1.4 Norms Met</Text>
          </View>
        </View>
      </View>

      {/* Quick Actions Cluster (M-06) */}
      <View style={styles.quickActionsGrid}>
        <TouchableOpacity
          style={styles.quickActionItem}
          onPress={onOpenQRScanner}
        >
          <View style={styles.quickActionIcon}>
            <Icon name="qr" size={20} color="#00eeff" />
          </View>
          <Text style={styles.quickActionLabel}>Verify Receipt</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickActionItem}
          onPress={onOpenDocCapture}
        >
          <View style={styles.quickActionIcon}>
            <Icon name="scan" size={20} color="#00eeff" />
          </View>
          <Text style={styles.quickActionLabel}>Scan FDR Doc</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickActionItem}
          onPress={() => onNavigateTab('cases')}
        >
          <View style={styles.quickActionIcon}>
            <Icon name="search" size={20} color="#00eeff" />
          </View>
          <Text style={styles.quickActionLabel}>Search Registers</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.quickActionItem}
          onPress={() => onNavigateTab('tasks')}
        >
          <View style={styles.quickActionIcon}>
            <Icon name="checklist" size={20} color="#00eeff" />
          </View>
          <Text style={styles.quickActionLabel}>My Tasks</Text>
        </TouchableOpacity>
      </View>

      {/* Due-Soon Statutory Timeline */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="deadline" size={16} color="#fbbf24" />
          <Text style={styles.sectionTitle}>Maturity & Escalation Ladder</Text>
        </View>

        <View style={styles.timelineCard}>
          <View style={styles.timelineRow}>
            <View style={[styles.timelineNode, styles.nodeActive]} />
            <View style={styles.timelineContent}>
              <View style={styles.timelineHeader}>
                <Text style={styles.timelineTitle}>T - 30 Days: AXIS-FDR-99201</Text>
                <Text style={styles.timelineDate}>20 Nov 2026</Text>
              </View>
              <Text style={styles.timelineDesc}>
                Statutory renewal obligation active. Direct branch confirmation L3 verified.
              </Text>
            </View>
          </View>

          <View style={styles.timelineRow}>
            <View style={styles.timelineNode} />
            <View style={styles.timelineContent}>
              <View style={styles.timelineHeader}>
                <Text style={styles.timelineTitle}>T - 0 Days: PNB-771829 (Matured)</Text>
                <Text style={styles.timelineDate}>25 Oct 2026</Text>
              </View>
              <Text style={styles.timelineDesc}>
                Shortfall discrepancy open (₹25L of ₹35L). Automatic casework pending.
              </Text>
            </View>
          </View>
        </View>
      </View>

      {/* Recent Deposits Register Preview */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="instrument" size={16} color="#00eeff" />
          <Text style={styles.sectionTitle}>Registered Security Deposits</Text>
        </View>

        {instruments.slice(0, 3).map((inst) => (
          <TouchableOpacity
            key={inst.id}
            style={styles.instrumentCard}
            onPress={() => onSelectInstrument && onSelectInstrument(inst)}
          >
            <View style={styles.cardTopRow}>
              <Text style={styles.instNumber}>{inst.instrument_number}</Text>
              <View
                style={[
                  styles.statusBadge,
                  inst.status === 'ACTIVE'
                    ? styles.statusActive
                    : inst.status === 'EXPIRING'
                    ? styles.statusExpiring
                    : styles.statusMatured,
                ]}
              >
                <Text style={styles.statusText}>{inst.status}</Text>
              </View>
            </View>

            <Text style={styles.instOrg}>{inst.institution_name}</Text>
            <View style={styles.cardBottomRow}>
              <Text style={styles.instBank}>{inst.bank_name}</Text>
              <Text style={styles.instAmount}>
                ₹{(inst.amount / 100000).toFixed(0)} Lakhs
              </Text>
            </View>
          </TouchableOpacity>
        ))}
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
    padding: 18,
    gap: 18,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 10,
  },
  headerSuper: {
    fontSize: 10,
    color: '#00eeff',
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: -0.5,
    marginTop: 2,
  },
  notifBadge: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: '#151316',
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  badgeDot: {
    position: 'absolute',
    top: 9,
    right: 9,
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#ef4444',
  },
  kpiCard: {
    backgroundColor: '#151316',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.25)',
    padding: 20,
    gap: 6,
  },
  kpiLabel: {
    fontSize: 10,
    color: '#94a3b8',
    fontWeight: '700',
    letterSpacing: 1,
  },
  kpiAmount: {
    fontSize: 28,
    fontWeight: '800',
    color: '#00eeff',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  kpiSubRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
  },
  kpiSubText: {
    fontSize: 11,
    color: '#cbd5e1',
  },
  kpiPill: {
    backgroundColor: 'rgba(61, 220, 151, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(61, 220, 151, 0.4)',
  },
  kpiPillText: {
    color: '#3ddc97',
    fontSize: 10,
    fontWeight: '700',
  },
  quickActionsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
  },
  quickActionItem: {
    flex: 1,
    backgroundColor: '#151316',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#334155',
    paddingVertical: 14,
    alignItems: 'center',
    gap: 8,
  },
  quickActionIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(0, 238, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  quickActionLabel: {
    color: '#e2e8f0',
    fontSize: 10,
    fontWeight: '600',
    textAlign: 'center',
  },
  section: {
    gap: 10,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#cbd5e1',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  timelineCard: {
    backgroundColor: '#151316',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    padding: 16,
    gap: 16,
  },
  timelineRow: {
    flexDirection: 'row',
    gap: 12,
  },
  timelineNode: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#475569',
    marginTop: 4,
  },
  nodeActive: {
    backgroundColor: '#00eeff',
  },
  timelineContent: {
    flex: 1,
    gap: 2,
  },
  timelineHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  timelineTitle: {
    color: '#f8fafc',
    fontSize: 12,
    fontWeight: '700',
  },
  timelineDate: {
    color: '#94a3b8',
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  timelineDesc: {
    color: '#94a3b8',
    fontSize: 11,
    lineHeight: 15,
  },
  instrumentCard: {
    backgroundColor: '#151316',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    padding: 14,
    gap: 6,
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  instNumber: {
    color: '#00eeff',
    fontSize: 13,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  statusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusActive: {
    backgroundColor: 'rgba(61, 220, 151, 0.2)',
  },
  statusExpiring: {
    backgroundColor: 'rgba(251, 191, 36, 0.2)',
  },
  statusMatured: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  statusText: {
    color: '#f8fafc',
    fontSize: 9,
    fontWeight: '700',
  },
  instOrg: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  cardBottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 2,
  },
  instBank: {
    color: '#94a3b8',
    fontSize: 11,
  },
  instAmount: {
    color: '#f1f5f9',
    fontSize: 12,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
});
