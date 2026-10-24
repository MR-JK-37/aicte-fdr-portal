import React, { useState } from 'react';
import { StyleSheet, View, Text, ScrollView, TouchableOpacity, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { MobileTask } from '../types';

interface TasksScreenProps {
  onTaskResolved?: (taskId: string) => void;
}

export const TasksScreen: React.FC<TasksScreenProps> = ({ onTaskResolved }) => {
  const [tasks, setTasks] = useState<MobileTask[]>([
    {
      id: 'task-301',
      title: 'Review OCR Candidate Extraction (AXIS-FDR-99201)',
      type: 'intake_review',
      instrument_number: 'AXIS-FDR-99201',
      institution_name: 'Delhi Global Technical Campus',
      assigned_role: 'scrutiny_officer',
      due_date: '2026-10-25',
      urgency: 'high',
    },
    {
      id: 'task-302',
      title: 'Confirm Table 1.4 Shortfall Casework (PNB-771829)',
      type: 'discrepancy_casework',
      instrument_number: 'PNB-771829',
      institution_name: 'St. Mary’s Polytechnic College',
      assigned_role: 'scrutiny_officer',
      due_date: '2026-10-26',
      urgency: 'statutory_deadline',
    },
    {
      id: 'task-303',
      title: 'Second-Person UTR Release Execution Review (HDFC-441029)',
      type: 'execution_proof',
      instrument_number: 'HDFC-441029',
      institution_name: 'National College of Engineering',
      assigned_role: 'competent_authority',
      due_date: '2026-10-24',
      urgency: 'high',
    },
  ]);

  const [toast, setToast] = useState<string | null>(null);

  const handleActionTask = (taskId: string, actionName: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    setToast(`Task ${taskId} resolved: ${actionName}`);
    if (onTaskResolved) onTaskResolved(taskId);
    setTimeout(() => setToast(null), 3000);
  };

  return (
    <View style={styles.container}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <View>
          <Text style={styles.headerSuper}>ROLE WORKLOAD & ACTIONS</Text>
          <Text style={styles.headerTitle}>Casework Tasks Queue</Text>
        </View>
        <View style={styles.countBadge}>
          <Text style={styles.countText}>{tasks.length} Pending</Text>
        </View>
      </View>

      {toast && (
        <View style={styles.toastBanner}>
          <Icon name="success" size={14} color="#3ddc97" />
          <Text style={styles.toastText}>{toast}</Text>
        </View>
      )}

      {/* Task List */}
      <ScrollView contentContainerStyle={styles.listContent}>
        {tasks.length === 0 ? (
          <View style={styles.emptyBox}>
            <Icon name="success" size={48} color="#3ddc97" />
            <Text style={styles.emptyTitle}>All Tasks Up to Date</Text>
            <Text style={styles.emptyDesc}>No regulatory intake reviews or release approvals pending for your assigned role.</Text>
          </View>
        ) : (
          tasks.map((task) => (
            <View key={task.id} style={styles.taskCard}>
              <View style={styles.cardHeader}>
                <View style={styles.typeBadge}>
                  <Text style={styles.typeText}>{task.type.replace('_', ' ').toUpperCase()}</Text>
                </View>
                <View style={[styles.urgencyBadge, task.urgency === 'statutory_deadline' ? styles.urgencyStatutory : styles.urgencyHigh]}>
                  <Text style={styles.urgencyText}>{task.urgency.replace('_', ' ').toUpperCase()}</Text>
                </View>
              </View>

              <Text style={styles.taskTitle}>{task.title}</Text>
              <Text style={styles.instText}>{task.institution_name}</Text>
              <Text style={styles.instRef}>Ref: {task.instrument_number} • Due: {task.due_date}</Text>

              <View style={styles.cardActions}>
                <TouchableOpacity
                  style={styles.actionBtnPrimary}
                  onPress={() => handleActionTask(task.id, 'Approved & Signed')}
                >
                  <Icon name="verified" size={13} color="#050505" />
                  <Text style={styles.actionBtnTextPrimary}>Verify & Approve</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.actionBtnSecondary}
                  onPress={() => handleActionTask(task.id, 'Discrepancy Flagged')}
                >
                  <Text style={styles.actionBtnTextSecondary}>Flag Casework</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
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
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
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
  countBadge: {
    backgroundColor: 'rgba(0, 238, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.3)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  countText: {
    color: '#00eeff',
    fontSize: 11,
    fontWeight: '700',
  },
  toastBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(61, 220, 151, 0.15)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(61, 220, 151, 0.3)',
  },
  toastText: {
    color: '#3ddc97',
    fontSize: 11,
    fontWeight: '600',
  },
  listContent: {
    padding: 16,
    gap: 12,
  },
  taskCard: {
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
  typeBadge: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  typeText: {
    color: '#94a3b8',
    fontSize: 9,
    fontWeight: '700',
  },
  urgencyBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  urgencyStatutory: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  urgencyHigh: {
    backgroundColor: 'rgba(251, 191, 36, 0.2)',
  },
  urgencyText: {
    color: '#f8fafc',
    fontSize: 9,
    fontWeight: '700',
  },
  taskTitle: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
    marginTop: 2,
  },
  instText: {
    color: '#cbd5e1',
    fontSize: 12,
  },
  instRef: {
    color: '#64748b',
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  cardActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    paddingTop: 10,
  },
  actionBtnPrimary: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#00eeff',
    borderRadius: 8,
    paddingVertical: 8,
  },
  actionBtnTextPrimary: {
    color: '#050505',
    fontSize: 11,
    fontWeight: '700',
  },
  actionBtnSecondary: {
    paddingHorizontal: 12,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderRadius: 8,
  },
  actionBtnTextSecondary: {
    color: '#f87171',
    fontSize: 11,
    fontWeight: '600',
  },
  emptyBox: {
    alignItems: 'center',
    gap: 12,
    paddingVertical: 48,
    paddingHorizontal: 24,
  },
  emptyTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  emptyDesc: {
    color: '#94a3b8',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 16,
  },
});
