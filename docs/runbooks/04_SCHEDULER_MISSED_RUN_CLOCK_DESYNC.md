# Runbook 04: Maturity Scheduler Missed Run & Clock Desynchronisation

> **Classification**: Severity 1 (S1) / Statutory Compliance
> **Reference**: SPEC §15.5 Runbook 4 & F-11

---

## 1. Symptoms & Triggers
- Alert: `scheduler_last_success` timestamp older than 26 hours.
- Alert: `clock_drift_seconds` exceeds 1.0 second relative to NTP.
- Due maturity reminders (90d, 60d, 30d, 15d, 0d) not generated for approaching FDRs.
- DB lease deadlock: scheduler process crashed holding lease with future `lease_until`.

---

## 2. Invariants & Guardrails
- **Real NTP Clock Only**: In production (`APP_ENV=production`), simulated clocks are strictly rejected at startup by `enforce_production_guard()`.
- **DB-Leased Singleton**: Exactly one scheduler instance runs at any given time via Postgres transactional row lock (`SELECT ... FOR UPDATE SKIP LOCKED` on `scheduler_leases`).
- **Idempotent Reminders**: Re-running the scheduler multiple times over the same day NEVER produces duplicate reminder entries for the same instrument and horizon.

---

## 3. Step-by-Step Remediation

### Step 1: Check NTP Clock Synchronization
On host server and container nodes:
```bash
chronyc tracking || timedatectl status
```
If clock drift > 1.0s:
1. Resynchronize immediately against national NTP pool (`in.pool.ntp.org` / `time.nic.in`):
   ```bash
   sudo chronyc makestep
   ```

### Step 2: Release Deadlocked Scheduler Lease
If scheduler crashed ungracefully:
1. Inspect lease status:
   ```sql
   SELECT lease_name, held_by, lease_until, updated_at 
   FROM scheduler_leases 
   WHERE lease_name = 'maturity_scanner';
   ```
2. If `held_by` points to an exited container PID, clear expired lease:
   ```sql
   UPDATE scheduler_leases 
   SET lease_until = NOW() - INTERVAL '1 second', held_by = NULL 
   WHERE lease_name = 'maturity_scanner' AND lease_until < NOW();
   ```

### Step 3: Trigger Immediate Catch-Up Scan
Execute the maturity scanner job synchronously:
```bash
docker exec -it fdr-portal-worker-1 python -m app.reminders.scheduler --run-catch-up
```
Verify generated reminder events:
```sql
SELECT count(*), horizon_days, created_at 
FROM reminder_logs 
WHERE created_at > NOW() - INTERVAL '1 hour' 
GROUP BY horizon_days, created_at;
```
