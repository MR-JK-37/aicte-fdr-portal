# Data Protection Impact Assessment (DPIA)
## AICTE Fixed Deposit Receipt & Security Deposit Management System
**Compliance Standard:** Digital Personal Data Protection (DPDP) Act, 2023 (India) & AICTE Statutory Security Standards

---

## 1. System Overview & Data Classification

The AICTE Security Deposit Portal processes personal, institutional, and financial instrument data to enforce statutory security deposits required under Section 10(k) of the AICTE Act 1987.

| Data Category | Data Elements | Processing Purpose | Legal Basis & Retention |
| :--- | :--- | :--- | :--- |
| **Personal Identifiers** | Institution Director Name, Email, Mobile, Role | User Authentication & Statutory Notification | DPDP Sec 4 (Legitimate Use for Statutory Functions); Retained for tenure + 3 years |
| **Authentication Secrets** | Password (Argon2id), 4-Digit Voice PIN (PBKDF2-HMAC-SHA256, 100k iter) | Role-Based Access & Telephony Channel Identity Verification | Irreversible salted hash only; Raw PIN never stored |
| **Voice & Call Telemetry** | WebRTC Audio stream, Call transcripts, DTMF events | Interactive voice reminder acknowledgement | Consent Record required; Audio encrypted in transit (SRTP/DTLS); transcripts retained in audit log |
| **Financial Records** | FDR Number, Bank Branch, IFSC, Deposit Amount, UTR Numbers | Verification of security deposit pledges, lien registration, shortfall detection | Section 10(k) AICTE Act; Permanent immutable retention in chained ledger |

---

## 2. Privacy & Security Safeguards Implemented

### 2.1 Voice Channel Privacy Protection (Pre-PIN Masking)
- **Zero Financial Disclosure Pre-PIN**: Prior to successful verification of the 4-digit PIN, the voice agent is strictly prohibited from speaking institution names, balances, FDR numbers, or dates.
- **Brute-Force Lockout Defense**: 3 consecutive failed PIN attempts trigger an automatic 24-hour channel lockout, marking the session locked and creating an immutable security audit entry.
- **Social Engineering Refusal**: The dialogue machine strictly refuses requests to reveal passwords, change bank account numbers, or alter beneficiary IFSCs over telephony.

### 2.2 Storage & Cryptographic Non-Repudiation
- **Immutable SHA-256 Hash Chain**: Every state transition, document verification, bank confirmation, and voice acknowledgement is cryptographically chained (`row_hash = sha256(prev_hash + payload + timestamp)`). Direct DB row tampering immediately breaks the downstream verification chain.
- **Encrypted Document Quarantine**: Uploaded scanned FDRs undergo ClamAV antivirus scanning, magic-byte MIME type validation, and pHash duplicate matching before encryption and storage in Garage S3.
- **Strict Row-Level Security (RLS)**: PostgreSQL RLS prevents cross-tenant access. Institution accounts can only read their own instruments; Officers require OIDC token validation.

### 2.3 Quiet Hours Telephony Safeguards
- Non-urgent telephony calls and push notifications are suppressed between **20:00 and 08:00 IST** to protect privacy and respect citizen communication rights.

---

## 3. Data Principal Rights & Consent Architecture

- **Right to Access & Correction**: Institutions view all declared vs bank-confirmed details in real-time on the portal diff view.
- **Consent Revocation**: Voice reminder consent can be revoked via portal settings or by saying "stop calling" to the voice agent, which sets `opted_out = true` in `ConsentRecord`.
- **Grievance Redressal**: All escalations and scrutiny disputes route directly to the AICTE Regulation Bureau with formal tracking tickets.
