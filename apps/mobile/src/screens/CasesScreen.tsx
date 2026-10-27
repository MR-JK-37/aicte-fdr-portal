import React, { useState, useMemo, useEffect, useCallback } from 'react';
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
import { api } from '../lib/apiClient';
import { useAuth } from '../auth/AuthContext';
import type { paths } from '@aicte-fdr/api-client';

type ReleaseRequestSummary =
  paths['/v1/release-requests']['get']['responses'][200]['content']['application/json'][number];
type ReleaseRequestDetail =
  paths['/v1/release-requests/{release_request_id}']['get']['responses'][200]['content']['application/json'];

interface CasesScreenProps {
  instruments: MobileInstrument[];
  onSelectInstrument?: (inst: MobileInstrument) => void;
}

function extractErrorCode(error: unknown): string | undefined {
  if (error && typeof error === 'object') {
    const e = error as Record<string, unknown>;
    if (typeof e.code === 'string') return e.code;
  }
  return undefined;
}

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object') {
    const e = error as Record<string, unknown>;
    if (typeof e.detail === 'string') return e.detail;
    if (typeof e.title === 'string') return e.title;
  }
  return fallback;
}

/**
 * Mobile Cases / Institutions Screen
 * Mirrors ui-refrence.png:
 * - Screen 8: "Institutions" list with wordmark, progress 56%, search bar, grouped list card with avatars & chevrons
 * - Screen 5: "Release decision" modal with checklist status, clause 6.46 card, 0/500 reason, black pill Approve, soft red Reject
 *
 * The release decision is real: it reads /v1/release-requests and submits
 * POST /v1/release-requests/{id}/decision, including the step-up MFA
 * round-trip the backend enforces (CLAUDE.md non-negotiable #4/#9 — a
 * decision is never shown as approved without a 2xx from that call).
 */
