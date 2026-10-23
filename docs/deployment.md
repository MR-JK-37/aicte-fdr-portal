# AICTE Security Deposit / FDR Management Portal — Production Deployment Guide

## 1. System Requirements & Architecture Overview

The portal is designed around a **Zero-Cost Production Specification** (`Blueprint.txt`), deployable on an **Oracle Cloud Always Free Ampere A1 VM** (4 OCPU, 24GB RAM, 200GB NVMe storage) or any standard Linux server (Ubuntu 22.04/24.04 LTS).

```
               +-------------------------------------------------------+
               |                  Cloudflare Tunnel / Edge              |
               +---------------------------+---------------------------+
                                           | HTTPS / 443
                                           v
               +-------------------------------------------------------+
               |                  Caddy Reverse Proxy                  |
               |       (Automatic TLS, Rate Limiting, Route Guard)      |
               +-------------+---------------------+-------------------+
                             |                     |
                /api/*       v        /auth/*      v           /*
              +--------------------+  +--------------------+  +--------+
              | FastAPI App (8000) |  |  Keycloak (8080)   |  | Web UI |
              +---------+----------+  +--------------------+  +--------+
                        |
      +-----------------+-----------------+-----------------+
      |                 |                 |                 |
      v                 v                 v                 v
+------------+   +-------------+   +-------------+   +-------------+
| PostgreSQL |   | Valkey 8    |   | ClamAV      |   | Garage S3   |
| + pgvector |   | (Cache/MQ)  |   | (Antivirus) |   | (Encrypted) |
+------------+   +-------------+   +-------------+   +-------------+
```

---

## 2. Prerequisites

- **Host OS**: Linux (Ubuntu 22.04 LTS or Debian 12 recommended)
- **Container Engine**: Docker 24.0+ & Docker Compose v2+
- **Runtimes**:
  - Python 3.12+ (managed via `uv`)
  - Node.js 20+ & pnpm 11+
- **Open Ports**:
  - 80/443 (HTTP/HTTPS via Caddy)
  - 5434 (PostgreSQL internal mapped port)
  - 6379 (Valkey)

---

## 3. Step-by-Step Installation

### Step 3.1: Clone and Configure Environment
```bash
git clone https://github.com/aicte/fdr-portal.git /opt/fdr-portal
cd /opt/fdr-portal

# Copy environment template
cp .env.example .env
chmod 600 .env
```

Ensure the following critical variables are set in `.env`:
```ini
APP_ENV=production
SECRET_KEY=<generate-via-openssl-rand-hex-32>
DATABASE_URL=postgresql://fdr_app:your_secure_password@db:5432/fdr
TEST_DATABASE_URL=postgresql://fdr_app:your_secure_password@localhost:5434/fdr
READONLY_DATABASE_URL=postgresql://fdr_readonly:your_secure_ro_password@localhost:5434/fdr
VALKEY_URL=redis://valkey:6379/0
GARAGE_ACCESS_KEY=<generated-key>
GARAGE_SECRET_KEY=<generated-secret>
PRODUCTION_TELEPHONY_ENABLED=false
```

### Step 3.2: Launch Infrastructure via Docker Compose
```bash
cd infra/docker
docker compose up -d
```

Verify all core containers report healthy status:
```bash
docker compose ps
```

### Step 3.3: Execute Database Migrations
```bash
# Run Alembic migrations to head
docker compose exec api uv run alembic upgrade head

# Verify Row-Level Security (RLS) policies and triggers
docker compose exec api uv run python -c "from app.core.database import engine; print('DB Connected:', engine.url)"
```

### Step 3.4: Build and Serve Frontend SPA
```bash
# Install workspace dependencies
pnpm install

# Approve build scripts for pnpm 11
pnpm approve-builds --all

# Build shared types & Web assets
pnpm --filter @aicte-fdr/shared build
pnpm --filter web build
```

Built static assets in `apps/web/dist/` are automatically served via Caddy.

---

## 4. Health Checks and Verification

Verify the system endpoints return `200 OK`:

| Service | Endpoint | Expected Response |
| :--- | :--- | :--- |
| **API Gateway** | `GET http://localhost:8000/health` | `{"status":"ok","db":"connected","valkey":"connected"}` |
| **Caddy Proxy** | `GET http://localhost:80/health` | `200 OK` |
| **Keycloak OIDC** | `GET http://localhost:8080/realms/aicte/.well-known/openid-configuration` | JSON Realm Metadata |
| **Audit Ledger** | `SELECT COUNT(*) FROM audit_log` | Non-zero verified block count |

---

## 5. Automated Backups & Disaster Recovery

Cron schedule for daily zero-downtime backups:
```bash
# Add to /etc/crontab:
0 2 * * * root /opt/fdr-portal/scripts/backup.sh /var/backups/aicte-fdr >> /var/log/aicte_backup.log 2>&1
```

To test restore drill:
```bash
/opt/fdr-portal/scripts/restore.sh /var/backups/aicte-fdr/<timestamp>
```
