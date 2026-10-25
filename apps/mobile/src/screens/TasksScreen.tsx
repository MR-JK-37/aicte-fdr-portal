import React, { useState } from 'react';
import { StyleSheet, View, Text, ScrollView, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { Kosh } from '../design-system/Kosh';
import { MobileTask } from '../types';

interface TasksScreenProps {
  tasks?: MobileTask[];
  onTaskResolved?: (taskId: string) => void;
}

const DEFAULT_REALISTIC_TASKS: MobileTask[] = [
  {
    id: 'tsk-101',
    title: 'Verify Tripartite Joint Lien Endorsement Letter',
    type: 'intake_review',
    instrument_number: 'FDR-XXXX0192',
    institution_name: 'Apex Institute of Technology, Bengaluru',
    assigned_role: 'scrutiny_officer',
    due_date: '28 Oct 2026',
    urgency: 'high',
  },
  {
    id: 'tsk-102',
    title: 'SFMS Confirmation Reconciliation with Bank Gateway',
    type: 'bank_verify',
    instrument_number: 'FDR-XXXX1008',
    institution_name: 'RV College of Engineering, Bengaluru',
    assigned_role: 'verifier',
    due_date: '30 Oct 2026',
    urgency: 'statutory_deadline',
  },
  {
    id: 'tsk-103',
    title: 'Examine T-50 Maturity Ladder Extension Request',
    type: 'discrepancy_casework',
    instrument_number: 'FDR-XXXX7821',
    institution_name: 'Apex Institute of Technology, Bengaluru',
    assigned_role: 'regional_officer',
    due_date: '04 Nov 2026',
    urgency: 'statutory_deadline',
  },
];

/**
 * Mobile Tasks Screen
 * Lavender Ledger layout: Topbar, page header, grouped list / calm Kosh empty state
 */
export const TasksScreen: React.FC<TasksScreenProps> = ({ tasks = DEFAULT_REALISTIC_TASKS }) => {
  const { tone, isDark } = useAppTheme();


  const cardBg = isDark ? tone.surface : '#ffffff';

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
            <Text style={[styles.rolePillText, { color: tone.accent }]}>Tasks</Text>
          </View>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {/* Title */}
        <View style={styles.headerBlock}>
          <Text style={[styles.pageTitle, { color: tone.text1 }]}>Action tasks</Text>
          <Text style={[styles.pageSubtitle, { color: tone.text3 }]}>
            Casework queues, statutory deadlines & verification actions
          </Text>
        </View>

        {/* Task List or Calm Empty State */}
        {tasks.length === 0 ? (
          <View style={styles.emptyWrap}>
            <View style={styles.koshEmptyIcon}>
              <Kosh pose="calm" size={96} />
            </View>
            <Text style={[styles.emptyTitle, { color: tone.text1 }]}>All caught up</Text>
            <Text style={[styles.emptySubtitle, { color: tone.text3 }]}>
              No pending casework tasks assigned to your queue at this time.
            </Text>
          </View>
        ) : (
          <View style={[styles.groupedCard, { backgroundColor: cardBg }]}>
            {tasks.map((task) => (
              <View key={task.id} style={styles.taskCard}>
                <View style={styles.cardHeader}>
                  <View style={[styles.typeBadge, { backgroundColor: tone.accentContainer }]}>
                    <Text style={[styles.typeText, { color: tone.accent }]}>
                      {task.type.replace('_', ' ').toUpperCase()}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.urgencyBadge,
                      task.urgency === 'statutory_deadline' ? styles.urgencyStatutory : styles.urgencyHigh,
                    ]}
                  >
                    <Text style={styles.urgencyText}>{task.urgency.replace('_', ' ').toUpperCase()}</Text>
                  </View>
                </View>

                <Text style={[styles.taskTitle, { color: tone.text1 }]}>{task.title}</Text>
                <Text style={[styles.instText, { color: tone.text2 }]}>{task.institution_name}</Text>
                <Text style={[styles.instRef, { color: tone.text3 }]}>
                  Ref: {task.instrument_number} • Due: {task.due_date}
                </Text>
              </View>
            ))}
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
    marginBottom: 20,
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
    padding: 16,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
  },
  taskCard: {
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#f1f5f9',
    gap: 6,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  typeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  urgencyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  urgencyStatutory: {
    backgroundColor: '#fef2f2',
  },
  urgencyHigh: {
    backgroundColor: '#fffbeb',
  },
  urgencyText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#b91c1c',
  },
  taskTitle: {
    fontSize: 14,
    fontWeight: '700',
  },
  instText: {
    fontSize: 12,
  },
  instRef: {
    fontSize: 11,
  },
});
