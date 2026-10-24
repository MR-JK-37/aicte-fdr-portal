import en from '../catalogs/en.json';
import hi from '../catalogs/hi.json';
import ta from '../catalogs/ta.json';
import type { Catalog, Locale } from './types';
import { AUTHORITATIVE_LOCALE } from './types';

const RAW_CATALOGS: Record<Locale, Catalog> = {
  en: en as Catalog,
  hi: hi as Catalog,
  ta: ta as Catalog,
};

export interface LoadCatalogOptions {
  /**
   * When true (the default — use this in production), keys whose status is
   * not `reviewed` in the requested locale are dropped and resolved from the
   * English catalogue instead, per MASTER_PROMPT §27: "production shows only
   * `reviewed` strings in that locale and falls back to English otherwise".
   * Set to false only in translator/review tooling that needs to see drafts.
   */
  reviewedOnly?: boolean;
}

/**
 * Builds a flat `{ key: message }` map for `locale`, honouring the
 * reviewed-only production rule. English is always the fallback and is
 * never itself filtered (it is the authoritative locale).
 */
export function loadCatalog(locale: Locale, options: LoadCatalogOptions = {}): Record<string, string> {
  const reviewedOnly = options.reviewedOnly ?? true;
  const english = RAW_CATALOGS[AUTHORITATIVE_LOCALE];
  const target = RAW_CATALOGS[locale] ?? {};

  const out: Record<string, string> = {};
  for (const [key, entry] of Object.entries(english)) {
    out[key] = entry.message;
  }
  if (locale !== AUTHORITATIVE_LOCALE) {
    for (const [key, entry] of Object.entries(target)) {
      if (!reviewedOnly || entry.status === 'reviewed') {
        out[key] = entry.message;
      }
      // else: silently keep the English fallback already in `out`.
    }
  }
  return out;
}

/** Raw, unmerged catalogue (status + message) for a single locale — used by review/translator tooling. */
export function getRawCatalog(locale: Locale): Catalog {
  return RAW_CATALOGS[locale] ?? {};
}

export { RAW_CATALOGS };
