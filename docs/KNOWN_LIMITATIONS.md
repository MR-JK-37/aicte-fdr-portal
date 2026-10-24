# Known System Limitations & Preflight External Dependencies

> **Standard Compliance**: MASTER_PROMPT §19, OPEN_DECISIONS §21 (D-01…D-14), PREFLIGHT.md.
> **Status**: Current Production & Staging Architecture Limitations (No invented capabilities).

---

## 1. Regulatory Policy & Sanction Rules (D-01)
- **Status**: AICTE Approval Process Handbook (APH) draft policy tables (e.g., Table 1.4 FDR slabs, Clause 6.46 checklist) are loaded in `DRAFT` status.
- **Limitation**: Any automated compliance evaluation or penalty calculation depending on unapproved rules displays: *"Policy rule not approved / pending Council sign-off"*. The system does not invent policy interpretations.

---

## 2. Direct Bank APIs & SFMS Feeds (D-05, D-06)
- **Status**: Direct real-time API integrations with public sector banks or SFMS (Structured Financial Messaging System) / NEFT / RTGS gateway hooks require formal tripartite Memoranda of Agreement (MoA) between AICTE, the Reserve Bank of India (RBI), and designated nodal banks (e.g., State Bank of India).
- **Supported Reality**: In the absence of signed bank production API contracts, the portal operates via:
  1. **Authorized Statement Import**: Parsing MT940, CAMT.053, and standardized CSV/XLSX statements with cryptographic batch verification.
  2. **Bank-Verifier Portal Role**: Nodal bank branch officers log in with MFA to independently confirm or challenge deposit liens and attach corroborating proof.
- **Limitation**: Direct API polling or simulated bank websockets are strictly excluded from production code.

---

## 3. Bank Guarantees (BG) & e-BG Integration (D-07)
- **Status**: National E-Governance Services Ltd (NeSL) digital e-BG integration is designated as future expansion.
- **Limitation**: BG and e-BG instrument types are currently marked `DISABLED` in the registry. Only Fixed Deposit Receipts (FDR) and Joint Security Deposits are actively processed.

---

## 4. Government Single Sign-On (Parichay / MeriPehchan) (D-08)
- **Status**: Production deployment expects NIC Parichay or MeriPehchan OIDC federation.
- **Supported Reality**: Identity is currently backed by a containerized Keycloak 26.8.1 OIDC realm implementing PKCE, TOTP, WebAuthn passkeys, and RBAC mapping.
- **Limitation**: Production cutover to Parichay requires AICTE NIC project credentials and callback URI registration.

---

## 5. Mobile Push Notifications (FCM / APNs) (PREFLIGHT Item 4)
- **Status**: Production FCM and Apple APNs credentials belong to official AICTE developer accounts.
- **Supported Reality**: In staging/development environments without private `.p8` or `service-account.json` keys, the push engine reports honest `NOT_CONFIGURED` or `PROVIDER_FAILED`.
- **Guarantee**: In-app inbox delivery persists 100% of compliance notices; the system NEVER fabricates a "delivered" status when push is unconfigured.

---

## 6. AI Gateway & Local Tier S Processing (D-12)
- **Status**: Per statutory data confidentiality directives and D-12, all Tier S sensitive operations (analyzing un-redacted financial instruments or institutional casework) are strictly restricted to local Ollama inference.
- **Limitation**: If local Ollama is un-provisioned or `AI_GATEWAY_DISABLED=true`, the system gracefully reports `"unavailable"` or routes directly to human officer review. No fallback to external cloud providers is permitted for Tier S.

---

## 7. Production Hosting Infrastructure (D-09)
- **Status**: The current deployment runs on portable OCI-compliant Docker containers (PostgreSQL 16, MinIO/Garage S3, Keycloak, ClamAV, Caddy).
- **Limitation**: Final production hosting (e.g., MeitY-empanelled cloud or AICTE National Data Centre) is subject to AICTE IT procurement and STQC security certification. Container portability ensures deployment can be transferred without architectural changes.
