import React from 'react';
import { Icon, type IconName } from './Icon';
import { Kosh } from './Kosh';

export interface SidebarItem {
  key: string;
  label: string;
  icon: IconName;
}

export interface SidebarProps {
  items: SidebarItem[];
  activeKey: string;
  onSelect: (key: string) => void;
  className?: string;
  style?: React.CSSProperties;
  tinted?: boolean;
  onOpenAskHandbook?: () => void;
}

/**
 * Floating Sidebar Card (Stream R5.4 / DESIGN_SPEC §5.13 / G-24).
 * Solid white surface, radius 20, soft shadow, pill navigation buttons
 * with Phosphor azure duotone icons and capsule active state.
 * Includes "Need help? Ask the handbook" with Kosh mascot (ui-refrence.png).
 */
export const Sidebar: React.FC<SidebarProps> = ({
  items,
  activeKey,
  onSelect,
  className = '',
  style,
  onOpenAskHandbook,
}) => {
  return (
    <aside
      className={`sidebar-card ${className}`}
      style={style}
      aria-label="Navigation Sidebar"
    >
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }}>
        {items.map((item) => {
          const isActive = item.key === activeKey;
          return (
            <button
              key={item.key}
              type="button"
              className={`sidebar-item ${isActive ? 'is-active' : ''}`}
              aria-current={isActive ? 'page' : undefined}
              onClick={() => onSelect(item.key)}
            >
              <Icon name={item.icon} size={20} color="var(--azure)" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {onOpenAskHandbook && (
        <div
          data-testid="sidebar-ask-handbook"
          className="sideft"
          onClick={onOpenAskHandbook}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onOpenAskHandbook();
            }
          }}
          title="Ask Approval Process Handbook"
        >
          <Kosh size={72} pose="smile" />
          <small>Need help? Ask the handbook</small>
        </div>
      )}
    </aside>
  );
};
