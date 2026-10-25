import { createApiClient } from '@aicte-fdr/api-client';

// Same-origin base URL — Vite's dev proxy (vite.config.ts) forwards /v1 to the
// real backend so cookies stay same-origin; production serves both from the
// same origin behind the reverse proxy (infra/caddy). Resolved from
// window.location.origin (not a bare '') because the WHATWG Request/URL
// constructors used under Node/jsdom (vitest) require an absolute base,
// unlike a real browser's relative-fetch resolution.
export const api = createApiClient(
  typeof window !== 'undefined' ? window.location.origin : ''
);
