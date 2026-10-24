# @aicte-fdr/api-client

Generated OpenAPI client (typed `fetch` wrapper via `openapi-fetch`) for
`apps/web` and `apps/mobile`.

## Status: toolchain-only, by design

This phase has no real backend endpoints beyond auth/RLS/Keycloak scaffolding
(built by sibling agents in the same Phase 1 workstream). `openapi.json` here
is a **placeholder spec** (one `GET /v1/health`) that exists only to prove
the generation pipeline works end to end:

```
openapi.json  --(openapi-typescript)-->  src/generated/schema.d.ts  --(openapi-fetch)-->  typed client
```

`src/generated/schema.d.ts` is committed (checked in) so `pnpm install` +
typecheck works without a generation step, but it is 100% regenerated, never
hand-edited — run `pnpm --filter @aicte-fdr/api-client generate` after any
`openapi.json` change.

## Once Phase 2 ships real endpoints

1. The backend publishes its real OpenAPI document — point `generate` at
   wherever it ends up (`make openapi` emits it per CLAUDE.md; wire that
   output path in here, replacing `./openapi.json`, likely via a `fetch`
   step from the running backend or a committed artifact from the backend
   build — decide based on how the backend agent wires `make openapi`).
2. Regenerate (`pnpm --filter @aicte-fdr/api-client generate`) and commit the
   diff. CI should fail if the generated client is stale relative to the
   live spec (CLAUDE.md "Definition of done": "generated client
   regenerated").
3. Delete this README's "Status" section.

## Verify

```
pnpm --filter @aicte-fdr/api-client generate
pnpm --filter @aicte-fdr/api-client typecheck
pnpm --filter @aicte-fdr/api-client test
```
