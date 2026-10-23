#!/usr/bin/env bash
# AICTE Security Deposit Portal — Disaster Recovery Restore Drill
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <path_to_backup_directory>"
  exit 1
fi

BACKUP_DIR="$1"
if [ ! -f "$BACKUP_DIR/fdr_db.sql.gz" ]; then
  echo "Error: Backup file $BACKUP_DIR/fdr_db.sql.gz not found!"
  exit 1
fi

echo "=== Starting AICTE FDR Disaster Recovery Restore Drill ==="
echo "Restoring from: $BACKUP_DIR"

# 1. Verify Checksums
echo "[1/3] Verifying SHA-256 checksums..."
(cd "$BACKUP_DIR" && sha256sum -c checksums.sha256)

# 2. Restore PostgreSQL
echo "[2/3] Restoring database to clean state..."
gunzip -c "$BACKUP_DIR/fdr_db.sql.gz" | docker exec -i fdr-portal-db-1 psql -U fdr -d fdr
docker exec fdr-portal-db-1 psql -U fdr -d fdr -c "GRANT USAGE ON SCHEMA public TO fdr_readonly; GRANT SELECT ON ALL TABLES IN SCHEMA public TO fdr_readonly; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO fdr_readonly;"


# 3. Post-Restore Verification
echo "[3/3] Running post-restore integrity check..."
docker exec fdr-portal-db-1 psql -U fdr -d fdr -c "SELECT COUNT(*) as restored_instruments FROM instruments;"
docker exec fdr-portal-db-1 psql -U fdr -d fdr -c "SELECT COUNT(*) as restored_audit_blocks FROM audit_log;"

echo "=== Disaster Recovery Drill Completed Cleanly ==="
