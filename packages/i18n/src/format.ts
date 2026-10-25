import IntlMessageFormat from 'intl-messageformat';
import type { Locale } from './types';

/**
 * Formats one ICU message-format string with `values`. Thin wrapper around
 * `intl-messageformat` so call sites never import it directly (keeps the
 * engine swappable). Supports ICU plural/select/number/date — not just
 * `{name}` substitution — per MASTER_PROMPT §27.
 */
export function formatICU(message: string, locale: Locale, values?: Record<string, string | number | Date>): string {
  const msg = new IntlMessageFormat(message, locale);
  return String(msg.format(values as Record<string, string | number | Date>));
}

/**
 * Indian digit grouping and currency formatting (R3.5 / RBI standard).
 * Formats with standard Indian numbering system: 3 digits for thousands, then 2 for lakhs and crores.
 */
export function formatIndianNumber(value: number): string {
  return new Intl.NumberFormat('en-IN').format(value);
}

export function formatINR(rupees: number, options?: { showPaisa?: boolean }): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: options?.showPaisa ? 2 : 0,
    maximumFractionDigits: options?.showPaisa ? 2 : 0,
  }).format(rupees);
}

export function formatPaiseINR(paise: number, options?: { showPaisa?: boolean }): string {
  return formatINR(paise / 100, options);
}

export function formatCroresINR(paise: number): string {
  const crores = paise / 1000000000;
  return `₹${crores.toFixed(2)} Cr`;
}

export function formatLakhsINR(paise: number): string {
  const lakhs = paise / 10000000;
  return `₹${lakhs.toFixed(2)} Lakh`;
}
