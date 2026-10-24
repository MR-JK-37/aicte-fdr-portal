# Runbook 06: Database Restore, Failover & Object Storage Recovery

> **Classification**: Severity 1 (S1) / Disaster Recovery
> **Reference**: SPEC §15.5 Runbook 6 & SPEC §18.1 Scenario 13

---

## 1. Symptoms & Triggers
- PostgreSQL primary node hardware failure or unrecoverable disk corruption.
- Object storage (MinIO / Garage S3) volume loss or replica desynchronisation.
- Accidental operational data wipe or failed database schema migration.

---

## 2. Invariants & Recovery Targets
- **RPO (Recovery Point Objective)**: 15 minutes (via automated WAL archiving / PITR).
- **RTO (Recovery Time Objective)**: 60 minutes.
- **Three-Way Reconciliation**: Restored state must pass `scripts/restore_drill.py` with 100% count, hash, and Ed25519 signature verification before returning to production traffic.

---

## 3. Step-by-Step Restoration Procedure

### Step 1: Provision Clean Database & Storage Volumes
```bash
# Clean container volumes if recreating from backup:
docker compose down -v
docker compose up -d db s3
```

### Step 2: Restore PostgreSQL Snapshot
```bash
# Locate most recent verified backup directory:
LATEST_BACKUP=$(ls -td ./backups/20* | head -1)
echo "Restoring from: $LATEST_BACKUP"

# Run restore script (verifies SHA-256 manifest and restores schema + data)
./scripts/restore.sh "$LATEST_BACKUP"
```

### Step 3: Restore MinIO / S3 Document Objects
```bash
# Restore S3 document mirror:
mc mirror "$LATEST_BACKUP/s3_vault" aicte-minio/fdr-vault/
```

### Step 4: Run Mandatory Post-Restore Verification Drill
```bash
python scripts/restore_drill.py
```
If `restore_drill.py` reports any count, hash, or signature mismatch, DO NOT open the system to traffic. Investigate missing records immediately.

### Step 5: Post-Restore Service Restart
```bash
# Apply any pending migrations if upgrading:
make migrate

# Restart API and worker containers:
docker compose restart api worker
```
Verify system readiness probe:
```bash
curl http://localhost:8000/readyz
```
