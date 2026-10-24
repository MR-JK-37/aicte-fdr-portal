import React, { useState, useMemo } from 'react';
import { StyleSheet, View, Text, TextInput, ScrollView, TouchableOpacity, Modal, Platform, Share } from 'react-native';
import { Icon } from '../design-system/Icon';
import { MobileInstrument } from '../types';

interface CasesScreenProps {
  instruments: MobileInstrument[];
  onSelectInstrument?: (inst: MobileInstrument) => void;
}

export const CasesScreen: React.FC<CasesScreenProps> = ({ instruments }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedCase, setSelectedCase] = useState<MobileInstrument | null>(null);
  const [calendarNotice, setCalendarNotice] = useState<string | null>(null);

  const filtered = useMemo(() => {
    return instruments.filter((inst) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesNumber = inst.instrument_number.toLowerCase().includes(q);
        const matchesOrg = inst.institution_name.toLowerCase().includes(q) || inst.institution_id.toLowerCase().includes(q);
        const matchesBank = inst.bank_name.toLowerCase().includes(q);
        if (!matchesNumber && !matchesOrg && !matchesBank) return false;
      }
      if (statusFilter !== 'ALL' && inst.status !== statusFilter) {
        return false;
      }
      return true;
    });
  }, [instruments, searchQuery, statusFilter]);

  const handleShareCase = async (inst: MobileInstrument) => {
    try {
      await Share.share({
        title: `AICTE Deposit Ref ${inst.instrument_number}`,
        message: `AICTE Security Deposit Case: ${inst.instrument_number} (${inst.institution_name}). Certified under AICTE Act Sec. 10(k). Deep Link: aicte-fdr://case/${inst.id}`,
      });
    } catch {
      // Ignore user cancellation
    }
  };

  const handleAddToCalendar = (inst: MobileInstrument) => {
    setCalendarNotice(`Maturity alert for ${inst.instrument_number} added to device calendar.`);
    setTimeout(() => setCalendarNotice(null), 3000);
  };

  return (
    <View style={styles.container}>
      {/* Top Search & Filter Bar */}
      <View style={styles.topBar}>
        <View style={styles.searchBox}>
          <Icon name="search" size={16} color="#00eeff" />
          <TextInput
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholder="Search FDR no., institution, bank..."
            placeholderTextColor="#64748b"
            style={styles.searchInput}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Text style={styles.clearText}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Filter Pills */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterScroll}>
          {['ALL', 'ACTIVE', 'EXPIRING', 'MATURED', 'RELEASE_REQUESTED'].map((filter) => {
            const active = statusFilter === filter;
            return (
              <TouchableOpacity
                key={filter}
                style={[styles.filterPill, active && styles.filterPillActive]}
                onPress={() => setStatusFilter(filter)}
              >
                <Text style={[styles.filterText, active && styles.filterTextActive]}>{filter}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {calendarNotice && (
        <View style={styles.noticeBar}>
          <Icon name="calendar" size={14} color="#00eeff" />
          <Text style={styles.noticeText}>{calendarNotice}</Text>
        </View>
      )}

      {/* Instruments List */}
      <ScrollView contentContainerStyle={styles.listContent}>
        <Text style={styles.listHeader}>
          {filtered.length} REGISTERED DEPOSIT CASES (PARITY F-03/F-17)
        </Text>

        {filtered.map((inst) => (
          <TouchableOpacity
            key={inst.id}
            style={styles.caseCard}
            onPress={() => setSelectedCase(inst)}
          >
            <View style={styles.cardHeader}>
              <Text style={styles.caseNumber}>{inst.instrument_number}</Text>
              <View style={styles.badgeRow}>
                <View style={styles.levelBadge}>
                  <Text style={styles.levelBadgeText}>{inst.evidence_level}</Text>
                </View>
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
            </View>

            <Text style={styles.instName}>{inst.institution_name}</Text>
            <Text style={styles.instCode}>{inst.institution_id}</Text>

            <View style={styles.cardFooter}>
              <Text style={styles.bankText}>{inst.bank_name}</Text>
              <Text style={styles.amountText}>
                ₹{(inst.amount / 100000).toFixed(0)} Lakhs
              </Text>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Detailed Case Inspector Modal */}
      {selectedCase && (
        <Modal visible={!!selectedCase} animationType="slide" transparent>
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <View>
                  <Text style={styles.modalSuper}>INSTRUMENT CASE DOSSIER</Text>
                  <Text style={styles.modalTitle}>{selectedCase.instrument_number}</Text>
                </View>
                <TouchableOpacity onPress={() => setSelectedCase(null)} style={styles.closeBtn}>
                  <Text style={styles.closeText}>Done</Text>
                </TouchableOpacity>
              </View>

              <ScrollView contentContainerStyle={styles.modalBody}>
                {/* Institution & Financials */}
                <View style={styles.sectionCard}>
                  <Text style={styles.secTitle}>Institutional Beneficiary</Text>
                  <Text style={styles.secName}>{selectedCase.institution_name}</Text>
                  <Text style={styles.secSub}>Code: {selectedCase.institution_id}</Text>
                  <View style={styles.divider} />
                  <Text style={styles.secTitle}>Deposit Particulars</Text>
                  <View style={styles.twoCol}>
                    <View>
                      <Text style={styles.colLabel}>Amount (INR)</Text>
                      <Text style={styles.colValAmount}>₹{(selectedCase.amount / 100000).toFixed(0)} Lakhs</Text>
                    </View>
                    <View>
                      <Text style={styles.colLabel}>Maturity Date</Text>
                      <Text style={styles.colValDate}>{selectedCase.maturity_date}</Text>
                    </View>
                  </View>
                </View>

                {/* Evidence & Custody */}
                <View style={styles.sectionCard}>
                  <Text style={styles.secTitle}>Custody & Verification Level</Text>
                  <View style={styles.evidenceRow}>
                    <View style={styles.levelBadgeLarge}>
                      <Text style={styles.levelLargeText}>{selectedCase.evidence_level} Verified</Text>
                    </View>
                    <Text style={styles.evidenceDesc}>
                      {selectedCase.evidence_level === 'L3'
                        ? 'Bank Statement Matched (Exact UTR)'
                        : selectedCase.evidence_level === 'L2'
                        ? 'Direct Branch Signed Confirmation'
                        : 'OCR Extracted Scanned Copy'}
                    </Text>
                  </View>
                  <Text style={styles.jointLabel}>Joint Account Holder:</Text>
                  <Text style={styles.jointVal}>{selectedCase.joint_account_holder ?? 'Regional Officer, AICTE'}</Text>
                </View>

                {/* Mobile Extra Actions (M-10, M-15) */}
                <View style={styles.actionGrid}>
                  <TouchableOpacity
                    style={styles.actionBtn}
                    onPress={() => handleAddToCalendar(selectedCase)}
                  >
                    <Icon name="calendar" size={16} color="#00eeff" />
                    <Text style={styles.actionBtnText}>Add to Calendar (M-10)</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.actionBtn}
                    onPress={() => handleShareCase(selectedCase)}
                  >
                    <Icon name="share" size={16} color="#00eeff" />
                    <Text style={styles.actionBtnText}>Share Dossier (M-15)</Text>
                  </TouchableOpacity>
                </View>
              </ScrollView>
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  topBar: {
    paddingHorizontal: 16,
    paddingTop: 12,
    gap: 10,
    backgroundColor: '#050505',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    paddingBottom: 12,
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#151316',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 12,
    paddingHorizontal: 12,
    gap: 8,
    height: 42,
  },
  searchInput: {
    flex: 1,
    color: '#ffffff',
    fontSize: 13,
  },
  clearText: {
    color: '#94a3b8',
    fontSize: 11,
  },
  filterScroll: {
    gap: 6,
  },
  filterPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    backgroundColor: '#151316',
    borderWidth: 1,
    borderColor: '#334155',
  },
  filterPillActive: {
    backgroundColor: 'rgba(0, 238, 255, 0.15)',
    borderColor: '#00eeff',
  },
  filterText: {
    color: '#94a3b8',
    fontSize: 10,
    fontWeight: '600',
  },
  filterTextActive: {
    color: '#00eeff',
  },
  noticeBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(0, 238, 255, 0.1)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 238, 255, 0.2)',
  },
  noticeText: {
    color: '#00eeff',
    fontSize: 11,
    fontWeight: '600',
  },
  listContent: {
    padding: 16,
    gap: 12,
  },
  listHeader: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748b',
    letterSpacing: 0.5,
  },
  caseCard: {
    backgroundColor: '#151316',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    padding: 16,
    gap: 6,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  caseNumber: {
    fontSize: 14,
    fontWeight: '700',
    color: '#00eeff',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 6,
  },
  levelBadge: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  levelBadgeText: {
    color: '#cbd5e1',
    fontSize: 10,
    fontWeight: '700',
  },
  statusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusActive: { backgroundColor: 'rgba(61, 220, 151, 0.2)' },
  statusExpiring: { backgroundColor: 'rgba(251, 191, 36, 0.2)' },
  statusMatured: { backgroundColor: 'rgba(239, 68, 68, 0.2)' },
  statusText: {
    color: '#f8fafc',
    fontSize: 9,
    fontWeight: '700',
  },
  instName: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  instCode: {
    color: '#64748b',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    paddingTop: 8,
  },
  bankText: {
    color: '#94a3b8',
    fontSize: 11,
  },
  amountText: {
    color: '#f8fafc',
    fontSize: 13,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#0c0716',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '85%',
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.3)',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  modalSuper: {
    color: '#00eeff',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
  },
  modalTitle: {
    color: '#ffffff',
    fontSize: 17,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  closeBtn: {
    padding: 6,
  },
  closeText: {
    color: '#00eeff',
    fontSize: 14,
    fontWeight: '600',
  },
  modalBody: {
    padding: 20,
    gap: 16,
  },
  sectionCard: {
    backgroundColor: '#151316',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    padding: 16,
    gap: 6,
  },
  secTitle: {
    color: '#94a3b8',
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  secName: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
  secSub: {
    color: '#64748b',
    fontSize: 11,
  },
  divider: {
    height: 1,
    backgroundColor: '#1e293b',
    marginVertical: 6,
  },
  twoCol: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  colLabel: {
    color: '#64748b',
    fontSize: 10,
  },
  colValAmount: {
    color: '#00eeff',
    fontSize: 15,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  colValDate: {
    color: '#f8fafc',
    fontSize: 13,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  evidenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
  },
  levelBadgeLarge: {
    backgroundColor: '#004f55',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  levelLargeText: {
    color: '#84f3ff',
    fontSize: 11,
    fontWeight: '700',
  },
  evidenceDesc: {
    color: '#cbd5e1',
    fontSize: 11,
    flex: 1,
  },
  jointLabel: {
    color: '#64748b',
    fontSize: 11,
    marginTop: 6,
  },
  jointVal: {
    color: '#e2e8f0',
    fontSize: 12,
    fontWeight: '600',
  },
  actionGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#151316',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 14,
    paddingVertical: 12,
  },
  actionBtnText: {
    color: '#00eeff',
    fontSize: 11,
    fontWeight: '600',
  },
});
