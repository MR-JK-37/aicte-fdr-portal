# Runbook 09: Policy Rule Misconfiguration & Version Rollback

> **Classification**: Severity 2 (S2) / Regulatory Rule Integrity
> **Reference**: SPEC §15.5 Runbook 9, OPEN_DECISIONS D-01 & F-10

---

## 1. Symptoms & Triggers
- Policy misconfiguration: incorrect deposit slab amounts (APH Table 1.4) or invalid tenure rules published.
- Unapproved penalty rule imported or enabled without formal AICTE Council sign-off.
- Spurious compliance shortfall alerts generated across hundreds of institutions due to flawed clause calculation.

---

## 2. Invariants & Guardrails
- **Draft by Default (D-01)**: All newly imported policy rules enter the system in `DRAFT` status and cannot drive automated compliance decisions until formally signed off.
- **Blocked Penalties**: All penalty entries are created in `BLOCKED` status awaiting explicit regulatory council resolution.
- **Immutable Historical Versions**: Once published, a policy version is NEVER edited in place; rollback is achieved by publishing a new superseding version or reverting the active pointer.

---

## 3. Step-by-Step Remediation

### Step 1: Identify Flawed Active Policy Version
```sql
SELECT id, handbook_edition, effective_from, effective_to, is_active, created_at 
FROM policy_versions 
WHERE is_active = true;
```

### Step 2: Emergency Policy Rule Suspension
If an active rule is generating incorrect shortfalls:
```sql
UPDATE policy_versions 
SET is_active = false, updated_at = NOW() 
WHERE id = '<FLAWED_POLICY_UUID>';
```
When `is_active = false`, the UI and compliance evaluation engines honestly report:
*"Policy rule not approved / suspended pending review"*, preventing incorrect penalty or shortfall calculations.

### Step 3: Rollback to Known-Good Prior Policy Edition
```sql
UPDATE policy_versions 
SET is_active = true, updated_at = NOW() 
WHERE handbook_edition = 'APH-2024-27' AND status = 'APPROVED';
```

### Step 4: Record Audit Event with Justification
```bash
python -c "
from app.db import SessionLocal
from app.audit import append_audit_entry
with SessionLocal() as session:
    append_audit_entry(
        session,
        action='policy.emergency_rollback',
        entity_type='policy_version',
        entity_id='<FLAWED_POLICY_UUID>',
        after={'active_version': 'APH-2024-27', 'reason': 'Council amendment clarification'}
    )
    session.commit()
"
```
Re-run compliance evaluation jobs on affected institutions to clear erroneous shortfalls.
