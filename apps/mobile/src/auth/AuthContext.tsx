import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import {
  api,
  setAccessToken,
  getAccessToken,
  persistRefreshToken,
  clearRefreshToken,
  tryRefreshSession,
} from '../lib/apiClient';
import type { paths } from '@aicte-fdr/api-client';

type UserProfile = paths['/v1/me']['get']['responses'][200]['content']['application/json'];
type NavigationManifest =
  paths['/v1/me/navigation']['get']['responses'][200]['content']['application/json'];

interface AuthContextValue {
  user: UserProfile | null;
  navigation: NavigationManifest | null;
  status: 'checking' | 'signed-out' | 'signed-in';
  /** Called after a successful /auth/login response to adopt the session. */
  adoptSession: (accessToken: string, refreshToken: string) => Promise<void>;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [navigation, setNavigation] = useState<NavigationManifest | null>(null);
  const [status, setStatus] = useState<AuthContextValue['status']>('checking');

  const loadMe = useCallback(async () => {
    const { data: me } = await api.GET('/v1/me');
    if (!me) {
      setUser(null);
      setNavigation(null);
      setStatus('signed-out');
      return;
    }
    setUser(me);
    const { data: nav } = await api.GET('/v1/me/navigation');
    setNavigation(nav ?? null);
    setStatus('signed-in');
  }, []);

  const refresh = useCallback(async () => {
    // No in-memory access token yet (fresh app launch) — try the stored
    // refresh token (Keychain/Keystore) before giving up as signed-out.
    if (!getAccessToken()) {
      const restored = await tryRefreshSession();
      if (!restored) {
        setStatus('signed-out');
        return;
      }
    }
    await loadMe();
  }, [loadMe]);

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const adoptSession = useCallback(
    async (accessToken: string, refreshToken: string) => {
      setAccessToken(accessToken);
      await persistRefreshToken(refreshToken);
      await loadMe();
    },
    [loadMe]
  );

  const logout = useCallback(async () => {
    await api.POST('/v1/auth/logout');
    setAccessToken(null);
    await clearRefreshToken();
    setUser(null);
    setNavigation(null);
    setStatus('signed-out');
  }, []);

  return (
    <AuthContext.Provider value={{ user, navigation, status, adoptSession, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
