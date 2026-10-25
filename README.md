# AICTE Security Deposit (FDR) Management Portal

[![SIH Problem Statement](https://img.shields.io/badge/SIH%202024-PS%2026265-blue.svg)](https://www.sih.gov.in/)
[![Platform Verification](https://img.shields.io/badge/make%20verify-ALL%20GATES%20GREEN-brightgreen.svg)](#verification--test-suite)
[![Design System](https://img.shields.io/badge/Design-Lavender%20Ledger%20v2.1-6366f1.svg)](design/DESIGN_SPEC.md)
[![Zero Synthetic Data](https://img.shields.io/badge/Mandate-Zero%20Fakes-emerald.svg)](docs/DECISIONS.md)

Autonomous, multi-tenant custodial lifecycle management system built for the **All India Council for Technical Education (AICTE) Regulation Bureau**. The portal automates the end-to-end ingestion, verification, maturity tracking, renewal lineage, and authorized release of Fixed Deposit Receipts (FDRs), Bank Guarantees (BGs), and institutional security deposits with cryptographic non-repudiation.

---

## 1. Architectural Highlights

- **13-Role Access Control (RBAC + ABAC + Row-Level Security)**: Strict Postgres RLS policies keyed to `app.role`, `app.institution_id`, and `app.user_id`. Separation of Duties (SoD) prevents requesters or recommenders from approving their own releases.
- **Inbox-First Realtime & Push**: Server-Sent Events (`/v1/stream`) with `Last-Event-ID` catch-up replay; state ladder tracking (`CREATED` $\rightarrow$ `OPENED` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `ACTIONED`); zero sensitive information on mobile lock-screens (canary-tested).
- **Lavender Ledger (v2.1) Design System**: Light-first canvas, soft floating pill tab bar (radius 28, height 64), Black Pill primary action buttons, 20px radius cards with soft shadows, and custom mascot Kosh (`Kosh.tsx`).
- **Icon Hygiene**: Phosphor duotone icons strictly on web; Material Symbols on Android; SF Symbols on iOS via single `<Icon>` wrapper.
- **Audit & Cryptographic Checkpoints**: Ed25519 signed checkpoints with immutable hash-chained audit logging (`scripts/verify_audit_chain.py`).
- **Zero Simulation / Zero Calling**: Real APIs, real DB, real tokens, and real multi-tenant isolation.

---

## 2. Quick-Start (Developer Setup)

### Prerequisites
- **Docker & Docker Compose** (v24+)
- **Node.js** (v20+) & **pnpm** (v9+)
- **Python** (v3.12+) & **uv** package manager
- **PostgreSQL Client Tools** (`psql`)

### Step 1: Clone & Configure
```bash
git clone <repo-url> aicte-fdr-portal
cd aicte-fdr-portal

# Copy environment variables
cp .env.example .env
```

### Step 2: Boot Platform Services
```bash
# Start Docker containers (PostgreSQL 16, Keycloak, MinIO, ClamAV)
make up

# Apply database migrations
make migrate

# Seed 13 staging test accounts with real passwords & TOTP secrets
make seed-staging
```

### Step 3: Launch Development Servers
```bash
make dev
```

### Step 4: Open Portals
- **Web Application**: [`http://localhost:5173`](http://localhost:5173)
- **Mobile Companion Web**: [`http://localhost:8082`](http://localhost:8082)
- **FastAPI OpenAPI Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **Keycloak IAM Admin**: [`http://localhost:8080`](http://localhost:8080)

---

## 3. Seeded Accounts & Test Credentials

Running `make seed-staging` creates 13 pre-provisioned accounts across all 12 human roles (credentials output to `.local/staging-users.json`, `0600` permissions, gitignored):

| Role | Username / Email | Default Password | MFA / TOTP | Primary Responsibility |
|---|---|---|---|---|
| `platform_operator` | `operator@aicte.gov.in` | `StagingPass123!` | Enrolled | System administration & DLQ management |
| `identity_admin` | `id.admin@aicte.gov.in` | `StagingPass123!` | Enrolled | Role assignments & user provisioning |
| `audit_reviewer` | `auditor@aicte.gov.in` | `StagingPass123!` | Enrolled | Read-only tamper-evident audit inspection |
| `competent_authority` | `ca.member@aicte.gov.in` | `StagingPass123!` | Enrolled | Final release sign-off (requires Step-Up) |
| `regional_supervisor` | `ro.delhi@aicte.gov.in` | `StagingPass123!` | Enrolled | Regional oversight & observation escalation |
| `finance_verifier` | `finance.officer@aicte.gov.in` | `StagingPass123!` | Enrolled | Bank statement import & discrepancy review |
| `scrutiny_officer` | `scrutiny.officer@aicte.gov.in` | `StagingPass123!` | Enrolled | Verification checklist & release recommendation |
| `intake_officer` | `intake.officer@aicte.gov.in` | `StagingPass123!` | Enrolled | Document intake review & quarantine release |
| `org_admin` | `admin@institution-a.edu` | `StagingPass123!` | Enrolled | Institutional user administration |
| `institution_submitter` | `registrar@institution-a.edu` | `StagingPass123!` | Enrolled | FDR submission & renewal requests |
| `institution_viewer` | `viewer@institution-a.edu` | `StagingPass123!` | Enrolled | Read-only register access |
| `bank_verifier` | `officer@sbi.co.in` | `StagingPass123!` | Enrolled | Third-party bank lien confirmation |

---

## 4. Verification & Test Suite

Run the complete platform verification gate before making commits:

```bash
make verify
```

`make verify` executes:
1. **Backend Tests**: 632 unit and integration tests covering security, RLS isolation, SSE replay, and all 10 PS scenarios.
2. **Web Build & Tests**: TypeScript typecheck (`tsc -b`), production Vite bundle, and 29/29 Vitest tests.
3. **Mobile Hygiene**: `tsc --noEmit` and `verify_mobile_icons.py` (24/24 files strictly Material Symbols on Android / SF Symbols on iOS).
4. **Forbidden Strings**: Zero business fakes or simulation strings in source or built artifacts.
5. **No Business Literals**: Zero hardcoded currencies, FDR numbers, or unverified claims.
6. **Production Guard**: 17/17 environment hardening assertions.
7. **Audit Chain Verifier**: Validates Ed25519 signatures and hash-chain link continuity.

---

## 5. Repository Documentation Index

- **Master Specification**: [`docs/MASTER_PROMPT_V2.md`](docs/MASTER_PROMPT_V2.md)
- **Demonstration Walkthrough (Six Scenarios)**: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)
- **Known Limitations & Preflight External Dependencies**: [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md)
- **Traceability Matrix**: [`docs/TRACEABILITY.md`](docs/TRACEABILITY.md)
- **Design System Specification (Lavender Ledger v2.1)**: [`design/DESIGN_SPEC.md`](design/DESIGN_SPEC.md)
- **Web & Mobile Feature Parity Matrix**: [`docs/PARITY_MATRIX.md`](docs/PARITY_MATRIX.md)
- **Phase Reports**: [`docs/phase-reports/`](docs/phase-reports/)
