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

/** Exchanges the stored refresh token for a new access+refresh pair via a raw
 * fetch (never through `api`/`mobileFetch` — that would recurse back into
 * the 401-retry logic below if the refresh call itself ever 401s, e.g. a
 * reused/expired refresh token). Returns false (and clears the stored token)
 * if the refresh token is invalid, expired, or was flagged as reused
 * (app/auth/router.py's theft detection) — callers should treat that as
 * "sign in again", never retry silently. */
async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = await loadRefreshToken();
  if (!refreshToken) return false;

  const res = await globalThis.fetch(`${API_BASE_URL}/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) {
    await clearRefreshToken();
    setAccessToken(null);
    return false;
  }
  const data = await res.json();
  setAccessToken(data.access_token);
  await persistRefreshToken(data.refresh_token);
  return true;
}

export async function tryRefreshSession(): Promise<boolean> {
  return refreshAccessToken();
}

// Shares one in-flight refresh across concurrent 401s instead of firing a
// refresh call per failed request.
let inFlightRefresh: Promise<boolean> | null = null;

function refreshOnce(): Promise<boolean> {
  if (!inFlightRefresh) {
    inFlightRefresh = refreshAccessToken().finally(() => {
      inFlightRefresh = null;
    });
  }
  return inFlightRefresh;
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
//
// Also retries once on a 401: the access token is short-lived (15 min) and
// nothing else in the app refreshes it proactively, so without this every
// screen silently stops loading data ~15 minutes into a session until the
// user manually signs out and back in. The refresh endpoint itself is never
// retried this way (see refreshAccessToken) to avoid recursing.
//
// `input` is cloned before every actual fetch, never issued directly: a
// Request's body stream can only be read once, so retrying the *same*
// Request object on a POST/PUT/PATCH would send an empty body the second
// time. Cloning `input` itself (rather than the already-used clone) keeps it
// pristine so it can be cloned again if a retry is needed.
const mobileFetch: typeof fetch = async (...args) => {
  const [input, init] = args;
  const isRequest = input instanceof Request;
  const url = isRequest ? input.url : String(input);
  const isRefreshCall = url.includes('/v1/auth/refresh');

  const doFetch = () => {
    const source = isRequest ? (input as Request).clone() : input;
    const headers = new Headers(isRequest ? (source as Request).headers : init?.headers);
    if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
    return globalThis.fetch(source, { ...init, headers });
  };

  let response = await doFetch();

  if (response.status === 401 && !isRefreshCall && accessToken) {
    const refreshed = await refreshOnce();
    if (refreshed) {
      response = await doFetch();
    }
  }

  return response;
};

export const api = createClient<paths>({ baseUrl: API_BASE_URL, fetch: mobileFetch });
