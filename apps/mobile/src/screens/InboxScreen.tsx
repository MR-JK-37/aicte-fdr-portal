import React, { useState } from 'react';
import { StyleSheet, View, Text, ScrollView, TouchableOpacity, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { MobileNotification } from '../types';

interface InboxScreenProps {
  notifications: MobileNotification[];
  onAcknowledgeNotification: (id: string) => void;
  onTriggerTestPush?: () => void;
}

export const InboxScreen: React.FC<InboxScreenProps> = ({
  notifications,
  onAcknowledgeNotification,
  onTriggerTestPush,
}) => {
  const [localNotifs, setLocalNotifs] = useState<MobileNotification[]>(notifications);
  const [filter, setFilter] = useState<'ALL' | 'UNACKNOWLEDGED'>('ALL');
  const [deferNotice, setDeferNotice] = useState<string | null>(null);

  const handleRemindAgain = (id: string, duration: string) => {
    setLocalNotifs((prev) =>
      prev.map((n) => (n.id === id ? { ...n, local_remind_at: `Remind in ${duration}` } : n))
    );
    setDeferNotice(`Local reminder set for ${duration} (M-11). Server obligation remains active.`);
    setTimeout(() => setDeferNotice(null), 3000);
  };

  const filtered = localNotifs.filter((n) => {
    if (filter === 'UNACKNOWLEDGED') {
      return n.status !== 'ACKNOWLEDGED' && n.status !== 'ACTIONED';
    }
    return true;
  });

  const getStageColor = (status: string) => {
    switch (status) {
      case 'ACTIONED':
        return '#3ddc97';
      case 'ACKNOWLEDGED':
        return '#00eeff';
      case 'OPENED':
        return '#c084fc';
      case 'DEVICE_RECEIVED':
        return '#60a5fa';
      default:
        return '#94a3b8';
    }
  };

  return (
    <View style={styles.container}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <View>
          <Text style={styles.headerSuper}>SERVER-BACKED INBOX (M-01/M-02)</Text>
          <Text style={styles.headerTitle}>Realtime Push & Notifications</Text>
        </View>

        {onTriggerTestPush && (
          <TouchableOpacity style={styles.testBtn} onPress={onTriggerTestPush}>
            <Icon name="notifications_active" size={14} color="#00eeff" />
            <Text style={styles.testBtnText}>Test Push</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Sync Status Banner */}
      <View style={styles.syncBanner}>
        <Icon name="sync" size={14} color="#3ddc97" />
        <Text style={styles.syncText}>SSE Stream Connected • Last-Event-ID Synced</Text>
      </View>

      {deferNotice && (
        <View style={styles.deferBanner}>
          <Icon name="deadline" size={14} color="#fbbf24" />
          <Text style={styles.deferText}>{deferNotice}</Text>
        </View>
      )}

      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        <TouchableOpacity
          style={[styles.filterTab, filter === 'ALL' && styles.filterTabActive]}
          onPress={() => setFilter('ALL')}
        >
          <Text style={[styles.filterTabText, filter === 'ALL' && styles.filterTabTextActive]}>
            All ({localNotifs.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterTab, filter === 'UNACKNOWLEDGED' && styles.filterTabActive]}
          onPress={() => setFilter('UNACKNOWLEDGED')}
        >
          <Text style={[styles.filterTabText, filter === 'UNACKNOWLEDGED' && styles.filterTabTextActive]}>
            Pending Ack
          </Text>
        </TouchableOpacity>
      </View>

      {/* Notification Cards */}
      <ScrollView contentContainerStyle={styles.listContent}>
        {filtered.map((n) => {
          const isAck = n.status === 'ACKNOWLEDGED' || n.status === 'ACTIONED';
          return (
            <View key={n.id} style={styles.notifCard}>
              <View style={styles.cardHeader}>
                <View style={styles.categoryRow}>
                  <Text style={styles.categoryText}>{n.category.replace('_', ' ')}</Text>
                  {n.local_remind_at && (
                    <Text style={styles.deferPill}>{n.local_remind_at}</Text>
                  )}
                </View>
                <View style={[styles.stageBadge, { borderColor: getStageColor(n.status) }]}>
                  <Text style={[styles.stageText, { color: getStageColor(n.status) }]}>
                    {n.status}
                  </Text>
                </View>
              </View>

              <Text style={styles.titleText}>{n.title}</Text>
              <Text style={styles.bodyText}>{n.body}</Text>

              <View style={styles.cardFooter}>
                <Text style={styles.timeText}>{n.created_at}</Text>

                <View style={styles.actionRow}>
                  {/* Local deferral (M-11) */}
                  <TouchableOpacity
                    style={styles.deferBtn}
                    onPress={() => handleRemindAgain(n.id, '4h')}
                  >
                    <Text style={styles.deferBtnText}>Remind in 4h</Text>
                  </TouchableOpacity>

                  {/* Server Ack */}
                  {!isAck ? (
                    <TouchableOpacity
                      style={styles.ackBtn}
                      onPress={() => {
                        onAcknowledgeNotification(n.id);
                        setLocalNotifs((prev) =>
                          prev.map((item) =>
                            item.id === n.id ? { ...item, status: 'ACKNOWLEDGED' } : item
                          )
                        );
                      }}
                    >
                      <Icon name="verified" size={13} color="#050505" />
                      <Text style={styles.ackBtnText}>Acknowledge</Text>
                    </TouchableOpacity>
                  ) : (
                    <View style={styles.ackDonePill}>
                      <Icon name="success" size={12} color="#3ddc97" />
                      <Text style={styles.ackDoneText}>Server Recorded</Text>
                    </View>
                  )}
                </View>
              </View>
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  headerSuper: {
    fontSize: 10,
    color: '#00eeff',
    fontWeight: '700',
    letterSpacing: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ffffff',
    letterSpacing: -0.5,
  },
  testBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(0, 238, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.3)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  testBtnText: {
    color: '#00eeff',
    fontSize: 11,
    fontWeight: '600',
  },
  syncBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#0c0716',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#1e293b',
    paddingHorizontal: 16,
    paddingVertical: 6,
  },
  syncText: {
    color: '#94a3b8',
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  deferBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(251, 191, 36, 0.1)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(251, 191, 36, 0.3)',
    paddingHorizontal: 16,
    paddingVertical: 6,
  },
  deferText: {
    color: '#fbbf24',
    fontSize: 11,
    fontWeight: '600',
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 8,
    gap: 12,
  },
  filterTab: {
    paddingBottom: 6,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  filterTabActive: {
    borderBottomColor: '#00eeff',
  },
  filterTabText: {
    color: '#64748b',
    fontSize: 12,
    fontWeight: '600',
  },
  filterTabTextActive: {
    color: '#00eeff',
  },
  listContent: {
    padding: 16,
    gap: 12,
  },
  notifCard: {
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
  categoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  categoryText: {
    color: '#00eeff',
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  deferPill: {
    color: '#fbbf24',
    fontSize: 9,
    backgroundColor: 'rgba(251, 191, 36, 0.15)',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
  },
  stageBadge: {
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  stageText: {
    fontSize: 9,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  titleText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  bodyText: {
    color: '#cbd5e1',
    fontSize: 12,
    lineHeight: 16,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    paddingTop: 8,
  },
  timeText: {
    color: '#64748b',
    fontSize: 10,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  deferBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: '#1e293b',
  },
  deferBtnText: {
    color: '#cbd5e1',
    fontSize: 10,
    fontWeight: '600',
  },
  ackBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#00eeff',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  ackBtnText: {
    color: '#050505',
    fontSize: 10,
    fontWeight: '700',
  },
  ackDonePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  ackDoneText: {
    color: '#3ddc97',
    fontSize: 10,
    fontWeight: '600',
  },
});
