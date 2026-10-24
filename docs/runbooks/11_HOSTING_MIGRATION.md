# Runbook 11: Hosting Migration & Infrastructure Portability

> **Classification**: Deployment Architecture / Cloud Neutrality
> **Reference**: OPEN_DECISIONS D-09, MASTER_PROMPT §18 & SPEC §15

---

## 1. Context & Architectural Commitment (D-09)
Per **OPEN_DECISIONS.md D-09**:
> *"Free hosting is acceptable for development/staging/hackathon demo; production hosting is an AICTE IT/security/procurement decision — document this limitation and ship portable containers so migration is trivial."*

The AICTE Security Deposit Portal is architected for **zero cloud lock-in**:
- Standard OCI Docker containers running non-root on Alpine/Debian-slim.
- Standard PostgreSQL 16 (relies on standard SQL, RLS, and JSONB; no proprietary cloud DB extensions required).
- S3-compatible object storage standard (MinIO, Garage, Ceph, AWS S3, or MeitY cloud object storage).
- Keycloak 26 OIDC identity adapter easily reconfigured to NIC Parichay, MeriPehchan, or on-prem enterprise IAM.

---

## 2. Pre-Migration Checklist
- [ ] Ensure `make verify` passes 100% on current deployment.
- [ ] Capture full backup using `./scripts/backup.sh`.
- [ ] Verify backup integrity using `python scripts/restore_drill.py`.
- [ ] Export DNS zone configuration and ensure TTL on portal domain is reduced to 300 seconds 48h prior to migration.

---

## 3. Migration Execution Procedure

### Step 1: Destination Infrastructure Provisioning
1. Clone repository on destination server / cloud VM (NIC MeghRaj / AWS / Self-Hosted):
   ```bash
   git clone https://github.com/aicte/fdr-portal.git /opt/aicte/fdr-portal
   cd /opt/aicte/fdr-portal
   ```
2. Configure `.env.production` with destination database URLs and object storage credentials. Ensure `APP_ENV=production`.

### Step 2: Data Transfer & Synchronization
1. Transfer PostgreSQL dump:
   ```bash
   scp ./backups/<LATEST>/fdr_db.sql.gz user@dest-server:/opt/aicte/backups/
   ```
2. Synchronize S3 object vault:
   ```bash
   rclone sync source-s3:fdr-vault dest-s3:fdr-vault --fast-list
   ```
3. Restore database on destination:
   ```bash
   ./scripts/restore.sh /opt/aicte/backups/
   ```

### Step 3: Run Full Verification Gate on Destination
```bash
# Verify audit chain, row counts, and document hashes
python scripts/restore_drill.py
python scripts/verify_audit_chain.py
```

### Step 4: Cutover DNS & Validate Production Guard
1. Update DNS `A` / `CNAME` records to point to destination IP.
2. Verify production guard passes and refuses mock adapters:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   docker compose logs api | grep "enforce_production_guard"
   ```
3. Monitor system telemetry and verify `/health` and `/readyz` endpoints.
