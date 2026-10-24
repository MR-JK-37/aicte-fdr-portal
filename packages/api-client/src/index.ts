import createClient from 'openapi-fetch';
import type { paths } from './generated/schema';

/**
 * Thin wrapper over `openapi-fetch`, typed from the generated OpenAPI
 * schema (`npm run generate`, see README). Every call site gets
 * request/response types for free and a compile error the moment the
 * backend's real contract changes underneath it.
 */
export function createApiClient(baseUrl: string) {
  return createClient<paths>({ baseUrl });
}

export type { paths } from './generated/schema';
