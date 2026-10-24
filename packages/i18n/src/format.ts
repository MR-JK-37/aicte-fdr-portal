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
