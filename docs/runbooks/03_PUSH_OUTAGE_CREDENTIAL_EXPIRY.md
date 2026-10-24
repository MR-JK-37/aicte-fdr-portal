# Runbook 03: Push Provider Outage, Credential Expiry & Token Spike

> **Classification**: Severity 2 (S2) / Notification Reliability
> **Reference**: SPEC §15.5 Runbook 3, MASTER_PROMPT §10 & F-14/F-15

---

## 1. Symptoms & Triggers
- Alert: Spike in `NotificationAttempt` with `status = 'PROVIDER_FAILED'` or `result_code = 'UNREGISTERED'`.
- FCM service account JSON expired or revoked in Google Cloud Console.
- Apple Push Notification service (APNs) `.p8` token expired or invalid team/key ID.
- Outbox worker logs showing repeated HTTP 401 / 403 / 503 from `fcm.googleapis.com` or `api.push.apple.com`.

---

## 2. Invariants & Guardrails
- **Inbox-First Persistence**: In-app inbox delivery is decoupled from push gateways. Domain events ALWAYS persist into `user_notifications` regardless of push status.
- **Zero Delivery Falsification**: When an external push provider fails or is unconfigured, the system reports `PROVIDER_FAILED` or `NOT_CONFIGURED`. It NEVER fabricates a "delivered" status.
- **Lock-Screen Privacy**: All push payloads sent to APNs / FCM use strictly sanitized static text.

---

## 3. Step-by-Step Remediation

### Step 1: Verify Provider Status & Error Code
Query failed notification attempts:
```sql
SELECT provider, result_code, error_category, error_details, count(*) 
FROM notification_attempts 
WHERE created_at > NOW() - INTERVAL '1 hour' AND status != 'DELIVERED' 
GROUP BY provider, result_code, error_category, error_details;
```

### Step 2: Handle Invalid Device Token Spikes
When `result_code = 'UNREGISTERED'` or `should_revoke_device = true`:
1. Cleanse dead tokens to prevent wasted quota:
   ```sql
   DELETE FROM device_installations 
   WHERE id IN (
     SELECT device_installation_id 
     FROM notification_attempts 
     WHERE result_code = 'UNREGISTERED' AND created_at > NOW() - INTERVAL '24 hours'
   );
   ```

### Step 3: Rotate Expired FCM Credentials
1. Generate new Firebase Service Account Key in Google Cloud IAM.
2. Securely copy to `/etc/aicte/fdr/fcm-credentials.json` with permissions `600`.
3. Update environment variable in container:
   ```bash
   export FCM_SERVICE_ACCOUNT_PATH=/etc/aicte/fdr/fcm-credentials.json
   docker compose restart worker
   ```
4. Verify using test notification endpoint:
   ```bash
   curl -X POST http://localhost:8000/v1/notifications/test-delivery \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d '{"platform":"android","provider":"fcm"}'
   ```
