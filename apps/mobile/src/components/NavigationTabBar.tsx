import React from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Platform } from 'react-native';
import { Icon, IconName } from '../design-system/Icon';
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

export const NavigationTabBar: React.FC<NavigationTabBarProps> = ({
  currentTab,
  onSelectTab,
  inboxUnreadCount = 0,
  tasksPendingCount = 0,
}) => {
  const tabs: TabItem[] = [
    { key: 'home', label: 'Home', icon: 'dashboard' },
    { key: 'cases', label: 'Cases', icon: 'instrument' },
    { key: 'inbox', label: 'Inbox', icon: 'inbox' },
    { key: 'tasks', label: 'Tasks', icon: 'checklist' },
    { key: 'more', label: 'More', icon: 'settings' },
  ];

  return (
    <View style={styles.container}>
      {tabs.map((tab) => {
        const active = currentTab === tab.key;
        const showBadge = (tab.key === 'inbox' && inboxUnreadCount > 0) || (tab.key === 'tasks' && tasksPendingCount > 0);
        const badgeCount = tab.key === 'inbox' ? inboxUnreadCount : tasksPendingCount;

        return (
          <TouchableOpacity
            key={tab.key}
            style={styles.tabButton}
            onPress={() => onSelectTab(tab.key)}
          >
            <View style={[styles.iconWrapper, active && styles.activeIndicator]}>
              <Icon
                name={tab.icon}
                size={22}
                color={active ? '#00eeff' : '#94a3b8'}
                filled={active}
              />
              {showBadge && (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{badgeCount}</Text>
                </View>
              )}
            </View>
            <Text style={[styles.tabLabel, active && styles.tabLabelActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    height: Platform.OS === 'ios' ? 78 : 64,
    backgroundColor: '#0c0716',
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 238, 255, 0.2)',
    paddingBottom: Platform.OS === 'ios' ? 18 : 6,
    paddingTop: 6,
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  tabButton: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
    flex: 1,
  },
  iconWrapper: {
    position: 'relative',
    paddingHorizontal: 16,
    paddingVertical: 4,
    borderRadius: 14,
  },
  activeIndicator: {
    backgroundColor: 'rgba(0, 238, 255, 0.12)',
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#94a3b8',
  },
  tabLabelActive: {
    color: '#00eeff',
    fontWeight: '700',
  },
  badge: {
    position: 'absolute',
    top: 0,
    right: 8,
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
