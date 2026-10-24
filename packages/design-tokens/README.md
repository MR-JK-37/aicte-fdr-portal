# @aicte-fdr/design-tokens

Wraps `/design/tokens.ts` and `/design/tokens.css` as a pnpm workspace
package so `apps/web` and `apps/mobile` can depend on it normally
(`workspace:*`) instead of using relative paths.

**This package holds no values of its own.** `src/index.ts` re-exports
`/design/tokens.ts` and `css/tokens.css` re-exports (`@import`s)
`/design/tokens.css`. The single source of truth is `/design/DESIGN_SPEC.md`
+ `/design/tokens.{css,ts}`; `design/check_tokens.py` verifies the two token
files stay in parity and every text/icon colour pair meets WCAG contrast.
If you need a new token, add it there, not here.

## Usage

Web (Vite/PostCSS):
```css
@import "@aicte-fdr/design-tokens/css/tokens.css";
```

Web or mobile (TS):
```ts
import { dark, light, m3Dark, m3Light, radius, space, typeApple, typeM3, glass, evidenceChip } from '@aicte-fdr/design-tokens';
```

React Native does not load CSS; mobile primitives consume the `dark`/`light`/
`m3Dark`/`m3Light`/`radius`/`space`/`typeApple`/`typeM3`/`glass` objects
directly as plain JS values (see `apps/mobile/src/design-system`).
