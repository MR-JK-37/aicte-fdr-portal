import createClient from 'openapi-fetch';
import type { paths } from './generated/schema';

/**
 * Thin wrapper over `openapi-fetch`, typed from the generated OpenAPI
 * schema (`npm run generate`, see README). Every call site gets
 * request/response types for free and a compile error the moment the
 * backend's real contract changes underneath it.
 */
export function createApiClient(baseUrl: string) {
  // credentials: 'include' — the backend's session/refresh tokens are httponly
  // cookies (app/auth/router.py); without this, the browser never sends them.
  //
  // `fetch` is passed as a thin dynamic wrapper, not the bare global: openapi-fetch
  // defaults its internal `baseFetch` to `globalThis.fetch` evaluated ONCE at
  // createClient() call time, so anything that swaps `globalThis.fetch` afterwards
  // (e.g. `vi.stubGlobal('fetch', ...)` in tests, or any runtime fetch
  // instrumentation) would otherwise be silently ignored by this client.
  return createClient<paths>({
    baseUrl,
    credentials: 'include',
    fetch: (...args: Parameters<typeof fetch>) => globalThis.fetch(...args),
  });
}

export type { paths } from './generated/schema';
