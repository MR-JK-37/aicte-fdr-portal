import React, { useState, useMemo } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  Modal,
  Platform,
} from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { EmptyState } from '../design-system/States';
import { MobileInstrument } from '../types';
import { formatPaiseINR } from '@aicte-fdr/shared';

interface CasesScreenProps {
  instruments: MobileInstrument[];
  onSelectInstrument?: (inst: MobileInstrument) => void;
}

/**
 * Mobile Cases / Institutions Screen
 * Mirrors ui-refrence.png:
 * - Screen 8: "Institutions" list with wordmark, progress 56%, search bar, grouped list card with avatars & chevrons
 * - Screen 5: "Release decision" modal with checklist status, clause 6.46 card, 0/500 reason, black pill Approve, soft red Reject
 */
export const CasesScreen: React.FC<CasesScreenProps> = ({ instruments, onSelectInstrument }) => {
  const { tone, isDark } = useAppTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCase, setSelectedCase] = useState<MobileInstrument | null>(null);
  const [reason, setReason] = useState('');
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const cardBg = isDark ? tone.surface : '#ffffff';

  const filtered = useMemo(() => {
    return instruments.filter((inst) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesNumber = inst.instrument_number.toLowerCase().includes(q);
        const matchesOrg =
          inst.institution_name.toLowerCase().includes(q) ||
          inst.institution_id.toLowerCase().includes(q);
        const matchesBank = inst.bank_name.toLowerCase().includes(q);
        if (!matchesNumber && !matchesOrg && !matchesBank) return false;
      }
      return true;
    });
  }, [instruments, searchQuery]);

  const handleApprove = (inst: MobileInstrument) => {
    setActionNotice(`Approved with step-up verification for ${inst.institution_name}.`);
    setTimeout(() => {
      setActionNotice(null);
      setSelectedCase(null);
    }, 2500);
  };

  const handleReject = (inst: MobileInstrument) => {
    setActionNotice(`Release request for ${inst.institution_name} returned for review.`);
    setTimeout(() => {
      setActionNotice(null);
      setSelectedCase(null);
    }, 2500);
  };

  return (
    <View style={[styles.container, { backgroundColor: tone.bg }]}>
      {/* 1. TopBar Header matching reference */}
      <View style={styles.topbar}>
        <View style={styles.topbarLeft}>
          <Text style={[styles.wordmark, { color: tone.text1 }]}>
            fdr<Text style={{ color: tone.accent }}>@</Text>portal
          </Text>
        </View>

        <View style={styles.topbarRight}>
          <View style={styles.progressMiniWrap}>
            <View style={[styles.progressTrack, { backgroundColor: isDark ? tone.surfaceMuted : '#e2e8f0' }]}>
              <View style={[styles.progressFill, { width: '56%', backgroundColor: tone.ink }]} />
            </View>
            <Text style={[styles.progressText, { color: tone.text1 }]}>56%</Text>
          </View>

          <TouchableOpacity style={[styles.bellBtn, { backgroundColor: cardBg }]}>
            <Icon name="notifications" size={18} color={tone.text1} />
          </TouchableOpacity>

          <View style={[styles.rolePill, { backgroundColor: tone.accentContainer }]}>
            <Text style={[styles.rolePillText, { color: tone.accent }]}>Intake</Text>
          </View>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {/* Title & Subtitle */}
        <View style={styles.headerBlock}>
          <Text style={[styles.pageTitle, { color: tone.text1 }]}>Institutions</Text>
          <Text style={[styles.pageSubtitle, { color: tone.text3 }]}>
            Find an institution by name or AICTE ID
          </Text>
        </View>

        {/* Search Bar matching Screen 8 */}
        <View style={[styles.searchBar, { backgroundColor: cardBg }]}>
          <Icon name="search" size={18} color="#94a3b8" />
          <TextInput
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholder="Search name or AICTE ID"
            placeholderTextColor="#94a3b8"
            style={[styles.searchInput, { color: tone.text1 }]}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Text style={{ fontSize: 12, color: tone.accent, fontWeight: '600' }}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Section: Available institutions */}
        <View style={styles.sectionWrap}>
          <Text style={[styles.sectionLabel, { color: tone.text3 }]}>Available institutions</Text>

          {filtered.length === 0 ? (
            <View style={[styles.emptyCard, { backgroundColor: cardBg }]}>
              <EmptyState
                icon="search"
                title="No institutions found"
                body={
                  instruments.length === 0
                    ? 'No institutions loaded yet from database.'
                    : 'No records matched your search.'
                }
              />
            </View>
          ) : (
            <View style={[styles.groupedCard, { backgroundColor: cardBg }]}>
              {filtered.map((inst, idx) => {
                const initials = inst.institution_name
                  .split(' ')
                  .filter(Boolean)
                  .map((w) => w[0])
                  .join('')
                  .slice(0, 2)
                  .toUpperCase();

                const idSuffix = inst.institution_id ? inst.institution_id.slice(-4) : '4417';

                return (
                  <TouchableOpacity
                    key={inst.id}
                    style={[
                      styles.instRow,
                      idx < filtered.length - 1 && styles.instRowBorder,
                    ]}
                    onPress={() => {
                      setSelectedCase(inst);
                      onSelectInstrument?.(inst);
                    }}
                  >
                    <View style={styles.instLeft}>
                      {/* Avatar Circle with Initials */}
                      <View style={[styles.avatarCircle, { backgroundColor: tone.accentContainer }]}>
                        <Text style={[styles.avatarText, { color: tone.accent }]}>{initials}</Text>
                      </View>

                      {/* Institution Details */}
                      <View style={styles.instInfo}>
                        <Text style={[styles.instName, { color: tone.text1 }]} numberOfLines={1}>
                          {inst.institution_name}
                        </Text>
                        <Text style={[styles.instSub, { color: tone.text3 }]}>
                          AICTE ID ending {idSuffix} · {inst.bank_name}
                        </Text>
                      </View>
                    </View>

                    <Text style={[styles.chevron, { color: tone.text3 }]}>›</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          )}
        </View>
      </ScrollView>

      {/* Screen 5 Modal: Release decision */}
      {selectedCase && (
        <Modal
          visible={!!selectedCase}
          animationType="slide"
          presentationStyle="pageSheet"
          onRequestClose={() => setSelectedCase(null)}
        >
          <View style={[styles.modalContainer, { backgroundColor: tone.bg }]}>
            {/* Modal TopBar */}
            <View style={styles.topbar}>
              <View style={styles.topbarLeft}>
                <Text style={[styles.wordmark, { color: tone.text1 }]}>
                  fdr<Text style={{ color: tone.accent }}>@</Text>portal
                </Text>
              </View>

              <View style={styles.topbarRight}>
                <TouchableOpacity style={[styles.bellBtn, { backgroundColor: cardBg }]}>
                  <Icon name="notifications" size={18} color={tone.text1} />
                </TouchableOpacity>

                <View style={[styles.rolePill, { backgroundColor: tone.accentContainer }]}>
                  <Text style={[styles.rolePillText, { color: tone.accent }]}>Authority</Text>
                </View>
              </View>
            </View>

            <ScrollView contentContainerStyle={styles.modalContent}>
              {/* Institution Header Card */}
              <View style={[styles.releaseHeaderCard, { backgroundColor: cardBg }]}>
                <View style={[styles.avatarCircleLarge, { backgroundColor: tone.accentContainer }]}>
                  <Text style={[styles.avatarTextLarge, { color: tone.accent }]}>
                    {selectedCase.institution_name
                      .split(' ')
                      .filter(Boolean)
                      .map((w) => w[0])
                      .join('')
                      .slice(0, 2)
                      .toUpperCase()}
                  </Text>
                </View>
                <View style={styles.releaseHeaderInfo}>
                  <Text style={[styles.releaseInstName, { color: tone.text1 }]}>
                    {selectedCase.institution_name}
                  </Text>
                  <Text style={[styles.releaseSub, { color: tone.text3 }]}>
                    Release request · FDR {selectedCase.instrument_number}
                  </Text>
                  <Text style={[styles.releaseAmount, { color: tone.accent }]}>
                    {formatPaiseINR(selectedCase.amount)}
                  </Text>
                </View>
              </View>

              {/* Checklist Complete Banner */}
              <View style={styles.checklistBanner}>
                <Text style={styles.checklistBannerText}>
                  Checklist is complete. Recommendation received from the Regional Supervisor.
                </Text>
              </View>

              {/* Recommendation Card */}
              <View style={[styles.recommendationCard, { backgroundColor: cardBg }]}>
                <Text style={[styles.recTitle, { color: tone.text1 }]}>Recommendation</Text>
                <Text style={[styles.recBody, { color: tone.text2 }]}>
                  All six clause 6.46 rows are satisfied. Execution evidence will be needed after approval.
                </Text>
                <Text style={[styles.recTimestamp, { color: tone.text3 }]}>
                  Yesterday, 18:38
                </Text>
              </View>

              {/* Add reason for your decision */}
              <View style={[styles.reasonSection, { backgroundColor: cardBg }]}>
                <Text style={[styles.reasonLabel, { color: tone.text1 }]}>
                  Add a reason for your decision
                </Text>
                <TextInput
                  value={reason}
                  onChangeText={setReason}
                  placeholder="Reason (optional)"
                  placeholderTextColor="#94a3b8"
                  maxLength={500}
                  multiline
                  style={[styles.reasonInput, { color: tone.text1, borderColor: isDark ? tone.outline : '#e2e8f0' }]}
                />
                <Text style={[styles.reasonCount, { color: tone.text3 }]}>
                  {reason.length}/500
                </Text>
              </View>

              {actionNotice && (
                <View style={styles.actionNoticeCard}>
                  <Text style={styles.actionNoticeText}>{actionNotice}</Text>
                </View>
              )}

              {/* Action Buttons */}
              <View style={styles.actionBlock}>
                {/* Black Pill: Approve with step-up */}
                <TouchableOpacity
                  style={[styles.pillBtnPrimary, { backgroundColor: tone.ink }]}
                  onPress={() => handleApprove(selectedCase)}
                >
                  <Text style={styles.pillBtnPrimaryText}>Approve with step-up</Text>
                </TouchableOpacity>

                {/* Soft Red Pill: Reject */}
                <TouchableOpacity
                  style={styles.pillBtnReject}
                  onPress={() => handleReject(selectedCase)}
                >
                  <Text style={styles.pillBtnRejectText}>Reject</Text>
                </TouchableOpacity>

                {/* Return */}
                <TouchableOpacity
                  style={styles.returnBtn}
                  onPress={() => setSelectedCase(null)}
                >
                  <Text style={[styles.returnBtnText, { color: tone.text3 }]}>Return</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          </View>
        </Modal>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  topbar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 54 : 20,
    paddingBottom: 14,
  },
  topbarLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  wordmark: {
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  topbarRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  progressMiniWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  progressTrack: {
    width: 32,
    height: 4,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 11,
    fontWeight: '700',
  },
  bellBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  rolePill: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 9999,
  },
  rolePillText: {
    fontSize: 11,
    fontWeight: '700',
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  headerBlock: {
    marginTop: 10,
    marginBottom: 16,
  },
  pageTitle: {
    fontSize: 26,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  pageSubtitle: {
    fontSize: 13,
    marginTop: 4,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 16,
    height: 48,
    borderRadius: 9999,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
    marginBottom: 24,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
  },
  sectionWrap: {
    marginBottom: 20,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 10,
  },
  groupedCard: {
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
  },
  emptyCard: {
    borderRadius: 22,
    padding: 24,
    alignItems: 'center',
  },
  instRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
  },
  instRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  instLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  avatarCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '800',
  },
  instInfo: {
    flex: 1,
  },
  instName: {
    fontSize: 14,
    fontWeight: '700',
  },
  instSub: {
    fontSize: 11,
    marginTop: 2,
  },
  chevron: {
    fontSize: 20,
    fontWeight: '400',
    marginLeft: 8,
  },
  modalContainer: {
    flex: 1,
  },
  modalContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
    gap: 16,
  },
  releaseHeaderCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    padding: 18,
    borderRadius: 22,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  avatarCircleLarge: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarTextLarge: {
    fontSize: 18,
    fontWeight: '800',
  },
  releaseHeaderInfo: {
    flex: 1,
  },
  releaseInstName: {
    fontSize: 15,
    fontWeight: '800',
  },
  releaseSub: {
    fontSize: 12,
    marginTop: 2,
  },
  releaseAmount: {
    fontSize: 13,
    fontWeight: '700',
    marginTop: 2,
  },
  checklistBanner: {
    backgroundColor: '#eff6ff',
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#dbeafe',
  },
  checklistBannerText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1e40af',
    lineHeight: 18,
  },
  recommendationCard: {
    padding: 18,
    borderRadius: 22,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
    gap: 6,
  },
  recTitle: {
    fontSize: 14,
    fontWeight: '800',
  },
  recBody: {
    fontSize: 12,
    lineHeight: 18,
  },
  recTimestamp: {
    fontSize: 11,
    marginTop: 4,
  },
  reasonSection: {
    padding: 18,
    borderRadius: 22,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  reasonLabel: {
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 8,
  },
  reasonInput: {
    height: 80,
    borderWidth: 1,
    borderRadius: 14,
    padding: 12,
    fontSize: 12,
    textAlignVertical: 'top',
  },
  reasonCount: {
    fontSize: 11,
    textAlign: 'right',
    marginTop: 4,
  },
  actionNoticeCard: {
    padding: 12,
    borderRadius: 14,
    backgroundColor: '#ecfdf5',
    borderWidth: 1,
    borderColor: '#a7f3d0',
  },
  actionNoticeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#065f46',
    textAlign: 'center',
  },
  actionBlock: {
    gap: 10,
    marginTop: 8,
  },
  pillBtnPrimary: {
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
  pillBtnPrimaryText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  pillBtnReject: {
    height: 48,
    borderRadius: 9999,
    backgroundColor: '#fee2e2',
    alignItems: 'center',
    justifyContent: 'center',
  },
  pillBtnRejectText: {
    color: '#b91c1c',
    fontSize: 14,
    fontWeight: '700',
  },
  returnBtn: {
    alignItems: 'center',
    paddingVertical: 10,
  },
  returnBtnText: {
    fontSize: 13,
    fontWeight: '600',
  },
});
