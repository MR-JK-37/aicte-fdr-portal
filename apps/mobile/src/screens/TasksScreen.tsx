import React, { useEffect, useState, useCallback } from 'react';
import { StyleSheet, View, Text, ScrollView, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { Kosh } from '../design-system/Kosh';
import { api } from '../lib/apiClient';
import type { paths } from '@aicte-fdr/api-client';

type QueueItem = paths['/v1/queues/intake']['get']['responses'][200]['content']['application/json'][number];

interface DisplayTask {
  id: string;
  title: string;
  type: string;
  instrument_number: string | null;
  institution_name: string;
  due_date: string;
  queue: 'Intake' | 'Scrutiny';
}

function toDisplayTask(item: QueueItem, queue: 'Intake' | 'Scrutiny'): DisplayTask {
  return {
    id: item.case_id,
    title: item.title,
    type: item.entity_type,
    instrument_number: null,
    institution_name: item.institution_name,
    due_date: new Date(item.created_at).toLocaleDateString(),
    queue,
  };
}

/**
 * Mobile Tasks Screen
 * Lavender Ledger layout: Topbar, page header, grouped list / calm Kosh empty state
 *
 * Reads the real intake and scrutiny casework queues (GET /v1/queues/intake,
 * GET /v1/queues/scrutiny) — no hardcoded sample casework (CLAUDE.md
 * non-negotiable #1).
 */
export const TasksScreen: React.FC = () => {
  const { tone, isDark } = useAppTheme();
  const [tasks, setTasks] = useState<DisplayTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    const [intake, scrutiny] = await Promise.all([
      api.GET('/v1/queues/intake'),
      api.GET('/v1/queues/scrutiny'),
    ]);
    if (!intake.data && !scrutiny.data) {
      setUnavailable(true);
      setTasks([]);
      setLoading(false);
      return;
    }
    setUnavailable(false);
    setTasks([
      ...(intake.data ?? []).map((i) => toDisplayTask(i, 'Intake')),
      ...(scrutiny.data ?? []).map((i) => toDisplayTask(i, 'Scrutiny')),
    ]);
    setLoading(false);
  }, []);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

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
        {loading ? (
          <Text style={{ fontSize: 12, color: tone.text3, textAlign: 'center', marginTop: 24 }}>
            Loading casework queues…
          </Text>
        ) : unavailable ? (
          <View style={styles.emptyWrap}>
            <View style={styles.koshEmptyIcon}>
              <Kosh pose="calm" size={96} />
            </View>
            <Text style={[styles.emptyTitle, { color: tone.text1 }]}>Queues unavailable</Text>
            <Text style={[styles.emptySubtitle, { color: tone.text3 }]}>
              Casework queues could not be reached. Your role may not be entitled to view them, or
              the server is temporarily unavailable.
            </Text>
          </View>
        ) : tasks.length === 0 ? (
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
                  <View style={[styles.urgencyBadge, styles.urgencyHigh]}>
                    <Text style={styles.urgencyText}>{task.queue.toUpperCase()} QUEUE</Text>
                  </View>
                </View>

                <Text style={[styles.taskTitle, { color: tone.text1 }]}>{task.title}</Text>
                <Text style={[styles.instText, { color: tone.text2 }]}>{task.institution_name}</Text>
                <Text style={[styles.instRef, { color: tone.text3 }]}>
                  Entered queue: {task.due_date}
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
