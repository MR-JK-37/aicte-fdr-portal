# AICTE Security Deposit Portal — Official Demonstration Script

> **Theme**: Smart Automation · AICTE Regulation Bureau · Smart India Hackathon PS 26265
> **Guiding Principle**: Zero simulation / Zero voice calling / Real workflows only.
> **Baseline Metrics**: All metrics defined baseline-first; no invented percentage improvements.

---

## 1. Metric Definitions & Baseline Tracking (SPEC §20 / D-13)

To ensure statutory integrity, this portal rejects fabricated claims of efficiency. Improvements are measured against verified operational baselines:

| Metric Name | Baseline Definition (Manual Legacy Process) | Portal Measurement Mechanism | Target KPI Evaluation |
|---|---|---|---|
| **Submission to Intake Review Time** | Days elapsed from physical post delivery of FDR copy to regional officer file creation (Baseline: 5–14 days). | `created_at` in `instruments` to `assigned_at` / `first_observation_at` in `observations`. | Median and 95th percentile automated turnaround time. |
| **Lien Verification Turnaround** | Manual physical letters posted to bank branches requesting lien confirmation (Baseline: 30–90 days). | Bank-verifier portal login with MFA or authorized statement import match timestamp. | Median duration from submission to verified bank evidence attachment. |
| **Discrepancy Detection Latency** | Discrepancies discovered during annual post-facto audit (Baseline: 6–12 months). | Discrepancy engine evaluates rule breaches instantly upon intake or statement import. | Zero-day exception generation upon document or statement mismatch. |
| **Maturity Reminder Coverage** | Manual diary entries and physical post notices; frequent missed horizons (Baseline: <40% on-time notification). | Automated DB-leased scheduler scanning daily horizons (90d, 60d, 30d, 15d, 0d) with in-app inbox persistence. | 100% due obligation scan coverage with zero duplicate events. |
| **Unauthorized Release Risk** | Physical paper signatures vulnerable to single-signatory forgery or maker-checker collision (Baseline: High audit risk). | Cryptographic SoD enforced in DB + Step-up MFA + Policy Checklist + Ed25519 hash chain. | 0% possibility of single-person release approval or checklist bypass. |

---

## 2. End-to-End Walkthrough of the Six PS Scenarios

### Scenario 1: New FDR Submission (L1 Intake, OCR Assist & Signed Receipt)
- **Role**: `INSTITUTION_SUBMITTER` (College Registrar)
- **Actor URL**: `/submit-fdr` (Web) or Submit Tab (Mobile)
1. **Intake Form**:
   - Registrar logs in via Keycloak OIDC.
   - Selects Institution and uploads digital copy of Fixed Deposit Receipt (`.pdf` or `.png`).
2. **Automated Pipeline**:
   - Document enters quarantine bucket.
   - ClamAV scans file for malware; magic-byte inspection verifies genuine PDF structure.
   - Local OCR extracts FDR Number, Amount, Bank Name, Issue Date, and Maturity Date with per-field confidence scores.
3. **Review & Submit**:
   - Registrar reviews extracted values side-by-side with original document image.
   - Clicks **Submit Instrument**.
4. **Immutable Artifacts**:
   - Version 1 immutable record created.
   - Downloadable official Submission Receipt generated with Ed25519 signed verification QR code.

---

### Scenario 2: Discrepancy Identification (Statement Import & Exceptions)
- **Role**: `FINANCE_VERIFIER` (AICTE Finance Officer)
- **Actor URL**: `/finance/statements`
1. **Statement Intake**:
   - Finance Officer imports official bank statement batch (MT940 or CAMT.053).
   - System checks batch SHA-256 hash to prevent duplicate imports.
2. **Reconciliation Engine**:
   - Engine executes deterministic ruleset matching transaction credits against declared UTRs and FDR amounts.
3. **Exception Queue Handling**:
   - Where amounts differ or institution UTR is missing, the system DOES NOT reject or auto-confirm.
   - Routes transaction to **Reconciliation Exceptions Queue** (`/reconciliation/exceptions`).
   - Officer attaches bank confirmation letter or opens an official Observation.

---

### Scenario 3: Validity Tracking (Active Register & KPI Dashboard)
- **Role**: `REGIONAL_SUPERVISOR` / `INTAKE_OFFICER`
- **Actor URL**: `/dashboard`
1. **Live KPI Register**:
   - Real-time dashboard renders total active deposit portfolio value, count of instruments by evidence level (`L0_DECLARED`, `L1_DOCUMENT_VERIFIED`, `L2_BANK_CONFIRMED`, `L3_LEDGER_RECONCILED`).
2. **Dynamic Search & Filters**:
   - Search by keyed HMAC blind index on instrument numbers.
   - Filter by Region, State, Status (`SUBMITTED`, `UNDER_SCRUTINY`, `ACTIVE`), and Maturity Horizon.

---

### Scenario 4: Approaching Maturity (Automated Reminders & Escalation)
- **Role**: System Scheduled Task (`worker` process) & College Registrar
- **Actor URL**: In-App Inbox (`/notifications`)
1. **Automated Horizon Scan**:
   - DB-leased scheduler scans active instruments due in 90, 60, 30, 15, or 0 days.
2. **Idempotent Dispatch**:
   - Dispatches domain event to outbox.
   - Generates in-app inbox notice with localized text in English, Hindi, or Tamil.
3. **Lock-Screen Privacy**:
   - External push notification sends strictly sanitized summary: *"AICTE FDR Portal — Deadline Notice: An active deposit obligation is approaching maturity."*
   - Zero confidential financial balances exposed on lock-screens.

---

### Scenario 5: Renewal Lineage (Gap & Overlap Handling)
- **Role**: `INSTITUTION_SUBMITTER` & `SCRUTINY_OFFICER`
- **Actor URL**: `/instruments/{id}/renew`
1. **Initiate Renewal**:
   - Registrar submits renewed deposit certificate linking directly to expiring parent FDR.
2. **Lineage Invariants**:
   - System computes time interval between parent maturity date and child issue date:
     - Gap detected (>0 days): Flags compliance warning for un-covered period.
     - Overlap detected: Reconciles interest rollover.
3. **Lineage Tree**:
   - Scrutiny Officer views complete parent-child renewal tree preserving full historical chain of custody.

---

### Scenario 6: Authorised Release (Checklist, SoD & Step-Up MFA)
- **Roles**:
  - `INSTITUTION_SUBMITTER` (Requester)
  - `SCRUTINY_OFFICER` (Recommender)
  - `COMPETENT_AUTHORITY` (Approver)
- **Actor URL**: `/release-workflow`
1. **Release Request**:
   - Registrar initiates release request citing completion of 10-year statutory term.
2. **Policy-Driven Checklist**:
   - System populates statutory clearance items (Regional Office NOC, Vigilance Clearance, Fee Settlement).
   - Each checklist item must be explicitly marked `SATISFIED`. No bulk-ticking allowed.
3. **Separation of Duties (SoD)**:
   - Scrutiny Officer submits formal recommendation (`RECOMMEND_RELEASE`).
   - Recommender CANNOT approve the release (denied by both API and DB trigger).
   - Requester CANNOT approve the release.
4. **Competent Authority Decision**:
   - Competent Authority opens request.
   - System prompts for **Step-Up MFA** (fresh TOTP / passkey authentication required).
   - Decision recorded (`APPROVED`). Request enters `EXECUTION_PENDING` until trusted bank closure advice is uploaded and verified.
5. **Tamper-Evident Audit Record**:
   - Every transition commits atomically to the Ed25519 hash-chained audit log.
