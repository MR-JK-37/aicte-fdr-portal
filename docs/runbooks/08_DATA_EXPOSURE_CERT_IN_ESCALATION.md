# Runbook 08: Sensitive Data Exposure & CERT-In Incident Escalation

> **Classification**: Severity 1 (S1) / Regulatory Obligation
> **Reference**: CERT-In Cyber Security Directions (2022) & DPDP Act 2023 §8(6)

---

## 1. Statutory Mandates & Timelines
Under CERT-In guidelines (Section 70B of IT Act) and the Digital Personal Data Protection (DPDP) Act 2023:
- **Mandatory Reporting Window**: Any cyber security incident must be reported to CERT-In within **6 hours** of noticing.
- **DPBI Notification**: Personal data breach notification must be submitted to the Data Protection Board of India (DPBI) and affected Data Principals without undue delay.

---

## 2. Trigger Scenarios
- Exposure of FDR deposit certificates or bank account numbers via public access or S3 bucket misconfiguration.
- Compromise of API bearer tokens or database credentials leading to bulk data exfiltration.
- Detection of SQL injection, prompt injection data leak, or cross-tenant data exposure.

---

## 3. Step-by-Step Incident Response

### Step 1: Immediate Technical Containment (0 - 1 Hour)
1. Revoke exposed credentials, API keys, or certificates immediately.
2. Invalidate affected sessions:
   ```bash
   kcadm.sh revoke-user-sessions -r aicte <USER_ID_OR_ALL>
   ```
3. Block suspicious IP addresses at the reverse proxy (Caddy / WAF):
   ```bash
   # Add offending IP to blocklist
   iptables -A INPUT -s <OFFENDING_IP> -j DROP
   ```

### Step 2: Impact Assessment & Forensic Evidence Collection (1 - 3 Hours)
1. Export immutable audit chain snapshot for the affected period:
   ```bash
   python scripts/verify_audit_chain.py > audit_verification_report.txt
   ```
2. Determine exact scope of compromised data principals (institutions, officers, bank records).
3. Capture memory dumps and proxy access logs for forensic preservation:
   ```bash
   tar -czf incident_logs_$(date +%s).tar.gz /var/log/caddy/ /var/log/api/
   ```

### Step 3: Formal CERT-In & DPBI Escalation (Within 6 Hours)
Submit Incident Report to CERT-In Incident Response Help Desk (`incident@cert-in.org.in`):
1. **Reporting Form Fields**:
   - Organization Name: All India Council for Technical Education (AICTE)
   - Incident Type: Unauthorized Access / Data Breach
   - Date & Time of Occurrence & Detection (IST)
   - Affected IP Addresses, Domains, and System Identifiers
   - Nature of Compromised Data (Redacted FDR metadata, Institutional Contact Info)
   - Initial Remediation & Mitigation Actions Taken
2. Notify AICTE Chief Information Security Officer (CISO) and Legal Cell.
