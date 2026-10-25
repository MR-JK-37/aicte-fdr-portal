import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

export type ThemeMode = 'dark' | 'light' | 'system';

const STORAGE_KEY = 'aicte-fdr.theme';
const TRANSPARENCY_KEY = 'aicte-fdr.reduce-transparency';

function matchMediaSafe(query: string): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false;
  try {
    return window.matchMedia(query).matches;
  } catch {
    return false;
  }
}

function resolveSystemPrefersLight(): boolean {
  return matchMediaSafe('(prefers-color-scheme: light)');
}

interface ThemeContextValue {
  mode: ThemeMode;
  resolved: 'dark' | 'light';
  setMode: (m: ThemeMode) => void;
  reduceTransparency: boolean;
  setReduceTransparency: (v: boolean) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

/**
 * Applies `data-theme="dark|light"` and `data-reduce-transparency="true|false"`
 * on `<html>` per design/tokens.css's rules (the `@theme`/`:root[data-theme]`
 * blocks + the `.glass` opacity fallback keyed off
 * `:root[data-reduce-transparency="true"]`). Dark is the hero theme (design
 * default); `system` follows `prefers-color-scheme` as the no-JS CSS media
 * block already does, so this provider is progressive enhancement, not a
 * requirement for correct first paint.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    // Pure crisp white theme strictly matching ui-refrence.png
    return 'light';
  });
  const [reduceTransparency, setReduceTransparencyState] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    if (localStorage.getItem(TRANSPARENCY_KEY) === 'true') return true;
    return matchMediaSafe('(prefers-reduced-transparency: reduce)');
  });

  const resolved: 'dark' | 'light' = 'light';

  useEffect(() => {
    const html = document.documentElement;
    html.setAttribute('data-theme', 'light');
    try {
      localStorage.setItem(STORAGE_KEY, 'light');
    } catch {
      /* ignore */
    }
  }, [mode]);

  useEffect(() => {
    document.documentElement.setAttribute('data-reduce-transparency', String(reduceTransparency));
  }, [reduceTransparency]);

  const setMode = useCallback((m: ThemeMode) => {
    setModeState(m);
    try {
      localStorage.setItem(STORAGE_KEY, m);
    } catch {
      /* private mode / storage disabled — theme just won't persist */
    }
  }, []);

  const setReduceTransparency = useCallback((v: boolean) => {
    setReduceTransparencyState(v);
    try {
      localStorage.setItem(TRANSPARENCY_KEY, String(v));
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo(
    () => ({ mode, resolved, setMode, reduceTransparency, setReduceTransparency }),
    [mode, resolved, setMode, reduceTransparency, setReduceTransparency],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme() must be used within <ThemeProvider>');
  return ctx;
}
