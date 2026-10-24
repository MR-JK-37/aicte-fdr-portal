/**
 * Mirrors the `translation_catalog_status` DB table (MASTER_PROMPT §27 /
 * F-27): every message key carries a per-locale review status. Production
 * must only ever show `reviewed` strings in the active locale and fall back
 * to English otherwise — never show an un-reviewed machine draft to an end
 * user outside a clearly labelled "draft translation" context.
 */
export type CatalogStatus = 'machine-draft' | 'reviewed';

export interface CatalogEntry {
  status: CatalogStatus;
  message: string;
}

export type Catalog = Record<string, CatalogEntry>;

export const SUPPORTED_LOCALES = ['en', 'hi', 'ta'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const AUTHORITATIVE_LOCALE: Locale = 'en';
