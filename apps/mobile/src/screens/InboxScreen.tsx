import React, { useState } from 'react';
import { StyleSheet, View, Text, ScrollView, TouchableOpacity, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { Kosh } from '../design-system/Kosh';
import { MobileNotification } from '../types';

interface InboxScreenProps {
  notifications: MobileNotification[];
  onAcknowledgeNotification: (id: string) => void;
  onTriggerTestPush?: () => void;
}

type FilterCategory = 'All' | 'Reminders' | 'Observations' | 'Decisions';

/**
 * Mobile Notifications Screen
 * Mirrors Screen 7 from ui-refrence.png:
 * - Topbar: fdr@portal, progress 56%, Institution pill
 * - Title: Notifications
 * - Filter chips: [All | Reminders | Observations | Decisions]
 * - Empty state with calm Kosh mascot:
 *   "Nothing here yet"
 *   "Reminders, observations and decisions will appear here as soon as they happen."
 */
export const InboxScreen: React.FC<InboxScreenProps> = ({
  notifications,
  onAcknowledgeNotification,
  onTriggerTestPush,
}) => {
  const { tone, isDark } = useAppTheme();
  const [localNotifs, setLocalNotifs] = useState<MobileNotification[]>(notifications);
  const [activeChip, setActiveChip] = useState<FilterCategory>('All');
  const [deferNotice, setDeferNotice] = useState<string | null>(null);

  const cardBg = isDark ? tone.surface : '#ffffff';

  const filterChips: FilterCategory[] = ['All', 'Reminders', 'Observations', 'Decisions'];

  const handleAcknowledge = (id: string) => {
    setLocalNotifs((prev) =>
      prev.map((n) => (n.id === id ? { ...n, status: 'ACKNOWLEDGED' } : n))
    );
    onAcknowledgeNotification(id);
  };

  const handleRemindAgain = (id: string, duration: string) => {
    setLocalNotifs((prev) =>
      prev.map((n) => (n.id === id ? { ...n, local_remind_at: `Remind in ${duration}` } : n))
    );
    setDeferNotice(`Local reminder set for ${duration}.`);
    setTimeout(() => setDeferNotice(null), 3000);
  };

  const filtered = localNotifs.filter((n) => {
    if (activeChip === 'Reminders') {
      return (
        n.category === 'deadline' ||
        n.title.toLowerCase().includes('reminder') ||
        n.title.toLowerCase().includes('matur')
      );
    }
    if (activeChip === 'Observations') {
      return (
        n.category === 'critical_workflow' ||
        n.title.toLowerCase().includes('observation') ||
        n.title.toLowerCase().includes('discrepan')
      );
    }
    if (activeChip === 'Decisions') {
      return (
        n.category === 'security_account' ||
        n.title.toLowerCase().includes('release') ||
        n.title.toLowerCase().includes('approv')
      );
    }
    return true;
  });

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

          <View style={[styles.rolePill, { backgroundColor: tone.accentContainer }]}>
            <Text style={[styles.rolePillText, { color: tone.accent }]}>Institution</Text>
          </View>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {/* Title */}
        <View style={styles.headerBlock}>
          <Text style={[styles.pageTitle, { color: tone.text1 }]}>Notifications</Text>
        </View>

        {/* Filter Chips matching Screen 7 */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterRow}
        >
          {filterChips.map((chip) => {
            const isSelected = activeChip === chip;
            return (
              <TouchableOpacity
                key={chip}
                style={[
                  styles.filterChip,
                  isSelected
                    ? { backgroundColor: tone.ink }
                    : { backgroundColor: cardBg, borderColor: isDark ? tone.outline : '#e2e8f0', borderWidth: 1 },
                ]}
                onPress={() => setActiveChip(chip)}
              >
                <Text
                  style={[
                    styles.filterChipText,
                    isSelected ? { color: '#ffffff' } : { color: tone.text2 },
                  ]}
                >
                  {chip}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {deferNotice && (
          <View style={styles.deferBanner}>
            <Icon name="deadline" size={14} color="#d97706" />
            <Text style={styles.deferText}>{deferNotice}</Text>
          </View>
        )}

        {/* Notifications List or Calm Empty State */}
        {filtered.length === 0 ? (
          <View style={styles.emptyWrap}>
            <View style={styles.koshEmptyIcon}>
              <Kosh pose="calm" size={96} />
            </View>
            <Text style={[styles.emptyTitle, { color: tone.text1 }]}>Nothing here yet</Text>
            <Text style={[styles.emptySubtitle, { color: tone.text3 }]}>
              Reminders, observations and decisions will appear here as soon as they happen.
            </Text>
          </View>
        ) : (
          <View style={[styles.groupedCard, { backgroundColor: cardBg }]}>
            {filtered.map((item, idx) => {
              const isAcknowledged = item.status === 'ACKNOWLEDGED' || item.status === 'ACTIONED';

              return (
                <View
                  key={item.id}
                  style={[
                    styles.notifRow,
                    idx < filtered.length - 1 && styles.notifRowBorder,
                  ]}
                >
                  <View style={styles.notifLeft}>
                    <View style={[styles.iconCircle, { backgroundColor: tone.accentContainer }]}>
                      <Icon
                        name={
                          item.category === 'deadline'
                            ? 'calendar'
                            : item.category === 'critical_workflow'
                            ? 'checklist'
                            : 'notifications'
                        }
                        size={18}
                        color={tone.accent}
                      />
                    </View>

                    <View style={styles.notifInfo}>
                      <View style={styles.notifMetaRow}>
                        <Text style={[styles.notifTime, { color: tone.text3 }]}>
                          {item.created_at || 'Just now'}
                        </Text>
                        <View
                          style={[
                            styles.statusTag,
                            isAcknowledged
                              ? { backgroundColor: '#ecfdf5' }
                              : { backgroundColor: '#eff6ff' },
                          ]}
                        >
                          <Text
                            style={[
                              styles.statusTagText,
                              isAcknowledged ? { color: '#059669' } : { color: tone.accent },
                            ]}
                          >
                            {item.status.replace('_', ' ')}
                          </Text>
                        </View>
                      </View>

                      <Text style={[styles.notifTitle, { color: tone.text1 }]}>
                        {item.title}
                      </Text>
                      <Text style={[styles.notifBody, { color: tone.text2 }]}>
                        {item.body}
                      </Text>

                      {item.local_remind_at && (
                        <Text style={styles.remindBadge}>
                          ⏰ {item.local_remind_at}
                        </Text>
                      )}

                      {!isAcknowledged && (
                        <View style={styles.actionsRow}>
                          <TouchableOpacity
                            style={[styles.actionBtnAck, { backgroundColor: tone.ink }]}
                            onPress={() => handleAcknowledge(item.id)}
                          >
                            <Text style={styles.actionBtnAckText}>Acknowledge</Text>
                          </TouchableOpacity>

                          <TouchableOpacity
                            style={[styles.actionBtnDefer, { borderColor: isDark ? tone.outline : '#e2e8f0' }]}
                            onPress={() => handleRemindAgain(item.id, '2 hours')}
                          >
                            <Text style={[styles.actionBtnDeferText, { color: tone.text2 }]}>Remind in 2h</Text>
                          </TouchableOpacity>
                        </View>
                      )}
                    </View>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>
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
  filterRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 28,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 9999,
  },
  filterChipText: {
    fontSize: 13,
    fontWeight: '700',
  },
  deferBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 14,
    backgroundColor: '#fef3c7',
    marginBottom: 16,
  },
  deferText: {
    fontSize: 12,
    color: '#92400e',
    fontWeight: '600',
  },
  emptyWrap: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 64,
    paddingHorizontal: 32,
  },
  koshEmptyIcon: {
    marginBottom: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '800',
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 20,
    marginTop: 6,
    maxWidth: 280,
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
  notifRow: {
    paddingVertical: 14,
  },
  notifRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  notifLeft: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'flex-start',
  },
  iconCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  notifInfo: {
    flex: 1,
  },
  notifMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  notifTime: {
    fontSize: 11,
  },
  statusTag: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 9999,
  },
  statusTagText: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  notifTitle: {
    fontSize: 14,
    fontWeight: '700',
  },
  notifBody: {
    fontSize: 12,
    marginTop: 2,
    lineHeight: 18,
  },
  remindBadge: {
    fontSize: 11,
    color: '#d97706',
    fontWeight: '600',
    marginTop: 6,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 10,
  },
  actionBtnAck: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 9999,
  },
  actionBtnAckText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  actionBtnDefer: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 9999,
    borderWidth: 1,
  },
  actionBtnDeferText: {
    fontSize: 12,
    fontWeight: '600',
  },
});
