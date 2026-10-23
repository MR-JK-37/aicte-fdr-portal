# Progress Log

## 2026-10-23

- Repo initialized (`git init`), local identity set.
- Read `Blueprint.txt` (project spec, 93KB) — using it as source of truth
  alongside the original 10-phase brief. Wrote `docs/plan.md`.
- Toolchain check: Node v22.23.1, pnpm 11.26.0, Python 3.14.7 (system — will
  pin 3.12 via `uv` for backend per spec), uv 0.11.32, Docker 29.8.0, Docker
  Compose 5.5.1. All present, no installs needed.
- Starting Phase 1 (Foundation): monorepo scaffold + Docker Compose.
- **Phase 1 complete and verified.** Full stack (`db`, `valkey`, `garage`,
  `keycloak`, `api`, `worker`, `beat`, `caddy`) comes up clean via
  `docker compose -f infra/docker/docker-compose.yml up -d`. Confirmed live:
  `GET /health` on the API (200, `{"status":"ok"}`), the same route proxied
  through Caddy at `:8081/health` and `:8081/api/health` (200), Garage admin
  health (`fully operational`), Keycloak booted and serving its login
  redirect (302) on `:8080`. Committed as `bd98148`.
- Host port collisions found with *other unrelated projects already running
  on this machine* (fraudshield-postgres on 5433, etc.) — remapped Postgres
  to host port 5434 only; no other host's containers were touched or
  stopped.

### Verified findings (changes from blueprint's assumptions)

- **MinIO open-source project was archived 2026-04-25** (GitHub repo is now
  read-only, "no longer maintained"). No new pre-built binaries/images ship
  for the community edition; source is still AGPLv3 but "at your own risk."
  Last published image: `minio/minio:RELEASE.2025-10-15T17-29-55Z` — pinned
  in `infra/docker/docker-compose.yml` for this build (fine for a frozen,
  zero-cost demo). **Flag for Phase 10 docs:** recommend evaluating Garage
  (actively maintained, S3-compatible, AGPLv3) as the production object
  store instead of MinIO.
- Keycloak current stable image confirmed via official docs:
  `quay.io/keycloak/keycloak:26.8.1`.

### Unverified / to confirm later

- Exact current free-tier limits for Groq/OpenRouter/Workers AI/Sarvam will
  be checked live against provider docs in Phase 6 (`check_providers.py`),
  not assumed from the blueprint's point-in-time numbers.
- Oracle Always Free Arm allowance (2 OCPU/12GB per blueprint) — confirm at
  Phase 10 deploy time against Oracle's current console.
