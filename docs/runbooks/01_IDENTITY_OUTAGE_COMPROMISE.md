# Runbook 01: Identity Provider Outage & Privileged Account Compromise

> **Classification**: Severity 1 (S1) / Operational Continuity
> **Reference**: SPEC §15.5 Runbook 1 & MASTER_PROMPT §18

---

## 1. Symptoms & Triggers
- Spikes in `401 UnauthenticatedError` across API endpoints.
- Keycloak / Parichay OIDC JWKS discovery endpoint unreachable (`GET /realms/aicte/.well-known/openid-configuration` timeout).
- Reports of unauthorized actions by privileged accounts (e.g., Competent Authority or Regional Supervisor).
- Security alert: Multiple failed TOTP step-up attempts followed by successful login from an anomalous IP address.

---

## 2. Immediate Containment Procedure

### A. If Identity Provider (Keycloak / Parichay) is Unreachable:
1. **Verify Outage**:
   ```bash
   curl -I -m 5 https://auth.aicte-india.org/realms/aicte/.well-known/openid-configuration
   ```
2. **Graceful UI Degradation**:
   - The API will reject new unauthenticated requests with `401 UnauthenticatedError`.
   - Web and mobile apps automatically display: *"Identity services are temporarily unavailable. Active sessions remain valid until token expiration."*
3. **Emergency Casework Continuity**:
   - For statutory deadlines occurring during outage, invoke manual continuity procedures per SPEC §15.4.
   - All manual paper authorizations must be recorded post-recovery with explicit signed receipts and audit annotations.

### B. If Privileged Account Compromise is Suspected:
1. **Immediate Session Revocation**:
   - In Keycloak Admin Console or via Keycloak CLI:
     ```bash
     kcadm.sh revoke-user-sessions -r aicte <USER_UUID>
     ```
   - In the FDR API database:
     ```sql
     UPDATE app_users 
     SET is_active = false, updated_at = NOW() 
     WHERE id = '<USER_UUID>';
     ```
2. **Revoke Active Push & Device Registrations**:
   ```sql
   DELETE FROM device_installations WHERE user_id = '<USER_UUID>';
   ```
3. **Audit Inspection & Blast Radius Analysis**:
   ```sql
   SELECT id, timestamp, action, entity_type, entity_id, before, after 
   FROM audit_log 
   WHERE actor_id = '<USER_UUID>' 
   ORDER BY timestamp DESC;
   ```
4. **Trigger Security Step-Up Password Reset**:
   - Issue required password reset and re-enrolment of TOTP / WebAuthn passkey before reactivating account.

---

## 3. Post-Incident Review & Resolution
1. Verify audit log integrity using `python scripts/verify_audit_chain.py`.
2. File Incident Report within 6 hours detailing compromised actor, timestamps, affected FDR cases, and remediation actions.
