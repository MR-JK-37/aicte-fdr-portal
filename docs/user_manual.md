# AICTE Security Deposit / FDR Portal — User Manual
## Step-by-Step Guide for Institutions & Regulatory Officers

---

## 1. Role-Based Navigation Overview

The portal supports distinct user roles with strict segregation of duties:
1. **Institution User**: Upload new FDRs, view active register, review reminder notices, request security deposit release.
2. **Scrutiny Officer (Maker)**: Review OCR extraction results (L1), verify bank letters (L2), inspect discrepancies, recommend release requests.
3. **Regional Officer (Checker)**: Approve bank mandates, review maker recommendations, execute dual-authorization gate.
4. **Competent Authority / Member Secretary**: Sign statutory release orders, issue cryptographically verifiable QR certificates.
5. **Auditor**: Inspect tamper-proof SHA-256 event ledger and query compliance analytics.

---

## 2. Problem Statement Scenarios Walkthrough

### Scenario 1: New FDR Submission & AI Extraction (L1 Intake)
1. Navigate to the **Submit FDR (L1)** tab.
2. Drag and drop the scanned Fixed Deposit Receipt (PDF, PNG, JPG).
3. The automated pipeline performs:
   - Antivirus screening & MIME byte verification.
   - Perceptual hash (pHash) duplicate check.
   - Tesseract OCR & Structured LLM extraction.
4. Review extracted fields with color-coded confidence score chips:
   - Instrument Number, Issuing Bank, IFSC, Amount, Issue Date, Maturity Date.
5. Scrutiny Officer clicks **Scrutiny Officer Confirm (Upgrade to L1)** to commit to the register.

---

### Scenario 2: Active Instrument Register & Risk Dashboard
1. Navigate to the **KPI Dashboard** tab.
2. Compare high-level metrics:
   - Legacy Manual Register vs Automated AI Oversight.
   - Status Breakdown: Active, Expiring Soon, Matured, Forfeited.
   - Evidence Distribution: Level 0 (Unverified) $\rightarrow$ Level 1 (OCR) $\rightarrow$ Level 2 (Bank Confirmed) $\rightarrow$ Level 3 (Statement Reconciled).
3. Use the search bar to filter by institution or bank name.

---

### Scenario 3: Bank Verification & Bank Statement UTR Reconciliation (L2/L3)
1. Navigate to **Bank Verification (L2/L3)**.
2. **Upload AICTE Statement CSV (L3 Gold Standard)**:
   - Ingest AICTE corporate account bank statement.
   - Engine matches credit transaction UTR numbers and exact credit amounts.
   - Matching instruments are instantly promoted to **Level 3 (Statement Reconciled)**.
3. **Bank Dispatch Letters**:
   - Preview and print official verification letters to Bank Branch Managers under Section 10(k) of the AICTE Act.
4. **Discrepancies Diff**:
   - Inspect highlighted differences (e.g. single account vs joint name with AICTE).
   - Resolve or override with statutory justification.

---

### Scenario 4: Automated Maturity Ladder & Interactive Reminders
1. Navigate to **Reminder Ladder**.
2. Observe the automated 6-step escalation schedule:
   - **T-90 Days**: In-App Advisory.
   - **T-60 Days**: Push Notification & Email.
   - **T-30 Days**: In-App AI Voice Bot Call (English, Hindi, Tamil).
   - **T-7 Days**: Daily Outbound Urgent Call.
   - **T-0 Days**: Maturity Expiry Notice.
   - **T+15 Days**: Regulation Bureau Escalation & Show-Cause Hold.
3. Use the **Simulate Ladder Advance** controls (`+30d`, `+60d`, `+83d`, `+300d`) to test future time scenarios.
4. Click **[Acknowledge]**, **[Snooze 7d]**, or **[AI Voice Call]** on any pending reminder.

---

### Scenario 5: Autonomous Voice Agent Interaction
1. When an AI Voice Call triggers (or upon clicking **AI Voice Call** in the top navigation):
   - Incoming call overlay opens with animated audio waveform.
   - AI bot provides opening statutory disclosure: *"Namaskar. This is AICTE automated security deposit service calling... To proceed, please enter your 4-digit voice PIN."*
2. **Enter Voice Security PIN**:
   - Key in 4 digits on the interactive keypad (Demo PIN: `1234`).
   - If incorrect, attempt counter decrements; 3 failed attempts lock the channel for 24 hours.
3. **Post-PIN Briefing**:
   - Bot speaks the exact amount in Indian numbering system (e.g. *"Thirty-Five Lakh Rupees"* / *"पैंतीस लाख रुपये"* / *"முப்பத்தைந்து லட்சம் ரூபாய்"*).
   - Last 4 digits of FDR are spoken.
4. **Voice Actions**:
   - Press 1 to acknowledge reminder.
   - Press 2 to request 7-day snooze.
   - Press 3 to request officer callback.
5. Acknowledgement is cryptographically committed to the audit ledger with a SHA-256 receipt.

---

### Scenario 6: Security Deposit Release & Maker-Checker Workflow
1. Navigate to **Release Authorization**.
2. Select an instrument to evaluate.
3. System runs the **Automated Statutory Eligibility Checklist (APH Clause 6.46)**:
   - Term Served (8/10 Years minimum lock-in).
   - Zero Open Discrepancies.
   - Scrutiny Clearance (No pending inspection observations).
   - Financial Dues Cleared (Zero shortfall or unpaid penalties).
4. **Segregation of Duties Pipeline**:
   - **Step 1 (Maker - Scrutiny Officer)**: Enters observations and clicks *Recommend for Release*.
   - **Step 2 (Checker - Regional Officer)**: Validates bank refund mandate and clicks *Dual-Authorize Approval*.
   - **Step 3 (Sign-Off - Member Secretary)**: Issues cryptographic digital order.
5. Preview and print the official **Certificate of Security Deposit Release** featuring the embedded verification QR code and SHA-256 seal.

---

### Scenario 7: Compliance Copilot & Natural Language SQL Analytics
1. Navigate to **AI Copilot & SQL**.
2. **Handbook RAG Mode**:
   - Ask any regulatory question (e.g. *"What is the mandatory security deposit for new engineering colleges?"*).
   - Returns factual answer with citations from the AICTE Approval Process Handbook (Table 6.1, Cl. 6.12).
3. **Text-to-SQL Analytics Mode**:
   - Query in natural language (e.g. *"Show deposits grouped by bank with total crores and L3 verified count"*).
   - Preview generated SQL query with safety badges (`READ_ONLY`, `ALLOW_LISTED_VIEW`, `sqlglot_validated`).
   - Inspect live tabular query results.
