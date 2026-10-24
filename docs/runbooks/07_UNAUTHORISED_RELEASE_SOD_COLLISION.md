# Runbook 07: Unauthorised Release Attempt & Separation of Duties Collision

> **Classification**: Severity 1 (S1) / Fraud Prevention & Governance
> **Reference**: SPEC §15.5 Runbook 7, SPEC §18.1 Scenario 9 & F-12/F-13

---

## 1. Symptoms & Triggers
- Security alert: Same-person maker-checker violation attempted (recommending officer attempted to approve release, or requester attempted to approve own request).
- Security alert: Release decision attempted without satisfying all prerequisite checklist items and clearances.
- Security alert: Release approval attempted without valid step-up MFA.
- Delegation limit exceeded: Competent Authority attempted approval for amount exceeding authorized financial threshold.

---

## 2. Invariants & Guardrails
- **Dual Enforcement**: Separation of Duties (SoD) is strictly enforced at both application code layer (`app/authz.py`) and PostgreSQL database trigger layer (`release_requests` constraints).
- **Hard Gate on Clearances**: Status `APPROVED` is impossible if any checklist item or clearance is `NOT_SATISFIED` or `PENDING_SOURCE`.
- **Step-Up MFA Mandatory**: Competent Authority approval requires an active step-up assurance window (≤15 min).

---

## 3. Step-by-Step Remediation

### Step 1: Isolate the Incident & Target Case
1. Identify the release request and actors involved:
   ```sql
   SELECT id, instrument_id, requester_id, recommender_id, approver_id, status, amount 
   FROM release_requests 
   WHERE id = '<RELEASE_REQUEST_UUID>';
   ```
2. Inspect the audit log for collision attempts:
   ```sql
   SELECT timestamp, action, actor_id, before, after 
   FROM audit_log 
   WHERE entity_id = '<RELEASE_REQUEST_UUID>' 
   ORDER BY timestamp DESC;
   ```

### Step 2: Lock Case Against Premature Execution
If a rogue approval slipped past or an off-system collusion is suspected:
1. Immediately place the release request into `LEGAL_HOLD`:
   ```sql
   UPDATE release_requests 
   SET status = 'BLOCKED_INVESTIGATION', updated_at = NOW() 
   WHERE id = '<RELEASE_REQUEST_UUID>';
   ```
2. Log explicit administrative hold entry in the hash-chained audit log:
   ```bash
   python -c "
   from app.db import SessionLocal
   from app.audit import append_audit_entry
   with SessionLocal() as session:
       append_audit_entry(session, action='release.security_hold', entity_type='release_request', entity_id='<RELEASE_REQUEST_UUID>', after={'status': 'BLOCKED_INVESTIGATION'})
       session.commit()
   "
   ```

### Step 3: Re-verify Checklists and Clearances
1. Ensure all regional clearances, vigilance clearances, and compliance checklists have non-conflicting reviewer IDs:
   ```sql
   SELECT clearance_type, reviewer_id, status, updated_at 
   FROM clearances 
   WHERE release_request_id = '<RELEASE_REQUEST_UUID>';
   ```
2. Require formal re-scrutiny by an independent Regional Supervisor before lifting hold.
