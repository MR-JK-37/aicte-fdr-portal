import createClient from 'openapi-fetch';
import type { paths } from '@aicte-fdr/api-client';
import { getSecureItem, setSecureItem, deleteSecureItem } from './secureStorage';

import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * Dynamically resolves the API Base URL:
 * - If EXPO_PUBLIC_API_URL is explicitly set, use it.
 * - On physical devices or Expo Go, auto-detect the dev machine's LAN IP from Metro's hostUri.
 * - In web browser preview on the machine, defaults to localhost:8000.
 * - Fallback to 192.168.31.237:8000 (prevents Android java.net.ConnectException: localhost/127.0.0.1:8000).
 */
function resolveApiBaseUrl(): string {
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }
  const hostUri =
    Constants.expoConfig?.hostUri ||
    (Constants as any).manifest?.debuggerHost ||
    (Constants as any).manifest2?.extra?.expoGo?.debuggerHost;

  if (hostUri) {
    const hostIp = hostUri.split(':')[0];
    if (hostIp && hostIp !== 'localhost' && hostIp !== '127.0.0.1') {
      return `http://${hostIp}:8000`;
    }
  }

  if (Platform.OS === 'web') {
    return 'http://localhost:8000';
  }

  return 'http://192.168.31.237:8000';
}

export const API_BASE_URL = resolveApiBaseUrl();

const REFRESH_TOKEN_KEY = 'fdr_refresh_token';

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export async function persistRefreshToken(token: string) {
  await setSecureItem(REFRESH_TOKEN_KEY, token);
}

export async function loadRefreshToken(): Promise<string | null> {
  return getSecureItem(REFRESH_TOKEN_KEY);
}

export async function clearRefreshToken() {
  await deleteSecureItem(REFRESH_TOKEN_KEY);
}

// Dynamic wrapper (not a bare `fetch` reference) for the same reason
// documented in packages/api-client/src/index.ts: avoids binding to whatever
// `globalThis.fetch` happened to be at module-import time, which breaks
// anything that swaps it later (tests, polyfills).
//
// openapi-fetch calls this as `fetch(request, requestInitExt)` where `request`
// is an already-built `Request` (method/body/Content-Type baked in) and
// `requestInitExt` is a separate, mostly-empty init object. Building headers
// from ONLY `init?.headers` (ignoring `input`'s own headers when `input` is a
// Request) silently drops Content-Type — passing that empty Headers object as
// the second arg to fetch(request, init) then overrides the Request's real
// headers per the Fetch spec, so the server receives the JSON body with no
// Content-Type and fails to parse it. Start from the Request's own headers.
const mobileFetch: typeof fetch = (...args) => {
  const [input, init] = args;
  const headers = new Headers(input instanceof Request ? input.headers : init?.headers);
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  return globalThis.fetch(input, { ...init, headers });
};

export const api = createClient<paths>({ baseUrl: API_BASE_URL, fetch: mobileFetch });

/** Exchanges the stored refresh token for a new access+refresh pair. Returns
 * false (and clears the stored token) if the refresh token is invalid,
 * expired, or was flagged as reused (app/auth/router.py's theft detection) —
 * callers should treat that as "sign in again", never retry silently. */
export async function tryRefreshSession(): Promise<boolean> {
  const refreshToken = await loadRefreshToken();
  if (!refreshToken) return false;

  const { data } = await api.POST('/v1/auth/refresh', {
    body: { refresh_token: refreshToken },
  });
  if (!data) {
    await clearRefreshToken();
    setAccessToken(null);
    return false;
  }
  setAccessToken(data.access_token);
  await persistRefreshToken(data.refresh_token);
  return true;
}
