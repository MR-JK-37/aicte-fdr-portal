# @aicte-fdr/schemas

Zod runtime-validation schemas shared by `apps/web` and `apps/mobile`.

## Status: placeholder, by design

No backend endpoints beyond auth/RLS/Keycloak scaffolding exist yet this
phase (three sibling agents are building those). The real domain schemas —
`Instrument`, `Institution`, `ReleaseRequest`, evidence records, etc. — must
be **generated from the backend's real OpenAPI spec**, never hand-written,
so client validation can never silently drift from what the server actually
accepts/returns (CLAUDE.md "generated client regenerated" is part of the
definition of done for every task).

`src/common.ts` holds a handful of hand-written placeholder schemas
(`errorEnvelopeSchema`, `evidenceAttributeSchema`, `statusToneSchema`,
`moneyPaiseSchema`) that exist only to:
1. prove the zod toolchain is correctly wired into the workspace, and
2. give the design-system showcase (`apps/web` `/_design-system`) something
   real to validate evidence-chip / status-badge props against.

**Do not add domain schemas here by hand.** Once `packages/api-client`'s
`openapi.json` is replaced by the backend's real spec (see that package's
README), regenerate zod schemas from it (e.g. via `openapi-zod-client` or an
equivalent OpenAPI→zod generator) and delete the placeholder note above.

## Verify

```
pnpm --filter @aicte-fdr/schemas typecheck
pnpm --filter @aicte-fdr/schemas test
```