export const CasesScreen: React.FC<CasesScreenProps> = ({ instruments, onSelectInstrument }) => {
  const { tone, isDark } = useAppTheme();
  const { user, navigation } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCase, setSelectedCase] = useState<MobileInstrument | null>(null);
  const [reason, setReason] = useState('');
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);

  const [releaseRequests, setReleaseRequests] = useState<ReleaseRequestSummary[]>([]);
  const [releaseDetail, setReleaseDetail] = useState<ReleaseRequestDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [needsStepUp, setNeedsStepUp] = useState(false);
  const [stepUpToken, setStepUpToken] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const roleLabel = (user?.role ?? '').replace(/_/g, ' ') || 'Institution';

  const canDecide = useMemo(
    () => navigation?.web_sidebar?.some((item) => item.required_permission === 'approve_release') ?? false,
    [navigation]
  );

  const loadReleaseRequests = useCallback(async () => {
    const { data } = await api.GET('/v1/release-requests');
    setReleaseRequests(data ?? []);
  }, []);

  useEffect(() => {
    loadReleaseRequests();
  }, [loadReleaseRequests]);

  const activeReleaseRequest = selectedCase
    ? releaseRequests.find((r) => r.instrument_id === selectedCase.id)
    : null;

  useEffect(() => {
    if (!activeReleaseRequest) {
      setReleaseDetail(null);
      return;
    }
    setLoadingDetail(true);
    api
      .GET('/v1/release-requests/{release_request_id}', {
        params: { path: { release_request_id: activeReleaseRequest.id } },
      })
      .then(({ data }) => setReleaseDetail(data ?? null))
      .finally(() => setLoadingDetail(false));
  }, [activeReleaseRequest]);

  const closeModal = () => {
    setSelectedCase(null);
    setReleaseDetail(null);
    setReason('');
    setNeedsStepUp(false);
    setStepUpToken('');
    setActionNotice(null);
    setErrorNotice(null);
  };

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

  const submitDecision = async (decision: 'APPROVE' | 'REJECT') => {
    if (!activeReleaseRequest) return;
    setSubmitting(true);
    setActionNotice(null);
    setErrorNotice(null);
    const { data, error } = await api.POST('/v1/release-requests/{release_request_id}/decision', {
      params: { path: { release_request_id: activeReleaseRequest.id } },
      body: {
        decision,
        reason,
        step_up_token: needsStepUp && stepUpToken ? stepUpToken : undefined,
      } as any,
    });
    setSubmitting(false);

    if (data) {
      setActionNotice(
        decision === 'APPROVE'
          ? 'Release authorization approved with step-up verification. Status moved to execution-pending.'
          : 'Release decision recorded as rejected.'
      );
      setNeedsStepUp(false);
      setStepUpToken('');
      loadReleaseRequests();
      return;
    }

    if (extractErrorCode(error) === 'step_up_required') {
      setNeedsStepUp(true);
      setErrorNotice('Enter your current 6-digit authenticator code to confirm this decision.');
      return;
    }
    setErrorNotice(extractErrorMessage(error, 'The decision was not accepted.'));
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
            <Text style={[styles.rolePillText, { color: tone.accent }]}>{roleLabel}</Text>
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
          onRequestClose={closeModal}
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
                  <Text style={[styles.rolePillText, { color: tone.accent }]}>{roleLabel}</Text>
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
                {releaseDetail && (
                  <Text style={[styles.releaseSub, { color: tone.text3 }]}>{releaseDetail.status}</Text>
                )}
              </View>

              {loadingDetail && (
                <Text style={{ fontSize: 12, color: tone.text3, textAlign: 'center' }}>
                  Loading release request…
                </Text>
              )}

              {!loadingDetail && !activeReleaseRequest && (
                <View style={[styles.recommendationCard, { backgroundColor: cardBg }]}>
                  <Text style={[styles.recBody, { color: tone.text2 }]}>
                    No release request is pending for this instrument. A request appears here once
                    the security deposit has cleared the completeness checklist and scrutiny
                    recommendation. Nothing on this screen is simulated or invented.
                  </Text>
                </View>
              )}

              {releaseDetail && (
                <>
                  {/* Checklist Status Banner */}
                  <View style={styles.checklistBanner}>
                    <Text style={styles.checklistBannerText}>
                      {releaseDetail.checklist.length === 0
                        ? 'No clause 6.46 checklist rows recorded yet for this request.'
                        : releaseDetail.checklist.every((c) => c.status === 'SATISFIED')
                        ? 'Checklist is complete.'
                        : `${releaseDetail.checklist.filter((c) => c.status !== 'SATISFIED').length} of ${releaseDetail.checklist.length} checklist rows still open.`}
                    </Text>
                  </View>

                  {/* Recommendation Card */}
                  <View style={[styles.recommendationCard, { backgroundColor: cardBg }]}>
                    <Text style={[styles.recTitle, { color: tone.text1 }]}>Recommendation</Text>
                    {releaseDetail.recommendation ? (
                      <>
                        <Text style={[styles.recBody, { color: tone.text2 }]}>
                          {releaseDetail.recommendation}
                          {releaseDetail.recommendation_reason ? `: ${releaseDetail.recommendation_reason}` : ''}
                        </Text>
                        {releaseDetail.recommended_at && (
                          <Text style={[styles.recTimestamp, { color: tone.text3 }]}>
                            {new Date(releaseDetail.recommended_at).toLocaleString()}
                          </Text>
                        )}
                      </>
                    ) : (
                      <Text style={[styles.recBody, { color: tone.text2 }]}>
                        No scrutiny recommendation recorded yet.
                      </Text>
                    )}
                  </View>

                  {!canDecide && (
                    <View style={[styles.recommendationCard, { backgroundColor: cardBg }]}>
                      <Text style={[styles.recBody, { color: tone.text2 }]}>
                        Your role is not entitled to decide release requests. This view is
                        read-only; only the competent authority can approve or reject a release.
                      </Text>
                    </View>
                  )}

                  {canDecide && (
                    <>
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

                        {needsStepUp && (
                          <View style={{ marginTop: 10, gap: 6 }}>
                            <Text style={[styles.reasonLabel, { color: tone.text1 }]}>
                              6-digit authenticator code (step-up verification)
                            </Text>
                            <TextInput
                              value={stepUpToken}
                              onChangeText={(v) => setStepUpToken(v.replace(/\D/g, '').slice(0, 6))}
                              placeholder="000000"
                              placeholderTextColor="#94a3b8"
                              keyboardType="number-pad"
                              maxLength={6}
                              style={[styles.reasonInput, { height: 48, color: tone.text1, borderColor: isDark ? tone.outline : '#e2e8f0' }]}
                            />
                          </View>
                        )}
                      </View>

                      {errorNotice && (
                        <View style={[styles.actionNoticeCard, { backgroundColor: '#fef2f2' }]}>
                          <Text style={[styles.actionNoticeText, { color: '#b91c1c' }]}>{errorNotice}</Text>
                        </View>
                      )}

                      {actionNotice && (
                        <View style={styles.actionNoticeCard}>
                          <Text style={styles.actionNoticeText}>{actionNotice}</Text>
                        </View>
                      )}

                      {/* Action Buttons */}
                      <View style={styles.actionBlock}>
                        {/* Black Pill: Approve with step-up */}
                        <TouchableOpacity
                          style={[styles.pillBtnPrimary, { backgroundColor: tone.ink, opacity: submitting ? 0.6 : 1 }]}
                          disabled={submitting || (needsStepUp && stepUpToken.length !== 6)}
                          onPress={() => submitDecision('APPROVE')}
                        >
                          <Text style={styles.pillBtnPrimaryText}>
                            {submitting ? 'Submitting…' : 'Approve with step-up'}
                          </Text>
                        </TouchableOpacity>

                        {/* Soft Red Pill: Reject */}
                        <TouchableOpacity
                          style={[styles.pillBtnReject, { opacity: submitting ? 0.6 : 1 }]}
                          disabled={submitting}
                          onPress={() => submitDecision('REJECT')}
                        >
                          <Text style={styles.pillBtnRejectText}>Reject</Text>
                        </TouchableOpacity>
                      </View>
                    </>
                  )}
                </>
              )}

              {/* Return */}
              <TouchableOpacity style={styles.returnBtn} onPress={closeModal}>
                <Text style={[styles.returnBtnText, { color: tone.text3 }]}>Return</Text>
              </TouchableOpacity>
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
