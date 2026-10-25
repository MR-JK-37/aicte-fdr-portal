import React from 'react';
import { StyleSheet, View, Text, ScrollView, TouchableOpacity, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { Kosh } from '../design-system/Kosh';
import { MobileInstrument, MobileTab } from '../types';
import { formatCroresINR, formatPaiseINR } from '@aicte-fdr/shared';
import { useAuth } from '../auth/AuthContext';

interface HomeScreenProps {
  instruments: MobileInstrument[];
  onNavigateTab: (tab: MobileTab) => void;
  onSelectInstrument?: (inst: MobileInstrument) => void;
  onOpenQRScanner?: () => void;
  onOpenDocCapture?: () => void;
  onOpenChatbot?: () => void;
}

/**
 * Mobile Home Screen — Matching ui-refrence.png (Screen 3: "Hello, Asha")
 * TopBar: wordmark, progress mini (56%), role pill, action bell
 * Hero Card: Region chip, dynamic greeting, peeking Kosh mascot with circular halo
 * Grouped Section 1: "Needs attention" list card with chevrons
 * Grouped Section 2: "Main" actions list card with chevrons
 */
export const HomeScreen: React.FC<HomeScreenProps> = ({
  instruments,
  onNavigateTab,
  onSelectInstrument,
  onOpenQRScanner,
  onOpenDocCapture,
  onOpenChatbot,
}) => {
  const { tone, isDark } = useAppTheme();
  const { user } = useAuth();
  const cardBg = isDark ? tone.surface : '#ffffff';

  const displayName = user?.full_name?.split(' ')[0] || 'Officer';
  const displayRole = user?.role ? user.role.replace(/_/g, ' ') : 'Registrar';

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: tone.bg }]}
      contentContainerStyle={styles.content}
    >
      {/* 1. TopBar Header matching reference */}
      <View style={styles.topbar}>
        <View style={styles.topbarLeft}>
          <Text style={[styles.wordmark, { color: tone.text1 }]}>
            fdr<Text style={{ color: tone.accent }}>@</Text>portal
          </Text>
        </View>

        <View style={styles.topbarRight}>
          {/* Progress Mini (56%) */}
          <View style={styles.progressMiniWrap}>
            <View style={[styles.progressTrack, { backgroundColor: isDark ? tone.surfaceMuted : '#e2e8f0' }]}>
              <View style={[styles.progressFill, { width: '56%', backgroundColor: tone.ink }]} />
            </View>
            <Text style={[styles.progressText, { color: tone.text1 }]}>56%</Text>
          </View>

          {/* Role Pill */}
          <View style={[styles.rolePill, { backgroundColor: tone.accentContainer }]}>
            <Text style={[styles.rolePillText, { color: tone.accent }]}>{displayRole}</Text>
          </View>

          {/* Notification Bell */}
          <TouchableOpacity
            style={[styles.bellBtn, { backgroundColor: cardBg }]}
            onPress={() => onNavigateTab('inbox')}
            accessibilityLabel="Notifications"
            accessibilityRole="button"
          >
            <Icon name="notifications" size={18} color={tone.text1} />
            <View style={styles.bellDot} />
          </TouchableOpacity>
        </View>
      </View>

      {/* 2. Hero Card with Peeking Mascot and Region Chip */}
      <View style={[styles.heroCard, { backgroundColor: isDark ? tone.surface : '#dbe7fb' }]}>
        <View style={styles.heroContent}>
          <View style={styles.regionChip}>
            <Text style={styles.regionChipText}>Region: South</Text>
          </View>

          <Text style={[styles.heroGreeting, { color: tone.text1 }]}>
            Hello,{'\n'}{displayName}
          </Text>
        </View>

        {/* Aura Ring SVG / Circle */}
        <View style={styles.auraRing} pointerEvents="none" />

        {/* Peeking Mascot */}
        <View style={styles.koshWrapper} pointerEvents="none">
          <Kosh pose="peek" size={110} />
        </View>
      </View>

      {/* 3. Section: Needs Attention */}
      <View style={styles.sectionWrap}>
        <Text style={[styles.sectionLabel, { color: tone.text3 }]}>Needs attention</Text>
        <View style={[styles.groupedCard, { backgroundColor: cardBg }]}>
          {/* Row 1: Reply to an observation */}
          <TouchableOpacity
            style={[styles.listRow, { borderBottomColor: isDark ? tone.surfaceMuted : '#f1f5f9' }]}
            onPress={() => onNavigateTab('cases')}
          >
            <View style={[styles.rowIconCircle, { backgroundColor: '#fef3c7' }]}>
              <Icon name="checklist" size={18} color="#d97706" />
            </View>
            <View style={styles.rowMain}>
              <Text style={[styles.rowTitle, { color: tone.text1 }]}>Reply to an observation</Text>
              <Text style={[styles.rowSub, { color: '#d97706' }]}>Due 28 Oct 2026</Text>
            </View>
            <Text style={[styles.rowArrow, { color: tone.text3 }]}>›</Text>
          </TouchableOpacity>

          {/* Row 2: FDR maturing in 30 days */}
          <TouchableOpacity
            style={styles.listRow}
            onPress={() => onNavigateTab('cases')}
          >
            <View style={[styles.rowIconCircle, { backgroundColor: '#fee2e2' }]}>
              <Icon name="deadline" size={18} color="#dc2626" />
            </View>
            <View style={styles.rowMain}>
              <Text style={[styles.rowTitle, { color: tone.text1 }]}>FDR maturing in 30 days</Text>
              <Text style={[styles.rowSub, { color: tone.text3 }]}>Renewal not yet submitted</Text>
            </View>
            <Text style={[styles.rowArrow, { color: tone.text3 }]}>›</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* 4. Section: Main Actions */}
      <View style={styles.sectionWrap}>
        <Text style={[styles.sectionLabel, { color: tone.text3 }]}>Main</Text>
        <View style={[styles.groupedCard, { backgroundColor: cardBg }]}>
          {/* Row 1: Submit a new deposit */}
          <TouchableOpacity
            style={[styles.listRow, { borderBottomColor: isDark ? tone.surfaceMuted : '#f1f5f9' }]}
            onPress={onOpenDocCapture || (() => onNavigateTab('cases'))}
          >
            <View style={[styles.rowIconCircle, { backgroundColor: tone.accentContainer }]}>
              <Icon name="add" size={18} color={tone.accent} />
            </View>
            <View style={styles.rowMain}>
              <Text style={[styles.rowTitle, { color: tone.text1 }]}>Submit a new deposit</Text>
            </View>
            <Text style={[styles.rowArrow, { color: tone.text3 }]}>›</Text>
          </TouchableOpacity>

          {/* Row 2: My documents */}
          <TouchableOpacity
            style={[styles.listRow, { borderBottomColor: isDark ? tone.surfaceMuted : '#f1f5f9' }]}
            onPress={() => onNavigateTab('cases')}
          >
            <View style={[styles.rowIconCircle, { backgroundColor: tone.accentContainer }]}>
              <Icon name="documents" size={18} color={tone.accent} />
            </View>
            <View style={styles.rowMain}>
              <Text style={[styles.rowTitle, { color: tone.text1 }]}>My documents</Text>
            </View>
            <Text style={[styles.rowArrow, { color: tone.text3 }]}>›</Text>
          </TouchableOpacity>

          {/* Row 3: Maturity calendar */}
          <TouchableOpacity
            style={[styles.listRow, { borderBottomColor: isDark ? tone.surfaceMuted : '#eceff8' }]}
            onPress={() => onNavigateTab('tasks')}
          >
            <View style={[styles.rowIconCircle, { backgroundColor: tone.accentContainer }]}>
              <Icon name="calendar" size={18} color={tone.accent} />
            </View>
            <View style={styles.rowMain}>
              <Text style={[styles.rowTitle, { color: tone.text1 }]}>Maturity calendar</Text>
            </View>
            <Text style={[styles.rowArrow, { color: tone.text3 }]}>›</Text>
          </TouchableOpacity>

          {/* Row 4: Ask AI Handbook Chatbot */}
          <TouchableOpacity
            style={styles.listRow}
            onPress={onOpenChatbot}
          >
            <View style={[styles.rowIconCircle, { backgroundColor: tone.accentContainer }]}>
              <Icon name="chat" size={18} color={tone.accent} />
            </View>
            <View style={styles.rowMain}>
              <Text style={[styles.rowTitle, { color: tone.text1 }]}>Ask Handbook Chatbot</Text>
              <Text style={[styles.rowSub, { color: tone.text3 }]}>Kosh AI regulatory compliance assistant</Text>
            </View>
            <Text style={[styles.rowArrow, { color: tone.text3 }]}>›</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* 5. Live Registered Deposits (if available) */}
      {instruments.length > 0 && (
        <View style={styles.sectionWrap}>
          <Text style={[styles.sectionLabel, { color: tone.text3 }]}>Active registers</Text>
          <View style={[styles.groupedCard, { backgroundColor: cardBg }]}>
            {instruments.slice(0, 3).map((inst, index) => (
              <TouchableOpacity
                key={inst.id}
                style={[
                  styles.listRow,
                  index < Math.min(instruments.length, 3) - 1 && {
                    borderBottomColor: isDark ? tone.surfaceMuted : '#f1f5f9',
                  },
                ]}
                onPress={() => onSelectInstrument && onSelectInstrument(inst)}
              >
                <View style={[styles.rowIconCircle, { backgroundColor: tone.accentContainer }]}>
                  <Icon name="instrument" size={18} color={tone.accent} />
                </View>
                <View style={styles.rowMain}>
                  <Text style={[styles.rowTitle, { color: tone.text1 }]} numberOfLines={1}>
                    {inst.institution_name}
                  </Text>
                  <Text style={[styles.rowSub, { color: tone.text3 }]}>
                    {inst.instrument_number} • {formatPaiseINR(inst.amount)}
                  </Text>
                </View>
                <Text style={[styles.rowArrow, { color: tone.text3 }]}>›</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    gap: 14,
    paddingBottom: 40,
  },
  topbar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 4,
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
    gap: 8,
  },
  progressMiniWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  progressTrack: {
    width: 38,
    height: 4,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '800',
  },
  rolePill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
  },
  rolePillText: {
    fontSize: 11,
    fontWeight: '700',
  },
  bellBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  bellDot: {
    position: 'absolute',
    top: 7,
    right: 7,
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#ef4444',
  },
  heroCard: {
    borderRadius: 24,
    padding: 20,
    minHeight: 160,
    position: 'relative',
    overflow: 'hidden',
    justifyContent: 'space-between',
    shadowColor: '#1e1b4b',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 14,
    elevation: 4,
  },
  heroContent: {
    zIndex: 2,
    gap: 12,
  },
  regionChip: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.75)',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 999,
  },
  regionChipText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#1a1a1e',
  },
  heroGreeting: {
    fontSize: 30,
    lineHeight: 34,
    fontWeight: '800',
    letterSpacing: -0.5,
  },
  auraRing: {
    position: 'absolute',
    right: -24,
    top: -10,
    width: 170,
    height: 170,
    borderRadius: 85,
    borderWidth: 2,
    borderColor: '#b4c9f4',
    zIndex: 1,
  },
  koshWrapper: {
    position: 'absolute',
    right: 4,
    bottom: -18,
    zIndex: 2,
  },
  sectionWrap: {
    gap: 6,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
    paddingHorizontal: 4,
  },
  groupedCard: {
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#1e1b4b',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  listRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    gap: 12,
  },
  rowIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  rowMain: {
    flex: 1,
  },
  rowTitle: {
    fontSize: 14,
    fontWeight: '700',
  },
  rowSub: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 2,
  },
  rowArrow: {
    fontSize: 20,
    fontWeight: '400',
    lineHeight: 20,
  },
});
