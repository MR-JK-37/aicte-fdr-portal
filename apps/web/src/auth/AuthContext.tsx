import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { api } from '../lib/apiClient';
import type { paths } from '@aicte-fdr/api-client';

type UserProfile = paths['/v1/me']['get']['responses'][200]['content']['application/json'];
type NavigationManifest =
  paths['/v1/me/navigation']['get']['responses'][200]['content']['application/json'];

interface AuthContextValue {
  user: UserProfile | null;
  navigation: NavigationManifest | null;
  status: 'checking' | 'signed-out' | 'signed-in';
  // Set when the last `refresh()` attempt failed to even reach the server
  // (network error, timeout, cold-starting backend that never came up in
  // time) — distinct from a clean 401, which just means "not logged in".
  serverUnreachable: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// The backend runs on Render's free tier, which spins the instance down after
// ~15 minutes idle and cold-starts it on the next request (commonly 30-60s,
// see .github/workflows/keep-alive.yml). A single request-level timeout
// shorter than that would misclassify a slow-but-healthy cold start as a
// failure, so each attempt gets a generous window and we retry a few times
// with backoff rather than failing fast.
const ATTEMPT_TIMEOUT_MS = 20_000;
const MAX_ATTEMPTS = 4;
const RETRY_DELAY_MS = [2_000, 5_000, 10_000];

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [navigation, setNavigation] = useState<NavigationManifest | null>(null);
  const [status, setStatus] = useState<AuthContextValue['status']>('checking');
  const [serverUnreachable, setServerUnreachable] = useState(false);
  // Guards against a stale in-flight refresh() clobbering state set by a
  // newer one (e.g. user hits "Retry" while a slow cold-start request from
  // the first attempt is still pending).
  const refreshIdRef = useRef(0);

  const refresh = useCallback(async () => {
    const refreshId = ++refreshIdRef.current;
    setStatus('checking');
    setServerUnreachable(false);

    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
      try {
        const { data: me, error: meError } = await api.GET('/v1/me', {
          signal: AbortSignal.timeout(ATTEMPT_TIMEOUT_MS),
        });
        if (refreshId !== refreshIdRef.current) return; // superseded by a newer refresh()

        if (meError || !me) {
          // A clean response from a live server saying "not authenticated" —
          // not a connectivity problem. Stop immediately, no retry.
          setUser(null);
          setNavigation(null);
          setStatus('signed-out');
          return;
        }

        setUser(me);
        try {
          const { data: nav } = await api.GET('/v1/me/navigation', {
            signal: AbortSignal.timeout(ATTEMPT_TIMEOUT_MS),
          });
          if (refreshId !== refreshIdRef.current) return;
          setNavigation(nav ?? null);
        } catch {
          // Navigation manifest is a secondary concern; don't block sign-in on it.
          if (refreshId !== refreshIdRef.current) return;
          setNavigation(null);
        }
        setStatus('signed-in');
        return;
      } catch {
        // Network error, aborted/timed-out request, or the backend still
        // cold-starting. Retry with backoff instead of hanging on
        // "checking" forever or giving up after one blip.
        if (refreshId !== refreshIdRef.current) return;
        if (attempt < MAX_ATTEMPTS) {
          await sleep(RETRY_DELAY_MS[attempt - 1]);
          if (refreshId !== refreshIdRef.current) return;
          continue;
        }
        // Exhausted retries: surface a definitive, non-hanging error state
        // instead of leaving the UI stuck on a blank "Loading…" screen.
        setUser(null);
        setNavigation(null);
        setStatus('signed-out');
        setServerUnreachable(true);
        return;
      }
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const logout = useCallback(async () => {
    try {
      await api.POST('/v1/auth/logout', { signal: AbortSignal.timeout(ATTEMPT_TIMEOUT_MS) });
    } catch {
      // Best-effort: even if the logout call fails to reach the server, clear
      // local session state so the user isn't stuck in a "signed-in" UI.
    }
    setUser(null);
    setNavigation(null);
    setStatus('signed-out');
  }, []);

  return (
    <AuthContext.Provider value={{ user, navigation, status, serverUnreachable, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
