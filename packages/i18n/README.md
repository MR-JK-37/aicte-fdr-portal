# @aicte-fdr/i18n

ICU-message-format catalogue + loader for `apps/web` and `apps/mobile`, per
`docs/MASTER_PROMPT.md` §27 (F-27 Internationalisation).

## Convention

- English (`catalogs/en.json`) is **authoritative** and must stay 100%
  `status: "reviewed"` (enforced by `src/loader.test.ts`).
- Hindi (`hi.json`) and Tamil (`ta.json`) ship at launch; every key starts as
  `status: "machine-draft"` until a human reviewer flips it to `"reviewed"`.
  This mirrors the `translation_catalog_status` DB table the backend owns
  for policy/notification templates — same two-state convention, applied
  here to UI strings.
- **Production never shows an un-reviewed string to an end user.** It falls
  back silently to English. `loadCatalog(locale, { reviewedOnly: true })`
  (the default) implements this. Pass `reviewedOnly: false` only from
  translator/review tooling that needs to see drafts.
- Legal/clause text from policy documents is never run through this
  package — it stays English-authoritative with a separately-labelled
  convenience translation, per CLAUDE.md.

## Adding a key

1. Add it to `catalogs/en.json` with `status: "reviewed"` — this is required
   for every key, no exceptions.
2. Add the same key to `hi.json` and `ta.json`. If you have a real
   translation, mark it `reviewed`; otherwise leave `machine-draft` (or copy
   the English text as a placeholder — either way it won't reach users in
   production until reviewed).
3. Keys use ICU message format — `{name}` substitution, and
   `{count, plural, one {# item} other {# items}}` for plurals. Formatting
   is done by `intl-messageformat` via `formatICU`/`createTranslator`, not a
   hand-rolled `{x}`-replace, so plural/select/number/date rules work
   correctly per-locale.

## Usage

```ts
import { createTranslator } from '@aicte-fdr/i18n';

const t = createTranslator('hi'); // reviewed-only by default
t('nav.dashboard');                 // -> 'Dashboard' (hi.json is all machine-draft at launch, so falls back to English)
t('greeting.hello', { name: 'Priya' });
t('count.items', { count: 3 });     // ICU plural
```

## Status today

Seeded with common app-shell strings only (app name, nav labels, generic
action/state/status/evidence labels) — enough for the primitives showcase
and loader tests to be real. Screen-specific copy is added as each screen is
built in later phases; there is nothing to translate yet beyond this shell.
