import React from 'react';
import clsx from 'clsx';
import { Icon, type IconName } from './Icon';

export interface SidebarItem {
  key: string;
  label: string;
  icon: IconName;
}

export interface SidebarProps {
  items: SidebarItem[];
  activeKey: string;
  onSelect: (key: string) => void;
  collapsed?: boolean;
  brand?: React.ReactNode;
  /** Violet-tinted glass variant (DESIGN_SPEC §13.1: violet is tint/glow only, never text/icon colour). */
  tinted?: boolean;
}

/**
 * Navigation-layer Liquid Glass shell (DESIGN_SPEC §6/§13.2). Uses the
 * shared `.glass` class from tokens.css, which already implements the
 * `backdrop-filter: blur(24px) saturate(180%)` recipe with -webkit- prefix,
 * the `@supports not (backdrop-filter)` fallback, and the
 * `prefers-reduced-transparency` / `data-reduce-transparency="true"` /
 * `prefers-contrast: more` opaque overrides — nothing re-implemented here.
 */
export function Sidebar({ items, activeKey, onSelect, collapsed, brand, tinted }: SidebarProps) {
  return (
    <nav
      className={clsx('ds-sidebar glass glass--panel', tinted && 'glass--violet', collapsed && 'ds-sidebar--collapsed')}
      aria-label="Primary"
    >
      {brand && <div className="ds-sidebar__brand">{brand}</div>}
      <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {items.map((item) => (
          <li key={item.key}>
            <button
              type="button"
              className={clsx('ds-sidebar__item', item.key === activeKey && 'ds-sidebar__item--active')}
              aria-current={item.key === activeKey ? 'page' : undefined}
              onClick={() => onSelect(item.key)}
            >
              <Icon name={item.icon} size={20} />
              {!collapsed && <span>{item.label}</span>}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
