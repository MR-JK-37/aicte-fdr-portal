import React from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Platform } from 'react-native';
import { Icon, type IconName } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { MobileTab } from '../types';

interface NavigationTabBarProps {
  currentTab: MobileTab;
  onSelectTab: (tab: MobileTab) => void;
  inboxUnreadCount?: number;
  tasksPendingCount?: number;
}

interface TabItem {
  key: MobileTab;
  label: string;
  icon: IconName;
}

/**
 * Lavender Ledger Floating Pill Tab Bar (DESIGN_SPEC §4, §5.4, §9):
 * White pill (radius 28, floating shadow, 12px inset, height 64) with active capsule in
 * `primaryContainer`, `primary` active text, azure duotone icons, and red notification badge.
 */
export const NavigationTabBar: React.FC<NavigationTabBarProps> = ({
  currentTab,
  onSelectTab,
  inboxUnreadCount = 0,
  tasksPendingCount = 0,
}) => {
  const { tone, isDark } = useAppTheme();

  const tabs: TabItem[] = [
    { key: 'home', label: 'Home', icon: 'dashboard' },
    { key: 'cases', label: 'Cases', icon: 'instrument' },
    { key: 'inbox', label: 'Inbox', icon: 'inbox' },
    { key: 'tasks', label: 'Tasks', icon: 'checklist' },
    { key: 'more', label: 'More', icon: 'settings' },
  ];

  return (
    <View style={styles.outerWrapper}>
      <View
        style={[
          styles.container,
          {
            backgroundColor: isDark ? tone.surface : '#ffffff',
            shadowColor: '#1e1b4b',
            shadowOpacity: isDark ? 0.35 : 0.08,
          },
        ]}
      >
        {tabs.map((tab) => {
          const active = currentTab === tab.key;
          const showBadge =
            (tab.key === 'inbox' && inboxUnreadCount > 0) ||
            (tab.key === 'tasks' && tasksPendingCount > 0);
          const badgeCount = tab.key === 'inbox' ? inboxUnreadCount : tasksPendingCount;

          return (
            <TouchableOpacity
              key={tab.key}
              style={styles.tabButton}
              onPress={() => onSelectTab(tab.key)}
              accessibilityRole="tab"
              accessibilityState={{ selected: active }}
              accessibilityLabel={tab.label}
            >
              <View
                style={[
                  styles.iconWrapper,
                  active && {
                    backgroundColor: isDark ? 'rgba(59, 130, 246, 0.2)' : tone.accentContainer,
                  },
                ]}
              >
                <Icon
                  name={tab.icon}
                  size={22}
                  color={active ? tone.accent : '#64748b'}
                  filled={active}
                />
                {showBadge && (
                  <View style={styles.badge}>
                    <Text style={styles.badgeText}>{badgeCount}</Text>
                  </View>
                )}
              </View>
              <Text
                style={[
                  styles.tabLabel,
                  active
                    ? [styles.tabLabelActive, { color: isDark ? tone.accent : '#1d4ed8' }]
                    : { color: '#64748b' },
                ]}
              >
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  outerWrapper: {
    position: 'relative',
    backgroundColor: 'transparent',
    paddingHorizontal: 12,
    paddingBottom: Platform.OS === 'ios' ? 24 : 12,
  },
  container: {
    flexDirection: 'row',
    height: 64,
    borderRadius: 28,
    borderWidth: 0,
    paddingHorizontal: 6,
    justifyContent: 'space-around',
    alignItems: 'center',
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 16,
    elevation: 8,
  },
  tabButton: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
    flex: 1,
  },
  iconWrapper: {
    position: 'relative',
    paddingHorizontal: 14,
    paddingVertical: 4,
    borderRadius: 16,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '600',
  },
  tabLabelActive: {
    fontWeight: '700',
  },
  badge: {
    position: 'absolute',
    top: 0,
    right: 4,
    minWidth: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: '#ef4444',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 2,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 8,
    fontWeight: '800',
  },
});
