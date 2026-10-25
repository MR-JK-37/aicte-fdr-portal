import React from 'react';

export interface WordmarkProps {
  big?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Wordmark component: "fdr·portal" (heavy lowercase with a blue ring-and-dot mark).
 * Never reproduces the reference product's brand assets.
 */
export const Wordmark: React.FC<WordmarkProps> = ({ big = false, className = '', style }) => {
  return (
    <div
      data-testid="wordmark"
      className={`wm ${big ? 'big' : ''} ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '2px',
        fontFamily: 'var(--font-display, "Plus Jakarta Sans", sans-serif)',
        fontWeight: 800,
        fontSize: big ? '24px' : '20px',
        lineHeight: 1,
        letterSpacing: '-0.04em',
        color: 'var(--text1, #14141a)',
        textDecoration: 'none',
        userSelect: 'none',
        ...style,
      }}
    >
      <span>fdr</span>
      <svg
        width={big ? 26 : 22}
        height={big ? 26 : 22}
        viewBox="0 0 26 26"
        aria-hidden="true"
        style={{ margin: '0 1px', flexShrink: 0 }}
      >
        <circle cx="13" cy="13" r="10" fill="none" stroke="var(--azure, #3b78d8)" strokeWidth="4" />
        <circle cx="13" cy="13" r="3.6" fill="var(--ink, #1a1a1e)" />
      </svg>
      <span>portal</span>
    </div>
  );
};
