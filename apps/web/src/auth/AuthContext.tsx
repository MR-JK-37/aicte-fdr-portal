import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api } from '../lib/apiClient';
import type { paths } from '@aicte-fdr/api-client';

type UserProfile = paths['/v1/me']['get']['responses'][200]['content']['application/json'];
type NavigationManifest =
  paths['/v1/me/navigation']['get']['responses'][200]['content']['application/json'];

interface AuthContextValue {
  user: UserProfile | null;
  navigation: NavigationManifest | null;
  status: 'checking' | 'signed-out' | 'signed-in';
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [navigation, setNavigation] = useState<NavigationManifest | null>(null);
  const [status, setStatus] = useState<AuthContextValue['status']>('checking');

  const refresh = useCallback(async () => {
    const { data: me, error: meError } = await api.GET('/v1/me');
    if (meError || !me) {
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

  useEffect(() => {
    refresh();
  }, [refresh]);

  const logout = useCallback(async () => {
    await api.POST('/v1/auth/logout');
    setUser(null);
    setNavigation(null);
    setStatus('signed-out');
  }, []);

  return (
    <AuthContext.Provider value={{ user, navigation, status, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
