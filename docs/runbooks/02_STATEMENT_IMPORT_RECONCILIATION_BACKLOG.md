# Runbook 02: Bank Statement Import Invalidity, Duplicate Batch & Reconciliation Backlog

> **Classification**: Severity 2 (S2) / Financial Ledger Integrity
> **Reference**: SPEC §15.5 Runbook 2 & F-07

---

## 1. Symptoms & Triggers
- MT940 or CAMT.053 statement parser fails on uploaded statement files.
- Duplicate batch import alert: identical statement file hash uploaded twice.
- Reconciliation worker backlog: `statement_transactions` table has unprocessed entries exceeding 500 items or oldest un-reconciled event > 24 hours.
- Ambiguous multi-match: single deposit credit matches multiple draft FDR instruments with identical amounts.

---

## 2. Invariants & Guardrails
- **Zero Auto-Confirmation**: Ambiguous or partial matches are NEVER automatically marked as `L3_LEDGER_RECONCILED` or `BANK_CONFIRMED`.
- **Idempotent Imports**: Duplicate statement uploads MUST be detected via SHA-256 batch hash and rejected with HTTP 409 Conflict.
- **Exception Queue First**: Any parsing failure, account number discrepancy, or value mismatch routes directly to the Finance Officer's Reconciliation Exception Queue (`/reconciliation/exceptions`).

---

## 3. Step-by-Step Remediation

### Scenario A: Statement File Syntax / Parser Error
1. Inspect parse failure details:
   ```sql
   SELECT id, filename, failure_reason, status, created_at 
   FROM statement_batches 
   WHERE status = 'FAILED' 
   ORDER BY created_at DESC LIMIT 5;
   ```
2. Verify bank statement format against official specifications:
   - MT940: SWIFT Field :61: statement line & :86: information to account owner.
   - CAMT.053: ISO 20022 XML `<BkToCstmrStmt>`.
3. If the bank used a non-standard delimiter or header, request a corrected statement from the bank nodal officer. Do not manually edit raw statement files on the server.

### Scenario B: Duplicate Batch Resubmission
1. Query statement batch hash:
   ```sql
   SELECT id, file_hash, uploaded_by, created_at 
   FROM statement_batches 
   WHERE file_hash = '<SHA256_HEX>';
   ```
2. If already processed, notify the finance officer that transactions from this batch are already recorded. The API returns `409 Conflict` with the ID of the original batch.

### Scenario C: Reconciliation Queue Backlog
1. Check outbox worker status and database lock contention:
   ```sql
   SELECT count(*), min(created_at) 
   FROM outbox 
   WHERE event_type = 'statement.transaction_reconcile' AND processed_at IS NULL;
   ```
2. Scale outbox worker consumer if necessary:
   ```bash
   docker compose up -d --scale worker=3
   ```
3. Finance Verifiers manually resolve unresolved items from the Exception Queue by attaching corroborating bank advice or opening an observation.
