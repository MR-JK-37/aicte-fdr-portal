export * from './types';
export * from './loader';
export * from './format';

import { loadCatalog } from './loader';
import { formatICU } from './format';
import type { Locale } from './types';

/**
 * Creates a `t(key, values?)` translator bound to one locale, applying the
 * reviewed-only-in-production rule from `loadCatalog`. This is the entry
 * point apps/web and apps/mobile should use.
 */
export function createTranslator(locale: Locale, options?: { reviewedOnly?: boolean }) {
  const messages = loadCatalog(locale, options);
  return function t(key: string, values?: Record<string, string | number | Date>): string {
    const message = messages[key];
    if (message === undefined) {
      // Missing key entirely (not even in English) — surface loudly in dev,
      // never silently render nothing in a compliance-grade UI.
      return `⟦missing:${key}⟧`;
    }
    return values ? formatICU(message, locale, values) : message;
  };
}
