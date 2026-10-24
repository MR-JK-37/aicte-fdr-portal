/**
 * @aicte-fdr/design-tokens
 *
 * Thin re-export. The actual token *values* live in exactly one place —
 * /design/tokens.ts (verified against /design/tokens.css for parity and
 * WCAG contrast by `design/check_tokens.py`). This package exists only so
 * apps/web and apps/mobile can `import { dark, m3Dark, radius, ... } from
 * '@aicte-fdr/design-tokens'` as a normal workspace dependency instead of
 * reaching across the repo with relative paths. Never copy values here —
 * add them to /design/tokens.ts and they flow through automatically.
 */
export * from '../../../design/tokens';
