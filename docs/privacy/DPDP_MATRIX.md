# Digital Personal Data Protection Act (DPDP 2023) Compliance Matrix

> **Statute**: Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023, Republic of India).
> **Data Fiduciary**: All India Council for Technical Education (AICTE), Regulation Bureau.
> **Scope**: Processing of digital personal data across the Security Deposit / FDR Portal.

---

## 1. Statutory Context & Lawful Basis

Under **Section 4** and **Section 7(b)** of the DPDP Act 2023, AICTE processes personal data on the lawful ground of **legitimate use for state function**:
> *Section 7(b): For the performance by the State or any of its instrumentalities of any function under any law for the time being in force in India or in the interest of sovereignty and integrity of India or security of the State.*

- **Statutory Mandate**: Sections 10 and 11 of the All India Council for Technical Education Act, 1987 (Act No. 52 of 1987) requiring technical education institutions to maintain financial security deposits as a prerequisite for institutional approval and student safeguarding.

---

## 2. Personal Data Inventory & Processing Classification

| Data Element | Category | Purpose of Processing | Storage & Protection Mechanism | Retention Period (D-11) |
|---|---|---|---|---|
| **Registrar / Trustee Full Name** | Identity | Authentication, submission provenance, receipt issuance | RLS tenant isolation; displayed on official receipts | Duration of institutional approval + statutory archive |
| **Official Email Address** | Contact | OIDC login, multi-factor auth, statutory maturity alerts | Keycloak identity store; HMAC-blind indexed | Active account lifecycle + audit chain persistence |
| **Mobile Phone Number** | Contact | SMS/MFA step-up notices, emergency compliance escalation | Keycloak identity store; masked on UI (`+91 98*** **123`) | Active account lifecycle |
| **Signer PAN / Identity Number** | Statutory ID | Verification of FDR lien and authorized institutional trust | Redacted in AI OCR parsing; blind indexed; masked | As prescribed by AICTE Approval Process Handbook (APH) |
| **Bank Account / FDR Number** | Financial | Deposit custody, reconciliation, release execution | Masked on non-privileged views (`SBI/2024/****`); blind indexed | 10-year term + release verification audit period |
| **Device Push Tokens** | Technical | Delivery of mobile compliance notices | Encrypted in `device_installations`; wiped upon user logout | Revoked upon logout or unregistered provider signal |
| **IP Address & User-Agent** | Metadata | CERT-In incident forensics and audit trail | Immutable hash-chained audit log (`audit_log`) | Minimum 180 days per CERT-In Cyber Directions |

---

## 3. Data Principal Rights Implementation (DPDP Chapter III)

| Right | DPDP Section | System Implementation | Verification / Workflow Reference |
|---|---|---|---|
| **Right to Access Information** | §11 | Institution users can access complete dashboard of submitted instruments, audit timelines, and official receipts. | `GET /v1/instruments/{id}/history`, `GET /v1/receipts/verify/{number}` |
| **Right to Correction & Updating** | §12 | Correction requests facilitated via Observation workflow (`F-09`); mistake correction before submission or via officer return. | Intake Observation & Correction workflow (`/v1/observations`) |
| **Right to Erasure** | §12 | Handled in accordance with statutory retention limits. Per **OPEN_DECISIONS D-11**, data is not arbitrarily deleted while legal deposit obligations remain active. | Rights & Retention module (`F-22`) |
| **Right to Grievance Redressal** | §13 | Dedicated grievance submission portal and nodal grievance officer contact published on portal footer. | Help & Support module (`/support`) |
| **Right to Nominate** | §14 | Institutional user administration allows primary Org Admin to nominate alternate registrars or nodal officers. | Institution User Management (`/v1/institutions/{id}/users`) |

---

## 4. Data Fiduciary Obligations (DPDP Chapter II)

| Obligation | DPDP Section | Architecture & Technical Controls |
|---|---|---|
| **Notice & Purpose Limitation** | §5 | Clear bilingual notice presented at login and intake submission specifying that data is processed solely for AICTE security deposit compliance. |
| **Data Protection Safeguards** | §8(5) | - ClamAV malware scanning on all incoming attachments.<br>- Postgres Row Level Security (RLS) enforcing tenant isolation.<br>- SHA-256 hash chains with Ed25519 digital signatures.<br>- TLS 1.3 in transit and AES-256 in object storage. |
| **Personal Data Breach Notification** | §8(6) | In the event of a personal data breach, AICTE notifies the Data Protection Board of India (DPBI) and affected Data Principals within statutory timelines per `docs/runbooks/08_DATA_EXPOSURE_CERT_IN_ESCALATION.md`. |
| **Data Retention & Disposal** | §8(7) | Automated data retention classifier tags documents per APH retention rules; no premature destruction. |
| **Zero Voice / Non-Consensual AI** | User Directive & M-21 | No automated voice calling, AI speech generation, or voice recording in production builds. |
