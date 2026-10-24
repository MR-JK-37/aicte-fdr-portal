# Runbook 10: Cryptographic Key & Secret Rotation

> **Classification**: Routine Maintenance / Security Hardening
> **Reference**: MASTER_PROMPT §18 & SPEC §15.5 Runbook 10

---

## 1. Scope of Keys & Rotation Schedules
1. **Ed25519 Audit Checkpoint Signing Key**: Annually (or immediately upon suspected compromise).
2. **JWT Secret / Session Signing Keys (HMAC-SHA256 / RS256)**: Every 90 days.
3. **Database Credentials (`fdr_app` & `fdr_readonly`)**: Every 180 days.
4. **MinIO / Garage S3 Access & Secret Keys**: Every 180 days.
5. **AI Gateway Provider API Keys (Groq, Gemini, OpenRouter)**: Every 90 days.

---

## 2. Invariants & Zero-Downtime Guarantee
- **Public Verification Continuity**: Checkpoints signed with older keys must remain verifiable using historical public key records (`signer_key_id` in `audit_checkpoints`).
- **Graceful Rollover**: JWT rotation supports verifying tokens signed with `KEY_N-1` during a 24-hour transition window while signing all new tokens with `KEY_N`.

---

## 3. Step-by-Step Rotation Procedures

### A. Ed25519 Audit Checkpoint Signing Key Rotation
1. Generate new Ed25519 keypair:
   ```bash
   python -c "
   from cryptography.hazmat.primitives.asymmetric import ed25519
   from cryptography.hazmat.primitives import serialization
   key = ed25519.Ed25519PrivateKey.generate()
   priv_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
   pub_pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
   open('/etc/aicte/fdr/audit_key_new.pem', 'wb').write(priv_pem)
   open('/etc/aicte/fdr/audit_pub_new.pem', 'wb').write(pub_pem)
   print('Generated new Ed25519 keypair')
   "
   ```
2. Update key identifier in configuration (`AUDIT_SIGNING_KEY_ID="prod-audit-key-2026-v2"`).
3. Append historical public key to `KNOWN_AUDIT_PUBLIC_KEYS` registry in `services/api/app/audit.py`.
4. Trigger immediate signed checkpoint with new key:
   ```bash
   docker exec -it fdr-portal-worker-1 python -m app.audit_checkpoint --force-checkpoint
   ```
5. Verify complete audit chain across both key generations:
   ```bash
   python scripts/verify_audit_chain.py
   ```

### B. MinIO / S3 Access Key Rotation
1. In MinIO Console or via `mc admin user`:
   ```bash
   mc admin user add aicte-minio fdr-app-v2 <NEW_SECRET>
   mc admin policy attach aicte-minio fdr-vault-policy --user fdr-app-v2
   ```
2. Update `S3_ACCESS_KEY` and `S3_SECRET_KEY` in `docker-compose.yml` or secret manager.
3. Restart API & worker: `docker compose restart api worker`.
4. Revoke old user `fdr-app-v1` after validating upload & download pathways.
