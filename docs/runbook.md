# AICTE Security Deposit Portal — Operations & Incident Runbook

## 1. Quick Reference & Service Inventory

| Service | Container / Process | Port | Health Check |
| :--- | :--- | :--- | :--- |
| **API** | `fdr-portal-api-1` | 8000 | `curl -f http://localhost:8000/health` |
| **PostgreSQL** | `fdr-portal-db-1` | 5434 (Host) / 5432 | `docker exec fdr-portal-db-1 pg_isready -U fdr` |
| **Valkey** | `fdr-portal-valkey-1` | 6379 | `docker exec fdr-portal-valkey-1 valkey-cli ping` |
| **ClamAV** | `fdr-portal-clamav-1` | 3310 | `nc -z localhost 3310` |
| **Garage S3** | `fdr-portal-garage-1` | 3900 | `/garage status` |
| **Celery Beat**| Process inside API | — | `celery -A app.core.celery_app inspect ping` |
| **Web SPA** | Caddy / Vite static | 80 / 3000 | `curl -f http://localhost:80/` |

---

## 2. Common Incident Response Procedures

### Incident 1: User Voice Channel Locked (3 Failed PIN Attempts)
- **Symptom**: Institution reports unable to authenticate on automated phone reminders ("Channel locked for 24 hours").
- **Diagnosis**: Query `app_users` table for `call_pin_locked_until > NOW()` and inspect `audit_log` for `action = 'voice_channel_locked'`.
- **Resolution**:
  1. Verify identity of Institution Director via institutional email / video verification.
  2. Clear lock and reset PIN via Scrutiny Officer terminal:
     ```bash
     docker exec -it fdr-portal-api-1 uv run python -c "
     from app.core.database import SessionLocal
     from app.models.models import AppUser
     from datetime import datetime, timezone
     with SessionLocal() as db:
         u = db.query(AppUser).filter_by(email='director@apex.edu').first()
         u.call_pin_locked_until = None
         db.commit()
         print('Lock cleared for', u.email)
     "
     ```

---

### Incident 2: Audit Chain Tamper Detected (Hash Mismatch)
- **Symptom**: Portal alert badge shows `TAMPER DETECTED: Hash broken at Block #X`.
- **Diagnosis**: Run the cryptographic audit verification utility:
  ```bash
  docker exec -it fdr-portal-api-1 uv run python -c "
  from app.core.database import SessionLocal
  from app.audit.chain import verify_audit_chain
  with SessionLocal() as db:
      valid, broken_id = verify_audit_chain(db)
      print(f'Audit Chain Valid: {valid}, Broken Block: {broken_id}')
  "
  ```
- **Resolution**:
  1. If `valid == False`, inspect `audit_log` row with `id = broken_id` and query PostgreSQL WAL logs or pgAudit to determine who executed an unauthorized direct `UPDATE` or `DELETE`.
  2. Restore compromised partition from verified backup (`/opt/fdr-portal/scripts/restore.sh <backup_dir>`).

---

### Incident 3: SimClock Testing Acceleration
- To fast-forward system time to test reminder ladders or maturity events without waiting months:
  ```bash
  # Advance clock by +30 days (triggers T-60 reminders)
  curl -X POST http://localhost:8000/api/v1/sim-clock/advance -H "Content-Type: application/json" -d '{"days": 30}'

  # Reset to real time
  curl -X POST http://localhost:8000/api/v1/sim-clock/reset
  ```
