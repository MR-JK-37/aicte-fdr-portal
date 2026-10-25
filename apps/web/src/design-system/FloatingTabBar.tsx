import React from 'react';
import { Icon, type IconName } from './Icon';

export interface TabItem {
  id: string;
  label: string;
  icon: IconName;
}

export interface FloatingTabBarProps {
  items: TabItem[];
  activeId: string;
  onSelect: (id: string) => void;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * FloatingTabBar: white pill tab bar (radius 28, floating shadow, 12px side inset, 64px high)
 * All icons are azure duotone; inactive labels are text1 bold 11px;
 * active tab gets a light-blue capsule (primaryContainer) and primary bold label.
 * (DESIGN_SPEC §5.4 / G-24).
 */
export const FloatingTabBar: React.FC<FloatingTabBarProps> = ({
  items,
  activeId,
  onSelect,
  className = '',
  style,
}) => {
  return (
    <nav data-testid="tabbar" className={`tabbar ${className}`} style={style} role="tablist">
      {items.map((tab) => {
        const isActive = tab.id === activeId;
        return (
          <a
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            aria-current={isActive ? 'page' : undefined}
            data-testid={`tab-${tab.id}`}
            onClick={(e) => {
              e.preventDefault();
              onSelect(tab.id);
            }}
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelect(tab.id);
              }
            }}
          >
            <Icon name={tab.icon} size={24} color="var(--azure)" />
            <span>{tab.label}</span>
          </a>
        );
      })}
    </nav>
  );
};
