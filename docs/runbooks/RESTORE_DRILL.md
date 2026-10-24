# Operational Runbook: Disaster Recovery Restore Drill & Reconciliation

> **Standard Compliance**: SPEC §18.1 Scenario 13 / SPEC §15.5 Runbook 6.
> **Objective**: Validate full database and artifact restoration with 100% hash, count, and key reconciliation.

---

## 1. Overview & Invariants

A restore procedure is not complete merely because `pg_restore` finished with exit code 0. To prevent silent data loss, bit rot, or unauthorized modifications during backups, every restoration must pass the **Three-Way Reconciliation Drill**:

1. **Count Reconciliation**: All domain tables (`institutions`, `instruments`, `documents`, `audit_log`, `policies`) must match or exceed the snapshot manifest counts.
2. **Hash Reconciliation**: Every stored instrument document and verification receipt must have a cryptographic SHA-256 digest matching the database ledger.
3. **Key & Chain Reconciliation**: The complete audit log hash-chain must replay from `GENESIS_HASH` with 0 broken links, and all periodic audit checkpoints must verify against AICTE's public Ed25519 signing key.

---

## 2. Automated Drill Procedure

### Step 1: Execute Backup
```bash
# Takes a timestamped snapshot of PostgreSQL schema + data and sha256 checksums
./scripts/backup.sh
```

### Step 2: Perform Restore into Target / Drill Database
```bash
# Restores PostgreSQL database and validates checksum manifest
./scripts/restore.sh ./backups/<backup_timestamp>
```

### Step 3: Run Automated Cryptographic Reconciliation
```bash
# Reconciles entity counts, document SHA-256 digests, and Ed25519 checkpoint signatures
python scripts/restore_drill.py
```

### Expected Output:
```text
=================================================================
AICTE FDR Portal — Disaster Recovery Restore & Hash Reconciliation
=================================================================
[*] Reconciling entity counts:
    - Institutions: 24
    - Instruments:  118
    - Documents:    118
    - Audit Log:    452
[*] Verifying cryptographic document hash integrity on 118 records...
    [PASS] All document SHA-256 hashes conform to cryptographic standards.
[*] Replaying audit hash-chain from GENESIS_HASH...
    [PASS] Audit log hash-chain intact: 0 tamper points detected.
[*] Verifying 12 signed Ed25519 audit checkpoints...
    [PASS] All 12 audit checkpoint signatures cryptographically verified.
=================================================================
[SUCCESS] Restore drill completed: Hashes, counts, and keys 100% RECONCILED.
=================================================================
```

---

## 3. Discrepancy Triage & Escalation

If `restore_drill.py` exits with non-zero status:
- **Count Mismatch**: Check if `pg_dump` was interrupted or if table exclusions occurred.
- **Hash Discrepancy**: Indicates potential storage bit rot or tampering in transit. Immediately quarantine affected storage keys.
- **Audit Chain Broken**: Indicates an unauthorized `UPDATE` or `DELETE` bypassing database triggers. Treat as a potential security incident and escalate per `docs/runbooks/08_DATA_EXPOSURE_CERT_IN_ESCALATION.md`.
