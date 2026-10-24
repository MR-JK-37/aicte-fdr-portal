**AICTE SECURITY DEPOSIT /  
FDR MANAGEMENT PORTAL**

Deep Research & Production Implementation Specification

SIH Problem Statement 26265  
Research cut-off: 23 October 2026 \| Revision: v3.0

| **MANDATORY SCOPE: The AI calling/voice-agent subsystem is removed. No WebRTC calling, PSTN calling, speech-to-text, text-to-speech, call PINs, call transcripts or call recordings. The web portal and native mobile app share one secure backend and the same authoritative records. Production must not contain seeded demo records, fake bank responses or mocked provider success.** |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

Purpose: a buildable specification for a team moving from research to implementation. It distinguishes official-source facts, engineering recommendations, assumptions and decisions requiring AICTE approval.

# Document control, scope and evidence labels

Document version: 3.0 \| Date: 23 October 2026 \| Subject: SIH PS 26265 — Streamline security deposit / FDR portal.

This is a research and engineering specification. It is not an official AICTE interpretation, a legal opinion, a security certification, or evidence that any integration has been provisioned. The product team must obtain written policy, process, security, legal, hosting and integration sign-offs from the authorised owners before production use.

| **Label**                                     | **Meaning in this report**                                                                                                     | **How the build team must use it**                                                                                      |
|-----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| VERIFIED SOURCE                               | Directly supported by an official primary page, standard owner or official document cited in Appendix A.                       | Preserve the claim and citation; re-check amendments/versions at implementation time.                                   |
| ENGINEERING RECOMMENDATION                    | Proposed design based on common secure-system practice and the reviewed standards.                                             | Adopt or document an architecture decision record (ADR) explaining an alternative.                                      |
| AICTE DECISION REQUIRED                       | Business process, legal authority, data, hosting or integration not established by reviewed sources.                           | Do not invent a default as if it were official; keep configurable and block production decision paths until signed off. |
| NOT VERIFIED / NO PUBLIC INTERFACE IDENTIFIED | No universal public integration was established by the sources reviewed. This is not proof that no private integration exists. | Ask AICTE and counterpart organisations for official specifications, agreements, test environment and owners.           |
| TEST-ONLY                                     | Permitted only in local/CI/test environment.                                                                                   | Make impossible to enable accidentally in production; test startup/deployment guardrails.                               |

## Most important improvement over the previous report

This revision adds a source-indexed extraction of the AICTE APH Clause 6.46 release path, an explicit DPDP commencement planning table from Gazette notifications, a correction audit, and separate state machines for instrument, evidence, observation and release request. It narrows the production baseline, removes voice calling completely, and distinguishes source facts from decisions AICTE must sign off. Direct opening of the APH PDF failed with 502 in the research session; the report flags that limitation rather than pretending the full document was directly reviewed.

# 1. Executive findings

## 1.1 Target product

Build a secure case-management and system-of-record platform that tracks the applicable security obligation and the evidence supporting it over time. It must cover current online deposits and the legacy FDR evidence path if AICTE confirms both remain in scope. It must connect institutional submissions, evidence review, bank/ledger verification, discrepancies, maturity, renewal/replacement, release requests, decisions and audit history in one traceable workflow.

## 1.2 Decisions that define the product

- One authoritative backend and one authoritative database. Web and mobile are clients—not separate systems of record and not separate workflow engines.

- Every financial or policy fact has provenance: who provided it, which source supports it, which version was reviewed, who made the verification decision and when.

- No “verified” badge based only on OCR, image inspection, AI score or institution declaration. An instrument can be document-extracted without being bank-confirmed.

- Maturity is a deadline/event, not permission to release. Release decisions require policy checks, an authorised human decision and execution evidence.

- Role-based access control (RBAC) must be combined with record scope and context (ABAC). A role label alone is not sufficient for multi-institution data protection.

- Mobile push is best-effort delivery. The server persists the event and in-app inbox record first; provider acceptance, device delivery, opening and acknowledgement are separate measurements.

- No mock success in production. An unavailable bank connector must be shown as unavailable or awaiting evidence—not as “bank verified.”

- AI/OCR is a bounded assistant, not the policy engine, bank, identity system or release authority.

## 1.3 Recommended architecture in one view

> Responsive Web Client ------------------\\
>
> +--\> HTTPS API / Identity / Policy Enforcement
>
> Native Android & iOS App --------------/ \|
>
> v
>
> Modular Backend Domains
>
> Institution Registry \| Instruments \| Documents \| Evidence/Verification
>
> Observations \| Reconciliation \| Lifecycle \| Renewal/Release \| Reports/Audit
>
> \|
>
> +------------------+------------------+
>
> v v v
>
> PostgreSQL Encrypted Object Store Outbox/Jobs
>
> \|
>
> v
>
> OCR/Scanning \| Deadline Engine \| Notification Dispatch
>
> \|
>
> +--------------------+---------------+-------------+
>
> v v v v
>
> FCM APNs Web Push Email\*
>
> \*Only when provider/domain configuration and institutional approval are real.
>
> No voice/calling/telephony subsystem.

Recommended first release: modular monolith (one backend codebase with strict internal domain boundaries), PostgreSQL, encrypted object storage, a durable outbox/worker, approved identity provider and push/email adapters. Microservices, LLM orchestration, natural-language SQL and predictive scoring are not prerequisites.

## 1.4 Accuracy audit: conclusions corrected or deliberately left open

| **Topic**                   | **What the reviewed evidence supports**                                                                                                                                                                             | **Implementation consequence**                                                                                                                                    |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Deposit amounts             | The AICTE-hosted APH 2024–2027 PDF search-indexed text lists the amounts in Table 1.4 and references a doubled amount for private leased building/land.                                                             | Use only as source-versioned rules after official owner review; evaluate programme/level, exemptions, effective date, historical instrument and later amendments. |
| Release procedure           | The indexed APH 2024–2027 Clause 6.46 text lists the request letter, Affidavit 6, FDR/payment evidence, latest LoA/EoA, relevant clearances and separate FDR/RPGF NOC versus RTGS sanction.                         | Make each evidence/clearance an explicit conditional checklist item; do not compress release into one “eligible” boolean.                                         |
| Current policy corpus       | The APH PDF is officially hosted, but the PDF endpoint did not open in the research browser; the indexed text was available. A complete authoritative amendments sweep could not be proven from the reviewed pages. | Before coding policy, download the current APH and all official corrigenda/notices; have AICTE sign the rule register and test cases.                             |
| Penalty percentages / dates | Prior research identified inconsistent interpretations across materials; this report has not established a single authoritative value for every penalty scenario.                                                   | Keep any unsettled rule in DRAFT/BLOCKED state; do not charge, waive or reject from a guessed percentage.                                                         |
| FDR verification APIs       | Reviewed public sources did not establish one universal API for validating all paper FDRs. This does not prove that private bank-to-bank or AICTE-specific integrations do not exist.                               | Require a named bank/data owner, authorised route, test credentials and proof of production operation for every connector.                                        |
| GIGW and STQC               | GIGW is the government-app guideline framework; STQC runs a separate Website Quality Certification process.                                                                                                         | Build against GIGW; do not claim a certificate until formal assessment/certificate is completed.                                                                  |
| Push delivery               | Android/iOS providers expose different telemetry and cannot guarantee that a user sees every notification immediately.                                                                                              | Persist in-app event first, track provider/device/user states separately, set measurable dispatch targets but never promise instant delivery.                     |
| DPDP commencement           | The Act and 2025 Rules have staggered commencement under official Gazette notifications.                                                                                                                            | Maintain a legal applicability matrix by provision/date, refreshed by AICTE counsel—not a blanket “DPDP compliant” checkbox.                                      |

# 2. Source-verified AICTE domain: what is known and what is not

## 2.1 Security deposit table

The official AICTE-hosted Approval Process Handbook 2024–2027, Clause 1.12 and Table 1.4, lists the programme/level amounts reproduced below. It also states that the amount is double in the case of private leased building/land and says the amount remains with the Council for 10 years; the principal is returned at the end of the term, subject to possible extension and/or forfeiture in specified circumstances. These are statements from the cited handbook, not a universal rule for every institution: applicability, exemptions, later amendments and the correct policy version must be assessed for each case. \[R1\]

| **Programme in Table 1.4**               | **Diploma / Post Diploma** | **Undergraduate** | **PG Diploma / PG Degree** |
|------------------------------------------|----------------------------|-------------------|----------------------------|
| Engineering and Technology               | ₹15 lakh                   | ₹35 lakh          | ₹15 lakh                   |
| Planning                                 | ₹15 lakh                   | ₹15 lakh          | ₹15 lakh                   |
| Applied Arts and Crafts                  | ₹15 lakh                   | ₹15 lakh          | ₹15 lakh                   |
| Design                                   | ₹15 lakh                   | ₹15 lakh          | ₹15 lakh                   |
| Hotel Management and Catering Technology | ₹15 lakh                   | ₹15 lakh          | ₹15 lakh                   |
| Computer Applications (e.g. BCA/MCA)     | —                          | ₹5 lakh           | ₹15 lakh                   |
| Management (e.g. BBA/MBA)                | —                          | ₹5 lakh           | ₹15 lakh                   |

| **Accuracy guardrail: these amounts are the table values in the cited APH, not a rule to blindly charge every institution. Table 1.4 does not list every conceivable programme category; programme applicability, exemptions, conversions, historical deposits and amendments need official validation before the rules engine can decide an amount.** |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 2.2 What must not be hardcoded from secondary or conflicting material

- Penalty percentages or cut-off dates where official handbook text and other material appear inconsistent. The prior report identified an apparent 10%/20% versus 10%/50% discrepancy in secondary materials. Do not resolve this using an LLM or guesswork; require written confirmation from AICTE’s policy owner and legal team.

- Exemptions, tenure, early encashment, closure, programme conversion, balance deposit and release requirements that depend on other clauses or circulars. Each rule must reference an official source and effective date.

- Who can approve releases, at what amount/region/programme threshold, and whether the same person can scrutinise and approve. The technical report cannot assign statutory authority.

- Whether this application replaces existing AICTE workflows, is a sub-system, or only assists the Regulation Bureau. This affects authoritative records, data migration, signatures and integration design.

## 2.3 APH release procedure: build the checklist from the source

The indexed text of the AICTE-hosted Approval Process Handbook 2024–2027, Clause 6.46 (“Release of Security Deposit”), describes a defined document and clearance path. The list below reflects the indexed text of that specific handbook; the AICTE policy owner must verify the final downloadable PDF, current amendments, and whether each requirement applies to a case before the production rules engine is approved. \[R1\]

| **APH 6.46 element (source-derived)**                                                                                            | **How the portal should model it**                                                                              | **Control / accuracy boundary**                                                                                                        |
|----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| Institution request/application letter for FDR / RTGS release                                                                    | Required checklist evidence with document category, submitted version, uploader, review status and source hash. | Do not auto-accept a blank/malformed letter; let policy owner define template/mandatory fields.                                        |
| Affidavit 6 containing institution and Trust/Society/Company details and FDR/RTGS details                                        | Checklist item linked to the relevant legal entity and instrument.                                              | Store the affidavit template/version and the date submitted; handle corrected versions without erasing history.                        |
| Copy of FDR to be released; for a corpus fund created by RPGF, DD copies if applicable; or online security-deposit payment proof | Conditional document rule based on the historical instrument/payment type.                                      | A file being present is not proof of authenticity or account credit; use the separate verification process.                            |
| Copy of latest LoA / EoA                                                                                                         | Checklist item with issued/effective date and source.                                                           | The approved policy owner must define acceptable official source and validity/version checks.                                          |
| Clearances from PGRC, Vigilance Cell and other AICTE Cells/Bureaus relevant to grants released to institutions                   | Separate clearance records with source, responsible cell, received date and outcome.                            | Do not infer “clear” from an empty queue, missing data, or an integration outage. Each required clearance must be explicitly resolved. |
| For FDR/RPGF, NOC from Approval Bureau; for RTGS, sanction order issued by Council                                               | Instrument-type-specific final authorisation artifact.                                                          | Keep FDR/RPGF NOC path distinct from RTGS sanction path; never issue a portal-generated substitute for the official instrument.        |
| Where financial embezzlement with a Government body/bank exists, no release until NOC from that body is received                 | Policy-conditioned hold/clearance item with evidence and authority.                                             | Do not infer such a condition from an AI score; the official case owner records the basis and required evidence.                       |
| APH also states the Council may initiate penal action for security-deposit norm violations                                       | Escalation/reference note and policy-linked casework.                                                           | The portal must not calculate or impose penalty unless the exact applicable rule/version is confirmed and approved.                    |

| **Implementation rule: every release checklist row must be one of SATISFIED / NOT SATISFIED / PENDING SOURCE / NOT APPLICABLE, with the deciding user, evidence link, rule version and reason. “All documents uploaded” is not equivalent to clearance, approval or release.** |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 2.4 Two evidence paths are required

| **Evidence path**                       | **What it establishes**                                            | **Required boundary**                                                                                                                                |
|-----------------------------------------|--------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| Online deposit / credit                 | Evidence that a transaction credited the authorised AICTE account. | Ideally use an authorised bank/API or controlled bank-origin statement import. A receipt/UTR supplied by an institution is a claim until reconciled. |
| Legacy paper FDR                        | Evidence from the instrument document.                             | A separately approved bank-confirmation process is required; receipt scan and OCR cannot prove a live deposit, lien or current encashment status.    |
| Other instruments (e.g. bank guarantee) | A separate security instrument, if confirmed in scope.             | Only support if AICTE confirms types and valid bank-authentication channels; do not claim unapproved SFMS/NeSL/bank integration exists.              |

## 2.5 Evidence terminology

| **Term**                         | **Definition**                                                                                                            | **Transition authority**                                                    |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| Institution-declared             | A value entered/submitted by an institution user.                                                                         | Institution user; provenance remains declared.                              |
| Document-extracted               | OCR/parser proposes a field from a specific document/page/region.                                                         | Reviewer may confirm/correct; extraction alone does not elevate bank trust. |
| Bank-confirmed                   | An authorised verifier has reviewed approved evidence from the named bank channel/person and recorded what was confirmed. | Designated verification role, with independent review if policy requires.   |
| Ledger-reconciled                | A deposit credit was matched to an authoritative bank/AICTE ledger source under an approved reconciliation rule.          | Finance/verifier; ambiguous matches require exception review.               |
| Rejected / inconclusive evidence | Evidence is insufficient, inconsistent, failed, or cannot be confirmed.                                                   | Authorised reviewer with reason; not an automated fraud conviction.         |

Prefer independent evidence attributes to one simplistic L0-L3 score. The old blueprint’s L0–L3 model is a useful visual shorthand, but legacy FDR confirmation and online-ledger matching are different kinds of evidence. A single score can incorrectly imply that a ledger reconciliation verifies the existence/lien of a separate FDR.

# 3. Production scope: module inventory and boundaries

| **Module**                    | **Core responsibility**                                                                                                  | **Must not do**                                                                                       |
|-------------------------------|--------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| Institution registry          | Authoritative institution/legal entity, programme, region, status, verified representatives and source freshness.        | Allow institution users to create arbitrary official identities or change regulator-owned attributes. |
| Identity & access             | Sign-in, MFA, session/revocation, invitation, role assignment, institution/region attributes and access recertification. | Treat hiding a button or trusting client-side claims as authorisation.                                |
| Instrument register           | Instrument records, versioning, history, lifecycle and renewal lineage.                                                  | Overwrite submitted values or delete history in place.                                                |
| Document/evidence vault       | Quarantine, malware scan, sanitisation, hashes, retention labels, versioned documents and downloads.                     | Serve unscanned uploads as trusted evidence or make private buckets public.                           |
| Verification & reconciliation | Bank confirmation request/evidence, authorised statement import, matching, exceptions and review.                        | Create a fake bank response or auto-accept fuzzy financial matches.                                   |
| Observations/casework         | Discrepancy/observation queue, due date, institution response, owner and resolution.                                     | Treat an AI alert as a final fraud finding.                                                           |
| Lifecycle/deadlines           | Expiry/maturity calculations, reminder schedules, renewal checks and escalations.                                        | Use mobile/client time as source of truth or rely on a push to execute a deadline.                    |
| Release/refund                | Rule checklist, recommendation, independent approval, decision reason and actual execution evidence.                     | Automatically release based only on maturity, checklist completion or LLM advice.                     |
| Notification service          | Persistent inbox, dispatch channels, retries, token lifecycle, delivery telemetry and preferences.                       | Claim the recipient saw a notification merely because the provider accepted it.                       |
| Policy/rules registry         | Approved rule versions, citations, effective dates, scope, signer/approver and supersession.                             | Silently change the policy behind a pending or historical decision.                                   |
| Reporting/audit               | Authorised dashboards/exports, history, decision trace, integration runs and metrics.                                    | Allow reports/exports to bypass record-level security.                                                |
| Integration administration    | Connector configuration, keys/certificates, source health, import batch history and ownership.                           | Present a connector as live without credentials, approved route and production test.                  |

## 3.1 Exclude entirely

- AI voice agent or AI calling app, real-time voice sessions, WebRTC calling, PSTN calling, call provider/telephony SDKs, call PINs, speech recognition/synthesis, recordings and transcripts.

- A demo/simulated clock in production. Time travel is allowed in automated tests only.

- Mock data seeding or fake service responses in production images, databases, environments, notifications or screenshots.

- AI-generated release decision, automatic “genuine FDR” declarations and unreviewed policy inference.

- Premature microservices, multi-agent orchestration, unconstrained text-to-SQL and black-box risk scores in the core release.

# 4. Complete roles and their governance

The following is a proposed functional role catalogue, not a claim that these exact job titles exist in AICTE’s formal service rules. AICTE must map these functions to approved posts/teams and confirm delegations before assigning them in production.

| **Proposed role**                          | **Scope attributes**                                    | **May do**                                                                                                              | **Must not do**                                                                                                              |
|--------------------------------------------|---------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| Institution Organisation Administrator     | One verified institution/legal entity only.             | Invite/deactivate institution users; set institution contacts; view own cases; submit if separately granted.            | Assign AICTE roles, alter regulator-owned institution identifiers, view other institutions, approve own release.             |
| Institution Submitter / Compliance Officer | Own institution; permitted programme/work items.        | Create drafts, upload documents, submit, respond to observations, request renewal/release.                              | Self-mark bank confirmed, change official policy or erase submitted versions.                                                |
| Institution Viewer                         | Own institution; read-only.                             | View status/timeline, download permitted documents, see notices and tasks.                                              | Submit, edit, approve, manage roles or make cross-institution exports.                                                       |
| Intake / Registry Officer                  | Assigned queue/region.                                  | Check completeness, categorise, assign, return for corrections.                                                         | Final release approval if policy requires independent separation.                                                            |
| Scrutiny Officer                           | Assigned cases/region/programmes.                       | Review evidence, raise observations, recommend outcomes and record reasons.                                             | Approve the same case if they initiated/recommended it and maker-checker forbids it.                                         |
| Finance / Verification Officer             | Authorised verification scope, account/statement scope. | Review bank responses, import authorised statements, reconcile transactions and resolve match exceptions with evidence. | Edit source statements, use global data extracts without permission or approve own exception when dual review is required.   |
| Regional Supervisor / Bureau Reviewer      | Assigned region or delegated bureau scope.              | Assign work, review queue aging, handle escalation, review recommendations and reports.                                 | Unrestricted cross-region access unless formally granted and logged.                                                         |
| Competent Authority / Release Approver     | Decision class/region/programme/delegation limit.       | Approve/reject/return/defer with reason and evidence after step-up authentication.                                      | Approve outside delegation, approve own case, bypass mandatory checklist or change evidence source.                          |
| Audit / Compliance Reviewer                | Explicit read-only scope.                               | Review records, policy versions, events, access audit, exports and control evidence.                                    | Alter business data, audit trail or decision state.                                                                          |
| Identity / Access Administrator            | Identity layer and approved assignment queue.           | Provision/deactivate identity, assign approved roles, support MFA recovery and review access.                           | Gain ordinary financial case access by default or grant own privilege.                                                       |
| Platform / Security Operator               | Infrastructure/admin plane, not business case scope.    | Deploy, monitor, rotate secrets, manage backups, incident response and service health.                                  | Perform business approvals using ops privileges; routine access to plaintext case documents should be separately restricted. |
| Integration service identity               | Named connector and API scopes only.                    | Import a bank statement, call a configured provider or process a queue under narrow machine role.                       | Interactive login, broad database access, role administration or unlogged actions.                                           |
| Participating bank verifier (conditional)  | Only approved bank organisation and assigned requests.  | Respond to assigned confirmation requests and view only submitted/requested fields.                                     | Access AICTE-wide case data, approve AICTE releases or be enabled before legal/procedural onboarding.                        |

## 4.1 Model permissions as actions, not pages

Define an action catalogue that can be tested independently of the UI. Suggested permission verbs include: view, create_draft, edit_draft, submit, upload_evidence, download_evidence, raise_observation, respond_observation, assign_case, recommend, verify_bank_evidence, reconcile_statement, resolve_exception, request_release, approve_release, execute_release_record, export_report, manage_institution_users, manage_roles, manage_policy, configure_integrations, view_audit and administer_platform.

## 4.2 Recommended RBAC + ABAC evaluation

> authorise(principal, action, resource, context):
>
> 1\. Reject if principal identity is inactive, session revoked or token invalid.
>
> 2\. Require valid MFA / step-up assurance for privileged decision actions.
>
> 3\. Require action permission granted by an approved role assignment.
>
> 4\. Check organisation, institution, region, assignment and programme attributes.
>
> 5\. Check resource state permits this action in the workflow state machine.
>
> 6\. Check delegation limits, separation-of-duties and policy version.
>
> 7\. Deny by default on missing/ambiguous attributes or policy engine failure.
>
> 8\. For consequential writes, record actor, reason, correlation ID and audit event.
>
> 9\. Return only the data fields the role is allowed to see.

## 4.3 Separation of duties

> 1\. Institution representative creates/submits the case and the evidence snapshot becomes versioned.
>
> 2\. Intake staff checks completeness and routes it to an authorised queue.
>
> 3\. Scrutiny officer reviews the case and recommends or returns it.
>
> 4\. An independent verifier reviews bank-confirmation/ledger evidence where applicable.
>
> 5\. The competent authority approves/rejects based on the signed-off role matrix and delegated authority.
>
> 6\. The actual release transaction is executed through the authorised financial process. The portal records transaction reference/evidence only after it receives trusted confirmation.
>
> 7\. Auditor reviews records and decisions without write privileges.

For high-impact actions, the database/workflow must reject the same user acting as both maker and checker. Emergency access (“break glass”) should require a separate privileged workflow, short expiry, reason, enhanced logs and retrospective review.

## 4.4 Login and account lifecycle

- Federate to an AICTE-approved OIDC identity provider if AICTE provisions one. A self-hosted provider such as Keycloak is an engineering option, not a presumed official identity arrangement.

- Web: authorization-code flow with PKCE where supported; use secure, HttpOnly, SameSite cookies when using a cookie-based browser session and protect state-changing requests against CSRF. Mobile: native OIDC authorization-code + PKCE and OS secure credential storage.

- Require MFA for AICTE staff, administrators and approval roles. Require step-up MFA/re-authentication immediately before release/forfeiture or privileged role/policy changes.

- Institution user onboarding must verify the representative’s authority through an AICTE-approved process. Email verification alone is not proof of authority to represent a legal entity.

- Use single-use, short-lived invitations; invite only into one institution; prevent users from submitting their own institution_id, region, role or approval limit as trusted claims.

- Privileged recovery requires documented identity proofing/dual control; no email-only recovery for a high-privilege account.

- Provide session/device list, remote session revocation, refresh-token rotation, lockout/rate limits, suspicious-login alerts and immediate access revocation when assignments end.

- Run quarterly or policy-defined access recertification for privileged users; keep a named role owner and reason for every access grant.

# 5. Authorization matrix: minimum baseline

This matrix is intentionally a proposed minimum. “Assigned” means the resource is in the user’s institution/region/case/connector scope and the state transition is allowed. “Restricted admin” means the action needs an approved role and often maker-checker.

| **Action**                          | **Institution submitter**  | **Institution viewer** | **Intake / scrutiny**          | **Verifier**                               | **Competent authority**                    | **Auditor**                | **Platform ops**                                                                    |
|-------------------------------------|----------------------------|------------------------|--------------------------------|--------------------------------------------|--------------------------------------------|----------------------------|-------------------------------------------------------------------------------------|
| View own institution instruments    | Yes                        | Yes                    | Assigned                       | Assigned verification scope                | Delegated scope                            | Read-only approved scope   | No routine content access                                                           |
| Create/edit draft                   | Yes                        | No                     | No                             | No                                         | No                                         | No                         | No                                                                                  |
| Submit instrument / release request | Yes                        | No                     | No                             | No                                         | No                                         | No                         | No                                                                                  |
| Upload/correct evidence             | Own cases                  | No                     | As assigned                    | As assigned                                | No by default                              | No                         | Infrastructure-only support path                                                    |
| Raise/resolve observation           | Respond only               | No                     | Raise/review                   | Technical match exceptions                 | Review escalation                          | Read-only                  | No                                                                                  |
| Confirm bank evidence               | No                         | No                     | No unless separately delegated | Yes, independently reviewed where required | Can consider in decision                   | Read-only                  | No                                                                                  |
| Reconcile bank statement            | No                         | No                     | No                             | Yes within source/account scope            | Read-only or exception approval per policy | Read-only                  | No                                                                                  |
| Recommend release                   | Request only               | No                     | Assigned reviewer              | Verification evidence only                 | No if same-person conflict                 | Read-only                  | No                                                                                  |
| Approve release/forfeiture          | No                         | No                     | No by default                  | No by default                              | Yes within delegation                      | No                         | No                                                                                  |
| Record financial execution          | No                         | No                     | No                             | Authorised finance operation only          | Only if formally included in process       | Read-only                  | No                                                                                  |
| Manage users within institution     | Admin only                 | No                     | No                             | No                                         | No                                         | No                         | Identity admin may administer identity, not institution membership without approval |
| Grant AICTE roles                   | No                         | No                     | No                             | No                                         | No                                         | No                         | Identity admin follows approved workflow; no self-grant                             |
| Change policy rules                 | No                         | No                     | No                             | No                                         | Policy owner + independent approver        | Review only                | Deploy configuration, not approve policy                                            |
| Export bulk records                 | Own scoped, policy-limited | No by default          | Assigned scope if permitted    | Assigned scope if permitted                | Delegated reports                          | Auditor exports if granted | No routine business export                                                          |
| Read / modify audit events          | No                         | No                     | Read relevant case history     | Read relevant case history                 | Read scope                                 | Read-only auditor          | No update/delete rights for application operators                                   |

## Mandatory backend test cases

- User changes an instrument UUID to another institution’s UUID in path, query, bulk export, document download or notification deep link: request must be denied without leaking whether the object exists.

- Client adds protected properties such as status=verified, role=admin, region=all, evidence_level=bank_confirmed or approved=true: server rejects/ignores them and records attempted tampering where appropriate.

- A user whose role is correct but region/assignment is stale is denied. A role change revokes effective access on the next valid authorization check; cached client UI does not preserve server access.

- Connection-pool reuse does not leak row-level security context between users. Test with actual DB role/pool settings rather than a mocked repository.

- Two simultaneous approvals or imports do not create duplicate decisions/transfers; optimistic concurrency and idempotency prevent repeat effects.

# 6. Domain workflow and lifecycle design

## 6.1 Use separate, linked state machines—not one overloaded status

The instrument, evidence review, observation/casework, renewal relationship and release request have different lifecycles. Model them as separate aggregates connected by IDs and state-transition events. A single long status field breaks down for early closure requests, multiple instruments, parallel clearances, inconclusive bank responses and matured instruments that remain unreleased.

> INSTRUMENT RECORD
>
> DRAFT -\> SUBMITTED -\> INTAKE_REVIEW -\> SCRUTINY -\> ACTIVE_TRACKING
>
> -\> SUPERSEDED / CANCELLED / ARCHIVED (only via approved transitions)
>
> EVIDENCE ITEM (per evidence source / field group)
>
> DECLARED -\> EXTRACTED (optional) -\> REVIEWED
>
> -\> BANK_CONFIRMED (where approved evidence exists)
>
> -\> LEDGER_RECONCILED (online payment path only, where applicable)
>
> -\> INCONCLUSIVE / REJECTED (always with reason and reviewer)
>
> OBSERVATION / CASEWORK
>
> OPEN -\> AWAITING_INSTITUTION -\> RESPONSE_RECEIVED -\> UNDER_REVIEW
>
> -\> RESOLVED / CLOSED (re-open only with reason and audit)
>
> RELEASE REQUEST (independent lifecycle; may start before maturity when policy permits)
>
> DRAFT -\> SUBMITTED -\> COMPLETENESS_REVIEW -\> REQUIRED_CLEARANCES
>
> -\> SCRUTINY/RECOMMENDATION -\> COMPETENT_AUTHORITY_DECISION
>
> -\> EXECUTION_PENDING -\> RELEASED/DISCHARGED (only with trusted execution evidence)
>
> -\> RETURNED / DEFERRED / REJECTED / CANCELLED (authorised transition)
>
> DEADLINE/MATURITY: derived from approved dates + policy; not itself authority to release.
>
> RENEWAL: create a new instrument and explicit old-\>new lineage; retain prior record.

Exact states, transitions, terminology and authority must be agreed with AICTE. Evidence dimensions are not a ranking where every type is comparable: a legacy bank-confirmed FDR is not “less than” or “more than” an online credit match in all respects. The UI should show evidence type and source, not merely a green badge.

## 6.2 Required workflow invariants

- Every transition has from_state, to_state, actor, timestamp, reason code, free-text reason when required, policy version, related evidence and request/correlation ID.

- Only an allow-listed transition can occur. State changes happen inside a database transaction with audit/outbox events created atomically.

- Submitted versions cannot be silently overwritten. Amendments create a new version and preserve the old submitted snapshot.

- Renewal/replacement links old and new instruments; historical values and approvals remain queryable.

- A state of ACTIVE requires approved evidence checks appropriate to the instrument type; the rules are policy-driven.

- A state of RELEASED/DISCHARGED requires approved decision plus verified execution/settlement evidence as defined by AICTE—not just approval or maturity date.

- A rejected/inconclusive bank response is not automatically labelled fraud. It creates an exception/review state with documented evidence.

- Policy/rules are evaluated using a version pinned to the case or decision; new policy versions must not silently rewrite past decisions.

## 6.3 Casework and discrepancy model

An observation is a first-class casework record, not a text field on an instrument. Minimum fields: type, severity, affected field(s), compared source IDs, explanation, owner, due date, lifecycle/status, institution response, evidence added, resolution code, reviewer, timestamps and policy reference. Support re-open with a reason; do not delete an observation after resolution.

# 7. Data model: implementation-level design

## 7.1 Recommended tables and purpose

| **Table / aggregate**                               | **Required content and constraints**                                                                                                                                                                       |
|-----------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| institutions                                        | AICTE-authoritative identifier, legal name, institution state, region, source system ID, verified status, timestamps and effective-dated source attributes. Unique authoritative IDs; no fuzzy auto-merge. |
| institution_programmes                              | Institution, programme/level, approval status, effective dates, land/building factor where policy applies, policy applicability result and source citation.                                                |
| users                                               | Identity-provider subject (unique), status, preferred language, MFA/assurance metadata and identity-link timestamps. Do not store passwords when the IdP owns credentials.                                 |
| role_assignments                                    | User, role, institution/region/queue scope, validity range, approved-by, grant reason, ticket/reference and revocation metadata. Never allow users to edit this table through generic profile update.      |
| instruments                                         | Internal UUID/public ID, institution/programme link, type, lifecycle state, policy version, owner, current version ID, issue/maturity/validity dates and instrument status.                                |
| instrument_versions                                 | Version number, normalised field snapshot, submitter, submitted_at, change reason and content hash. Unique instrument_id + version_number.                                                                 |
| instrument_fields / evidence_values                 | Field key, declared/extracted/confirmed/reconciled value, source/evidence ID, confidence, reviewer, status, timestamp and prior version. Model provenance; do not overwrite source values.                 |
| documents                                           | Document ID, object key, checksum, size, content type detected, malware/sanitisation statuses, category, upload identity, version, retention class, accepted/quarantined state.                            |
| document_access_events                              | Who generated/downloaded a signed URL, target document, reason, timestamp, IP/device summary per approved logging policy.                                                                                  |
| evidence_items                                      | Evidence type, issuer/source, instrument/version, signed/source reference, captured/received/validated dates, fields supported, decision, reviewer and evidence hash.                                      |
| verification_requests                               | Institution/instrument, requested confirmation fields, destination/channel, approved template/version, tracking number, sent/received time and status.                                                     |
| bank_responses                                      | Bank/source, authenticated responder or file provenance, confirmed fields, response signature/reference, attachment, reviewer and accepted/rejected/inconclusive outcome.                                  |
| statement_batches / statement_lines                 | Source account identifier (masked), source file/API batch ID, checksum, statement date range, totals, line references and immutable imported values. Unique batch checksum/source ID.                      |
| reconciliation_runs / matches / exceptions          | Rule-set version, run totals, deterministic match candidates, confidence/matching reasons, exceptions, reviewer and final resolution. Fuzzy match remains a candidate until approved.                      |
| observations                                        | Instrument/version, affected field/source comparison, category, severity, opened_by, owner, due date, response and resolution state, reviewer, timestamps.                                                 |
| state_transitions                                   | Entity ID, from/to state, actor, reason, related evidence, policy version, request ID and event timestamp. Append only for normal app roles.                                                               |
| renewal_links                                       | Old instrument, new instrument, relationship/replacement type, overlap/gap dates, review result and approving actor. Constraints prevent cycles/orphan replacement.                                        |
| release_requests / release_checklist_items          | Requester, instrument, reason, policy version, criterion IDs/results, evidence links, recommended outcome, return/decision reasons and execution reference.                                                |
| policy_versions / policy_rules                      | Official source URL/ID, document hash, clause, scope, effective_start/end, config payload, status (draft/review/approved/retired), approver and changelog.                                                 |
| notification_events / user_notifications / attempts | Domain event, dedupe key, recipient, channel, template version, locale, provider response, attempt number, failure category, read/ack/action times.                                                        |
| device_installations                                | User, platform, provider, token/FID or subscription encrypted at rest, created/last-seen/last-registered timestamps, app version and revocation.                                                           |
| audit_events / audit_checkpoints                    | Actor, action, resource, safe before/after diff, reason, timestamp, correlation ID, source, prior/current hash and signed checkpoint metadata.                                                             |
| integration_runs                                    | Connector name/version, environment, external correlation ID, start/end, source checksum, counts, result, error category, retry count and service owner.                                                   |
| export_jobs                                         | Requester, filter/scope, reason, row count, format, file hash, storage key, expiry, download audit and cleanup status.                                                                                     |
| retention_holds / deletion_jobs                     | Record class, legal hold, policy basis, scheduled disposal, approving authority, deletion proof and exception.                                                                                             |

## 7.2 Data integrity rules

- Use NUMERIC/DECIMAL for amounts, never binary floating point. Store currency explicitly even if INR is the only initial currency.

- Use DATE for maturity/issue dates and UTC timestamptz for events. Deadline interpretation needs a documented business timezone (likely Asia/Kolkata) and approved holiday/weekend rules.

- Use foreign keys, check constraints, uniqueness and transactions. Public IDs are non-guessable but must never substitute for authorisation.

- Use optimistic concurrency (version/ETag) on edits and conflict responses when the client submits stale state.

- Use idempotency keys for state-changing endpoints and imports. Retry-safe endpoints must return the same logical outcome for the same key.

- Store raw uploaded source, extracted text, normalised fields and reviewer corrections separately. Preserve the original evidence hash.

- Use explicit transition enums and policy/rule version references instead of free-form statuses or code-only policy rules.

- Use migration scripts with precondition/rollback strategy; test them on a copy of representative schema/data volume before production.

## 7.3 Source-of-truth fields

For every important fact, the data model should answer: What value does the system currently use? Who/what asserted it? When was it asserted? Which evidence supports it? Who reviewed it? What is its evidence type? Is there conflicting evidence? Which source and policy version were used for the decision? A current “verified” status without these answers is not audit-ready.

# 8. Document security and verification controls

## 8.1 Upload pipeline

> 1\. Authenticate user and check access to the instrument/document category before issuing an upload intent.
>
> 2\. Issue a short-lived upload URL limited to one object key, expected max size and quarantined bucket/prefix. The client cannot choose a trusted destination.
>
> 3\. Check actual file signature/magic bytes, declared MIME, extension, size, page count and archive/decompression risk. Reject unsupported/encrypted files unless an authorised process is defined.
>
> 4\. Scan with malware tooling and sanitise risky PDF features/embedded content. The accepted-document path remains blocked until all required pipeline checks pass.
>
> 5\. Compute SHA-256 integrity hash; optionally compute perceptual hashes for duplicate detection. Similarity is a flag, not a fraud verdict.
>
> 6\. Create the document record and keep quarantine/scan outcome. Move/copy to protected storage only after successful validation; capture every pipeline step.
>
> 7\. Run OCR on a safe, preferably rasterised representation. Record engine/model/version, page/region, candidate value, confidence and extraction timestamp.
>
> 8\. Present a side-by-side review UI so a permitted person can confirm/correct values; store the change, reviewer, reason and field provenance.
>
> 9\. Issue download access only through authenticated API checks and short-lived signed URLs; redact or watermark as required by policy. Log sensitive downloads and exports.

## 8.2 OCR/anomaly scope and boundaries

| **Check**                    | **Value**                                                                                               | **Limit / action**                                                                                    |
|------------------------------|---------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| Field extraction             | Reduces manual transcription of bank name, FDR number, amount, dates, holder and other approved fields. | Human confirmation for material fields; measure field-level accuracy by scan quality/type.            |
| Tenor/date consistency       | Flag impossible or inconsistent issue/maturity date relationships.                                      | The expected tenor must come from the applicable instrument and policy; exceptions may be legitimate. |
| Duplicate number/image       | Find exact or near-duplicate instrument numbers, hashes or images.                                      | Duplicate may be legitimate across versions or a bad OCR result; route to reviewer.                   |
| Metadata/layout irregularity | Point out suspicious inconsistencies for a trained reviewer.                                            | Metadata can be absent or altered; no single signal proves tampering.                                 |
| Expected amount comparison   | Compare against a versioned policy calculation.                                                         | Policy inputs/exemptions must be approved; conflict blocks automated “compliant” result.              |
| Bank / ledger match          | Match against authoritative source data.                                                                | This is the only path to a ledger match; OCR cannot substitute for the bank/ledger source.            |

## 8.3 Reconciliation must be deterministic and reviewable

For online deposits, use approved statement data with source and integrity provenance. Matching candidates may use exact reference/UTR, amount, currency, date window, remitter and destination account. Store the ruleset version and a human-readable match explanation. Use exact deterministic rules for automatic candidate identification; fuzzy narrative matching must go to an exception queue unless AICTE approves and validates a narrow auto-match policy with measured false-match risk. Duplicate statement batches and duplicate rows must be idempotently rejected or reconciled.

# 9. Maturity, renewal, reminder and escalation engine

## 9.1 Server-authoritative deadline logic

- All deadline calculations originate from backend/policy configuration and a server-side clock synchronised to an approved time source. CERT-In Directions specify NTP synchronisation to NIC/NPL or a traceable source for covered entities. \[R4\]

- Store the relevant business deadline date separately from event timestamps. Apply timezone and date arithmetic consistently. Only use holidays, weekend adjustments, grace periods and escalation periods when formally specified.

- Reminder windows are config, not literals in business code. The prior report’s T-90/T-60/T-30/T-7/T-0 are examples only; AICTE must choose official windows.

- Each scheduled reminder needs an idempotency key, e.g. instrument + event type + target date + schedule version + recipient. Re-running a scheduler should not duplicate the same business reminder.

- Scheduler/worker failure is observable: missed run, backlog age, retry count and dead-letter count are metrics and alerts.

- Overdue escalation may reassign or expose a case to a supervisor. It must not itself reject, forfeit or release the deposit.

## 9.2 Lifecycle notifications to support

| **Domain event**                                  | **Primary recipient (proposal)**                  | **Expected in-app action**                                                |
|---------------------------------------------------|---------------------------------------------------|---------------------------------------------------------------------------|
| Submission received                               | Institution submitter + assigned intake queue     | Open receipt and case timeline.                                           |
| Missing/incorrect evidence observation raised     | Institution submitter; assigned case officer      | View the reason and due date; submit corrected evidence.                  |
| Institution response submitted                    | Assigned scrutiny officer                         | Review the new version and response.                                      |
| Verification result accepted / inconclusive       | Institution contact as policy permits; case owner | Open evidence outcome; provide next action if required.                   |
| Maturity horizon reached                          | Institution contact and assigned workflow owner   | View instrument/date and renewal/release obligations.                     |
| Renewal/replacement pending or accepted           | Institution submitter + verifier/scrutiny queue   | Open linked old/new instrument and continuity checklist.                  |
| Release returned / approved / rejected / deferred | Requestor and assigned authorised officers        | View decision, reason, checklist and next steps.                          |
| Reconciliation exception                          | Authorised finance/verifier queue                 | Review matching candidates and resolve with evidence.                     |
| Role/device/session change                        | Affected user and security admin as appropriate   | Review session/security event, revoke session or contact support.         |
| Provider/connector failure                        | Operations/connector owner                        | Open health alert/runbook; no false institution-facing success.           |
| Policy/configuration approved or superseded       | Policy admins/officers as appropriate             | View change and effective date; historical case decisions stay versioned. |

# 10. Shared web + native mobile implementation

## 10.1 Avoid two competing applications

Web and mobile should share the domain model, OpenAPI schema, generated TypeScript API client, validation rules, i18n message catalogue, permission identifiers, error model and design tokens. The backend is the sole place where policy, access and state-transition rules are enforced. Web can provide denser tables and broad exports; mobile can provide compact workflows, camera/document picker, upload progress, push and quick case review. If AICTE policy requires a desktop for certain approvals, the same API can deny that action from mobile without creating a separate ruleset.

| **Capability**            | **Web**                                                                                             | **Native mobile**                                                                                                                                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Authentication & account  | Full OIDC, MFA, recovery/session/device management.                                                 | Same identity provider; OIDC PKCE; local biometric unlock only after server authentication. Never use biometrics as proof of role or remote authorisation. |
| Instrument list/detail    | Advanced search, sortable queues, evidence comparison, multi-column tables.                         | Responsive searchable lists, filters, compact status/provenance summary, full detail on tap.                                                               |
| Submission                | Complete draft/edit/submit workflow.                                                                | Same permissions and validation; camera/document picker and resilient upload.                                                                              |
| Review and observation    | Full side-by-side evidence and complex review tools.                                                | Same backend actions; if a decision requires desktop, server policy denies mobile action and explains why.                                                 |
| Approval                  | Full checklist, decision reason and step-up MFA.                                                    | Only if approved policy permits; strong re-auth, confirmation screen and audit reason still required.                                                      |
| Notifications             | In-app inbox and web push where supported; email preferences.                                       | Native push, in-app inbox, badge counts, deep links to authorised record.                                                                                  |
| Offline                   | No offline consequential writes. Cache only public/static shell or expressly approved minimal data. | Optional minimal encrypted read cache with expiry; no approvals, reconciliations or financial transitions offline.                                         |
| Accessibility / languages | Keyboard, screen reader, contrast, zoom, semantic structure.                                        | TalkBack/VoiceOver, dynamic text, touch targets, focus and OS notification settings.                                                                       |

## 10.2 Recommended technology choices (not official mandates)

| **Layer**       | **Preferred initial choice**                                                                          | **Decision notes**                                                                                                                                                                                |
|-----------------|-------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Web             | React + TypeScript + Vite; accessible component system; TanStack Query/Router or equivalent.          | Use a locked dependency graph, semantic controls, Content Security Policy, error boundaries and supported browser matrix.                                                                         |
| Mobile          | React Native + TypeScript (Expo development build/prebuild or native build as needed).                | Must support real APNs/FCM setup, signed release artifacts, secure store, deep links, permission handling and store account ownership. PWA alone should not be assumed equivalent to native push. |
| Shared packages | OpenAPI-generated client, TypeScript schemas/validation, i18n catalogue, design tokens.               | Generated from a versioned API spec; CI checks generated client is current.                                                                                                                       |
| Backend         | FastAPI + Pydantic + SQLAlchemy/Alembic or one equivalent framework chosen by the team.               | Choose and pin supported versions; one modular monolith before microservices.                                                                                                                     |
| Database        | PostgreSQL supported major version; managed/HA option according to approved hosting.                  | Transactions, integrity constraints, RLS where suitable, backup/PITR and tested migrations.                                                                                                       |
| Documents       | Encrypted S3-compatible object store or approved equivalent.                                          | Private by default; versioned objects; short-lived downloads; retention and keys governed.                                                                                                        |
| Identity        | AICTE-approved OIDC provider. Keycloak is an option if self-management is accepted.                   | Do not bake one identity provider’s proprietary claims into business logic.                                                                                                                       |
| Jobs            | Transactional outbox + durable worker/queue; DB-backed scheduler acceptable at small scale.           | Celery/Valkey is a viable option but not inherently mandatory; operate retry and dead-letter handling.                                                                                            |
| Notification    | FCM for Android; APNs or FCM routing to APNs for iOS; Web Push for browser; configured email service. | One notification domain model, channel adapters and observable failure/retry states.                                                                                                              |
| Operations      | Central logs, metrics, tracing, error reporting and uptime alerts under approved governance.          | Do not send raw FDR documents, tokens or unnecessary personal/financial data to external telemetry.                                                                                               |

## 10.3 Mobile-specific security

- Android 13+ requires runtime notification permission before app notifications can appear. If the user denies it, keep portal/in-app inbox usable and show a settings explanation. \[R11\]

- Device-token registration is tied to a signed-in user and app installation, refreshed when the provider rotates the token and revoked/retired on logout, account disablement or invalid-token responses. Firebase recommends refreshing registrations and removing stale/invalid tokens. \[R12\]

- Use operating-system secure storage for refresh credentials; do not store secrets in plain AsyncStorage. Clear protected caches on logout, revocation and role downgrade.

- Notification/deep-link IDs are untrusted input. The app authenticates and fetches the entity through normal API access checks before showing protected detail.

- Lock-screen content is minimal by default. Do not include FDR number, full amount, bank account, legal details or document previews unless a deliberate, user-controlled and policy-approved design says otherwise.

- No offline approval or sensitive state transition. Queuing a write offline can become unsafe when roles, policy, case state or delegated authority changes before reconnection.

- Test real supported Android OEMs and iOS devices; power-saving modes and user settings can affect display/delivery.

# 11. Real push notification design and limits

## 11.1 Correct definition of “instant notification”

| **Engineering target: create the notification event immediately after the business transaction commits and enqueue dispatch without a human operator. Do not promise that the operating system will display it instantly: network, permissions, device power, platform queues and user settings can delay or suppress display.** |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

Apple documents delivery via a provider server, APNs and the user device, and notes delivery can be delayed/coalesced due to device/network/power conditions. FCM similarly exposes message outcomes and dropped/delayed conditions; an accepted send is not the same thing as proof a person saw the notification. \[R12–R13\]

## 11.2 Event pipeline (must be reliable)

> 1\. A business transaction updates the instrument/case and inserts a domain event into a transactional outbox in the same database transaction. If either fails, neither is committed.
>
> 2\. A worker claims the outbox event, uses idempotency/deduplication, and resolves recipient candidates from the current approved role/scope/assignment records.
>
> 3\. The notification service persists one in-app inbox item per user/event/category before attempting external delivery.
>
> 4\. A localised, versioned template creates a minimal payload. Server-owned amounts/dates/statuses are substituted from authorised data; no model-generated financial facts.
>
> 5\. The channel adapter sends through a real configured provider (FCM/APNs/Web Push/email) and stores the provider response, message ID, attempt and error category.
>
> 6\. Retries use backoff/jitter for transient errors; permanent token/configuration errors retire the registration or raise an operations alert. Exhausted events enter a monitored dead-letter queue.
>
> 7\. Opening a deep link causes normal authentication and resource authorisation. Read/acknowledge/action is recorded server-side; a push notification itself does not change financial state.
>
> 8\. Monitor enqueue latency, dispatch latency, provider accept/fail counts, invalid registrations, backlog age, dead letters, and read/acknowledgement separately.

## 11.3 Notification state model

| **Status**                        | **Meaning**                                                    | **What can safely be claimed**                                           |
|-----------------------------------|----------------------------------------------------------------|--------------------------------------------------------------------------|
| CREATED                           | Notification event committed and in-app item persisted.        | The system recorded the event.                                           |
| QUEUED                            | Dispatch work is ready.                                        | The system plans to attempt sending.                                     |
| PROVIDER_ACCEPTED                 | Provider accepted send request / valid response received.      | Attempt accepted by provider—not that a device displayed it.             |
| PROVIDER_FAILED                   | Provider rejected or send failed.                              | Failure category and retryability known/being handled.                   |
| DEVICE_RECEIVED (when observable) | A supported SDK/provider reports receipt.                      | The message reached the app/SDK if the platform gives that signal.       |
| OPENED                            | User opened the app/deep link from notification or inbox item. | Open event was recorded; not necessarily read in full.                   |
| ACKNOWLEDGED                      | User explicitly acknowledged a reminder/action.                | Acknowledgement was recorded by the server.                              |
| ACTIONED                          | Authorised state-changing API action completed.                | Only when that API transaction succeeded.                                |
| EXPIRED / DEAD-LETTER             | No further send retry or retention window ended.               | Requires visible in-app status and/or operations review based on policy. |

## 11.4 Channels and what each actually provides

| **Channel**     | **Real prerequisites**                                                                                            | **Limitations to communicate**                                                                                          |
|-----------------|-------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Android push    | Firebase project, correct app ID, server-to-FCM credentials, device registration and runtime permission.          | Permission can be denied; stale token, OEM battery settings, offline state and provider throttling can affect delivery. |
| iOS native push | Apple developer configuration, APNs key/certificate, bundle ID/signing, server integration and real-device tests. | OS/user settings, device/power/connectivity, APNs acceptance versus delivered/displayed are distinct.                   |
| Web push        | HTTPS, supported browser, service worker, user permission, VAPID keys and subscription management. \[R14\]        | Browser/platform support and permission differ; not a substitute for native support in every environment.               |
| In-app inbox    | Database-backed notification rows and authenticated polling/realtime refresh.                                     | Works after user opens app; it must be the persistent source for missed push events.                                    |
| Email fallback  | Verified sending domain, SPF/DKIM/DMARC, production provider, bounces/complaints handling and approval.           | Email can be delayed, filtered or fail; do not include sensitive details unnecessarily.                                 |
| SMS / WhatsApp  | Institutional approval, provider procurement, sender/template registration and policy/legal review.               | Disabled until provisioned; do not use stub adapters in production or label queued messages sent.                       |

## 11.5 Notification preferences and urgency

- Classify events as critical workflow, deadline, security/account, operations or digest. Recipient mapping is configured and signed off.

- Preferences may control optional reminders/digests, language and quiet hours. Statutory/business-critical notices must follow official policy and alternate delivery requirements; personal preference must not silently cancel an obligation.

- Support escalation to a supervisor queue when a critical case remains unacknowledged, but keep the case status independent of notification delivery.

- Provide an explicit status page in user profile: device registered/not registered, permission unknown/denied where the app can report it, last registration time, and channel configuration.

- Use localization templates with verified translations; keep the payload template key and version so audit reports can reproduce what was sent.

## 11.6 Suggested notification schema

> notification_events(
>
> id UUID PK, type, entity_type, entity_id, event_version,
>
> occurred_at_utc, minimal_payload_json, dedupe_key UNIQUE, created_at
>
> )
>
> user_notifications(
>
> id UUID PK, event_id FK, recipient_user_id FK, category, channel,
>
> template_key, template_version, locale, status,
>
> created_at, read_at, acknowledged_at, actioned_at
>
> )
>
> notification_attempts(
>
> id UUID PK, user_notification_id FK, provider, provider_message_id,
>
> attempt_number, attempted_at, result_code, error_category, next_retry_at
>
> )
>
> device_installations(
>
> id UUID PK, user_id FK, platform, provider, protected_token_reference,
>
> created_at, last_registered_at, last_seen_at, app_version, revoked_at
>
> )
>
> notification_preferences(
>
> user_id FK, category, channel, enabled, locale, quiet_hours, updated_at
>
> )

# 12. External integrations: “real” means more than an adapter

A production integration is only real when a named source owner, formal permission, endpoint/file-transfer route, data contract, credentials/certificates, sandbox and production setup, audit trail, error handling, monitoring and end-to-end acceptance tests exist. Search did not identify a documented, universal public FDR-verification API. That should be phrased as “not identified in reviewed public sources,” not as proof that no private or bilateral facility exists.

| **Integration**                       | **Production-entry criteria**                                                                                                                 | **Until entry criteria are met**                                                                      |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| AICTE institution/approval data       | Official data owner, schema/identifier mapping, update semantics, access agreement and reconciliation plan.                                   | Use authorised, provenance-tagged manual onboarding/import where allowed; do not advertise live sync. |
| AICTE bank statement / online deposit | Authorised bank data feed/API or approved bank-origin file process; account/source validation; cut-off and reversal handling.                 | Queue evidence and show pending reconciliation; no simulated matched status.                          |
| Legacy FDR bank confirmation          | Approved request channel, bank identity assurance, format/signature requirements, evidence fields, turnaround ownership and reviewer process. | Track request as awaiting response; store signed/file evidence only after receipt.                    |
| BG / SFMS / NeSL / e-BG               | Written AICTE/bank eligibility, product endpoint, credentials, security review and certified integration tests.                               | Feature unavailable. Do not assume such a protocol covers legacy FDRs.                                |
| Government identity / Parichay        | Formal registration, relying-party setup, claim contract, redirect/metadata and support escalation.                                           | Use an approved, controlled identity arrangement; no fake government SSO.                             |
| FCM/APNs/Web Push                     | Real production app identifiers, service credentials, token enrolment and real-device/production endpoint tests.                              | In-app inbox works; show external push as not configured.                                             |
| Email                                 | Verified production sender, domain records, privacy/vendor review, suppression/bounce handling and alert monitoring.                          | Persist in-app messages; mark email channel unconfigured.                                             |
| DigiLocker/eSign/API Setu             | Formal agency onboarding, permitted use case, scopes, credential setup, audit, consent/notices and acceptance test.                           | Do not create a fake signed certificate or claim official document retrieval.                         |
| Financial execution/refund system     | Authorised transaction system/API, maker-checker, transaction reference, reversals and reconciliation semantics.                              | Record approval but remain EXECUTION_PENDING until authentic execution evidence is available.         |

## 12.1 Connector interface design

Every connector should implement a common operational contract: health/status, configuration validation, credential expiry, source identity, data schema version, request correlation ID, idempotency, retry policy, rate limits, timeout, circuit-breaker state, normalised error categories, audit event and reconciliation. Store no plaintext credential in source control, client code, database audit or logs. Build each connector behind a feature flag with environment-specific credentials and explicit production-enable approval.

## 12.2 Bank import and statement controls

- Validate the file schema and account/source identity before import; compute checksum and keep original source under restricted retention.

- Check statement period, opening/closing balance/totals where source provides them, duplicate batch and row reference, sequence/coverage gaps and currency.

- Never silently drop malformed rows. Produce import totals and exception report (received, parsed, rejected, duplicate, matched, unmatched, ambiguous).

- Exact match candidates must expose which attributes matched. If date tolerance or amount tolerance exists, it must be policy-controlled and approved.

- Corrections to imported transaction data must be represented as adjustments/reconciliation decisions; raw source rows remain intact.

- Handle reversals, returned payments, amended statements and late-arriving lines with explicit compensating events rather than rewriting the original match history.

# 13. Production data: zero demo records and no fake success

## 13.1 Environment segregation

| **Environment**      | **Data and allowed services**                                                    | **Controls**                                                                                                                                      |
|----------------------|----------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| Local developer      | Synthetic fixture data only; fake provider adapters allowed for automated tests. | Local secrets; no production account/credentials; seeded fixture labels cannot be mistaken for real institution records.                          |
| CI / automated tests | Generated fixtures, test database, provider stubs and security test payloads.    | Isolated network/secrets, deterministic tests and no access to production storage/identity/project.                                               |
| Staging/UAT          | Synthetic or formally anonymised data; approved sandbox connectors.              | Separate identity realm, DB/storage, keys, email sender, app IDs and push endpoints; recipients are internal test users.                          |
| Production           | Authorised real records and real provider results only.                          | No seeding, test identities, simulation clock, fake bank confirmations or provider-stub success. Deploy guardrail plus runtime config validation. |

## 13.2 Technical guardrails

- Production build must omit fixture/seeder modules or fail CI if test seed code is bundled in production artifacts.

- API startup refuses configuration containing DEMO_MODE, MOCK_BANK_PROVIDER, SIMULATED_CLOCK, FAKE_PUSH_SUCCESS or any equivalent setting.

- Production deployment uses distinct databases, object stores/buckets, identity realm, app IDs, service accounts and keys; staging credentials cannot touch production.

- Use a feature registry with status: disabled, sandbox-only, production-enabled, degraded. Only designated release owners may enable a connector after acceptance tests.

- Any external verification result stores source, query/reference, received time, response hash or signed evidence and reviewer; lack of response is not success.

- Production UI must distinguish “not configured,” “temporarily unavailable,” “pending source response,” “provider accepted,” “evidence received,” and “human verified.”

- Backfill/import of real historical data requires an approved migration plan, reconciliation totals, row counts, sampled case review, discrepancy queue and sign-off before cutover.

## 13.3 Migration and cutover plan

> 1\. Inventory every existing spreadsheet/database/folder, its owner, date range, fields, provenance and data-quality limitations.
>
> 2\. Map each source column into a canonical data dictionary; preserve original IDs and source row/file references.
>
> 3\. Profile duplicates, missing dates, inconsistent amounts, conflicting institutional names and missing documents. Never auto-resolve material conflicts silently.
>
> 4\. Build a dry-run migration report with counts by source/type/status and totals for amount/date groupings where meaningful.
>
> 5\. Migrate to staging first, perform reconciliation totals and human sampling, then obtain business/finance/security sign-off.
>
> 6\. At cutover, freeze or track source changes, run final delta import, confirm counts/checksums, lock legacy source per approved process and preserve an archive.
>
> 7\. Post-cutover, reconcile exceptions under case management; maintain an explicit rollback/correction route without duplicating or losing decisions.

## 13.4 Historical-data migration: additional financial controls

- Import each legacy source as an immutable batch. Store the original file, checksum, received-by/received-at, source owner, source date range and parser/mapping version.

- Produce signed reconciliation reports for row counts, counts by instrument class/status, distinct institution IDs, document counts, amount totals where comparable, duplicates, missing critical fields and unmatched records.

- Do not use a migration script to “correct” a financial amount, maturity date, instrument number or legal institution identity without an approved source-backed correction record.

- Preserve source-native IDs, original wording and historical document links. A transformed canonical record must link to the exact source row/document and any human mapping decision.

- Use a two-person cutover sign-off from the data owner and finance/business owner. Any variance must be accepted explicitly or remain a blocking exception—not hidden in an aggregate.

- After go-live, mark imported legacy records with evidence source and verification state. Migration into the new database does not independently verify the underlying FDR/deposit.

# 14. Security, privacy and government quality requirements

## 14.1 GIGW and STQC distinction

The official GIGW site states its scope includes government websites/apps and references WCAG 2.1; GIGW 3.0 emphasizes accessibility and cybersecurity. STQC’s official Website Quality Certification process describes evaluation, security audit and certificate issuance, with stated validity/surveillance requirements. Therefore, build toward GIGW requirements from day one, but do not write “STQC certified” or equate a checklist pass with an official certificate. The certification process is separate. \[R2–R3\]

## 14.2 OWASP verification baseline

- Use OWASP ASVS 5.0.0 as a versioned web/API security verification checklist and explicitly select a target appropriate to sensitive financial/regulatory workflows. ASVS is intended to provide verifiable technical security requirements. \[R5\]

- Use OWASP API Security Top 10 2023 to prioritise object-level/function-level authorisation, authentication, property-level exposure/mass assignment, unrestricted resource consumption and unsafe external API risks. \[R6\]

- Use OWASP MASVS and its testing guide for mobile storage, cryptography, authentication, network, platform, code, resilience and privacy. \[R7\]

- Record the exact standard version and control references in a security traceability matrix. Do not claim “OWASP compliant” based only on running a scanner.

## 14.3 Security control baseline

| **Area**          | **Minimum control / evidence**                                                                                                                                          |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Authentication    | OIDC/OAuth-compatible flow, MFA for privileged accounts, secure recovery, PKCE on mobile, session revocation, rate limits and step-up re-auth for high-risk decisions.  |
| Authorization     | RBAC+ABAC, default deny, server-side resource and field checks, separation of duties, access recertification and automated negative tests.                              |
| Transport/storage | TLS, HSTS, secure headers, encryption at rest, key separation/rotation, private object storage and short-lived signed URLs.                                             |
| Database          | Least-privilege roles, no app superuser, migrations under controlled role, RLS where appropriate, backup/PITR, secrets outside source control and audited admin access. |
| File pipeline     | Quarantine, magic-byte verification, malware scan, sanitisation, hash integrity, archive/zip-bomb controls, OCR isolation and controlled downloads.                     |
| API               | Input/output schemas, object-level authorisation, idempotency, bounded pagination/search/export, timeouts, CORS allow-list, safe errors and request correlation.        |
| AppSec delivery   | Peer review, SAST, dependency audit, secrets scan, SBOM, signed artifacts, container scan, DAST/VAPT, risk acceptance and patch SLAs.                                   |
| Mobile            | OS secure storage, minimal cache, deep-link validation, permission handling, app signing, privacy-safe push, logout/revocation and update policy.                       |
| Audit             | Append-only application interface, restricted DB rights, secure central retention, time sync, signed checkpoints and access-event monitoring.                           |
| Operations        | Monitoring, incident roles, patching, recovery testing, capacity alerts, provider-outage handling and runbooks.                                                         |
| AI/OCR            | Redaction and approved providers, prompt-injection defence, bounded tools, model versioning, evaluation, human review and graceful fail-closed behaviour.               |

## 14.4 CERT-In logging and incident workflow

CERT-In Directions dated 28 April 2022 state that covered service providers, intermediaries, data centres, body corporates and government organisations must synchronise ICT system clocks to NIC/NPL or a traceable source; report specified cyber incidents within six hours of noticing them or being brought to notice; designate a point of contact; and securely maintain ICT logs for a rolling 180 days within Indian jurisdiction. The security/legal owner must confirm applicability and the current reporting procedures for AICTE and every relevant operator; do not infer that every vendor has identical obligations. \[R4\]

## 14.5 DPDP legal posture

The DPDP Act, 2023 and Rules, 2025 are official sources, but their provisions do not all commence at once. MeitY’s commencement notification G.S.R. 843(E) and the Rules notification G.S.R. 846(E) specify staggered phases. The official portal lists the Act/Rules publication as 14 November 2025, while the Gazette notifications are dated 13 November 2025; counsel should confirm the legally controlling Gazette publication date and any corrigendum before calculating deadlines. \[R9, R16–R17\]

| **Officially stated group (summary only)**                                                                                         | **Scheduled timing relative to publication**                                                       | **Engineering / legal action**                                                                                                  |
|------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| Act sections 2, 18–26, 35, 38–43 and section 44(1),(3) under G.S.R. 843(E)                                                         | On publication of the commencement notification (November 2025 according to the official listing). | Apply requirements already in force; counsel confirms the exact provision-level applicability and organisational role.          |
| Act section 6(9) and section 27(1)(d)                                                                                              | One year after publication; approximately mid-November 2026.                                       | As of report date 23 October 2026, this one-year phase is imminent. Re-check the exact effective date; implement readiness now. |
| Act sections 3–5, section 6(1)–(8) and (10), sections 7–17, section 27 except clause (d), sections 28–34, 36, 37 and section 44(2) | Eighteen months after publication; approximately mid-May 2027.                                     | Plan for this phase in design and contracts now; counsel must map each data process to the exact provision and date.            |
| Rules 1, 2 and 17–21 under G.S.R. 846(E)                                                                                           | On publication of the Rules (November 2025 according to the official listing).                     | Verify the exact duties and responsible entity with counsel; do not treat this as whole-Rules commencement.                     |
| Rule 4                                                                                                                             | One year after publication; approximately mid-November 2026.                                       | Near-term legal checkpoint; determine applicability and required controls with counsel.                                         |
| Rules 3, 5–16, 22 and 23                                                                                                           | Eighteen months after publication; approximately mid-May 2027.                                     | Prepare notices, operational workflows and evidence now; apply each rule on its legally confirmed date.                         |

This table is a planning aid summarising the notifications, not a legal opinion. The system should be privacy-engineered now even where a provision has a future commencement date. Do not claim full DPDP compliance because the application has a consent checkbox or because the Rules are published. AICTE counsel must determine Data Fiduciary/Data Processor roles, lawful processing grounds, notices, retention, rights/grievance process, processor terms, security safeguards and breach duties provision by provision. \[R8–R9, R16–R17\]

## 14.6 Privacy engineering requirements

- Maintain a data inventory for user identities, institution contacts, uploaded documents, bank transaction details, access history, device IDs, support records and analytics.

- Document purpose, access roles, retention, residency, sharing and lawful basis for every personal-data category. Notification permission is separate from the legal basis to process the case data.

- Keep sensitive values out of application logs, crash reports, analytics and push previews. Mask full FDR/bank identifiers where business display does not require them.

- Review third-party hosting, push, OCR, email and AI vendors for contract, subprocessor, retention, access, region, breach notice, delete/export and exit terms.

- Create authorised workflows for correction, grievance/rights requests, retention expiry, legal hold and deletion where permitted. Financial records may need retention; do not promise unconditional deletion.

- Use only approved AI/OCR processing for real records. If provider data terms, location or retention are unclear, process locally or do not send sensitive data.

## 14.7 Audit logs are tamper-evident—not magically immutable

A hash chain alone does not make a log immutable if a privileged administrator can rewrite the entire chain. Recommended controls are: append-only application permissions, separate security-log access controls, central forwarding to a restricted log store, reliable time sync, independent access review, periodic signed checkpoint/head hashes, alerting on sequence gaps and protected backup/retention. State the assurance accurately: tamper-evident with controls; formally immutable only if the selected storage/control actually enforces immutability.

# 15. Deployment, operations and business continuity

## 15.1 Hosting decision

Production hosting must be selected by AICTE’s IT/security/procurement owners. MeitY’s GI Cloud/MeghRaj documents describe the government cloud initiative, but the project must still confirm the currently approved hosting route, service catalogue, contracts, security policy, required region, network path, availability and support. A free personal VM or free-tier SaaS should be treated as development/testing unless formally accepted for the real risk classification. \[R10\]

## 15.2 Environment model

- Dev: fast local iteration, generated fixture data, local/stub adapters only.

- CI: reproducible tests, ephemeral DB/services, test credentials and generated fixture set; never access real production records.

- Staging/UAT: isolated identity realm, DB, storage, domain, email/push projects and approved sandbox integrations; internal recipients only.

- Production: approved cloud/project, real identities, live policy versions and only integrations with production credentials and acceptance evidence.

- Disaster-recovery environment: access-restricted, separately protected keys and backups, regular restore drills; access is not used as an informal staging environment.

## 15.3 Deploy pipeline

> Pull request -\> lint/typecheck/unit tests -\> DB migration tests -\> authorization tests
>
> -\> SAST/dependency/secrets/container scans -\> integration/E2E tests -\> build SBOM
>
> -\> sign artifacts -\> deploy staging -\> smoke + migration verification + security checks
>
> -\> release approval -\> staged production rollout -\> post-deploy smoke/metrics
>
> -\> rollback or fix-forward decision with audit record

## 15.4 Backup/DR requirements

- AICTE must approve RPO/RTO. Values such as 24-hour RPO or four-hour RTO are planning candidates, not official targets unless accepted in writing.

- Cover database, documents and object metadata, policy versions, identity config, integration metadata, audit logs, deployment configuration and the encryption-key recovery procedure.

- Use encrypted backups and separately controlled access. Avoid a backup target sharing the same credentials and failure domain as production.

- Run restore exercises at an approved cadence; measure achieved recovery point/time and reconcile document hashes, record counts and audit checkpoints.

- Monitor backup freshness, failed jobs, replica lag, free space, certificate/secret expiry, worker backlog, queue age, database connections, API p95 latency and provider errors.

- Prepare manual continuity procedures for urgent casework during outage. Any off-system decision entered after restoration must have source evidence, approval and an audit trace.

## 15.5 Operational runbooks to write before go-live

- Identity provider outage and privileged account compromise.

- Bank statement import invalidity, duplicate batch and reconciliation backlog.

- Push provider outage, APNs/FCM credentials expiry and invalid device token spikes.

- Maturity scheduler missed run or clock desynchronisation.

- Malware in uploaded file, suspicious document and storage exposure.

- Database restore/failover and object storage recovery.

- Unauthorised release attempt or same-person maker-checker collision.

- Sensitive data exposure, CERT-In escalation and privacy incident assessment.

- Policy rule misconfiguration and rollback of a published policy version.

# 16. API design, errors and contract

## 16.1 API rules

- Expose a versioned REST/OpenAPI contract; generate web/mobile clients from the same schema.

- All private endpoints authenticate and re-check role, scope, state and field-level visibility server-side.

- State-changing operations use idempotency keys and produce audit/outbox events atomically.

- Use cursor pagination, bounded filters, server-side sorting, query timeouts and export size limits.

- Use ETag/version fields for optimistic concurrency; return a conflict response with safe recovery instructions when stale.

- Use consistent problem+json error semantics without SQL, internal stack traces, secrets or protected object existence leaks.

- Rate-limit login, MFA attempts, upload URLs, OCR, search, reconciliation and export; add per-user and per-institution quotas as suitable.

- Every request has correlation/request ID across API, worker, provider attempt and audit event.

## 16.2 Proposed endpoint groups (design names only)

| **Group**       | **Example API contract**                                                                                                                   |
|-----------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Identity        | GET /v1/me; GET /v1/me/permissions; POST /v1/me/devices; DELETE /v1/me/sessions/{sessionId}                                                |
| Institutions    | GET /v1/institutions/{id}; GET /v1/institutions/{id}/programmes; institution-user lifecycle endpoints scoped to institution administrator  |
| Instruments     | POST /v1/instruments; GET /v1/instruments/{id}; PATCH draft only; POST /v1/instruments/{id}/submit; GET timeline/version history           |
| Documents       | POST upload intent; POST upload finalisation; GET authorised download intent; GET extraction result; POST reviewer confirmation/correction |
| Observations    | POST observation; POST response; POST resolve/reopen with required reason and reviewer                                                     |
| Verification    | POST verification request; attach source response; POST evidence acceptance/rejection/inconclusive decision                                |
| Reconciliation  | POST statement batch; POST reconciliation run; GET exceptions; POST exception resolution                                                   |
| Renewal/release | Create renewal link; request release; record recommendation; record authority decision; record execution confirmation                      |
| Notifications   | GET inbox; POST read/acknowledge; PATCH preferences; POST/DELETE device registration                                                       |
| Audit/report    | GET authorised audit events; POST scoped export job; GET export status/download once permission revalidated                                |
| Admin/config    | Role assignment requests, policy draft/approval/supersession, connector config/health, template versioning and audit.                      |

These are illustrative endpoint names to help design the API contract. They are not existing live AICTE endpoints. Keep high-consequence operations explicit (e.g. /decisions) rather than a generic PATCH status field.

## 16.3 Essential error categories

| **HTTP / error family**      | **Meaning**                                                   | **Client behaviour**                                              |
|------------------------------|---------------------------------------------------------------|-------------------------------------------------------------------|
| 401 UNAUTHENTICATED          | Missing/expired/invalid credentials.                          | Re-authenticate; do not retry endlessly.                          |
| 403 FORBIDDEN                | Identity is valid but lacks action/scope authority.           | Show permission guidance; do not expose protected details.        |
| 404 NOT_FOUND                | Resource absent or intentionally hidden for anti-enumeration. | Offer safe navigation/back; do not reveal cross-tenant existence. |
| 409 CONFLICT / STALE_VERSION | Duplicate idempotency/state transition or concurrent change.  | Fetch latest state and ask user to review conflict.               |
| 422 VALIDATION_ERROR         | Input fields/transition requirements failed.                  | Show field-specific correction while preserving draft where safe. |
| 429 RATE_LIMITED             | Rate or quota exceeded.                                       | Show retry window; do not immediately hammer endpoint.            |
| 503 INTEGRATION_UNAVAILABLE  | Trusted connector/provider not available.                     | Persist pending state and retry safely; never display success.    |
| 500 INTERNAL_ERROR           | Unexpected server fault.                                      | Show correlation ID; do not leak internals.                       |

# 17. AI/OCR governance

## 17.1 Allowed initial use cases

- Extract candidate FDR/deposit fields from documents with page/region and confidence provenance.

- Flag duplicate candidates, amount/date inconsistencies or missing evidence for human review.

- Search approved policy documents and give concise answers only with citations to real versions/clauses.

- Summarise the case record using authorised fields and label the output as AI-generated assistance.

## 17.2 Prohibited automated decisions

- No autonomous bank authenticity declaration, evidence promotion, policy waiver, penalty adjudication, forfeiture, release/refund approval or financial execution.

- No LLM as authoritative database, permission checker or workflow state machine.

- No generated numbers, dates, clause references or source identity not obtained from authorised records or retrieved source documents.

- No raw financial documents submitted to cloud AI providers without approved contract, privacy assessment, allowed data classification and minimisation.

- No document extraction agent with broad tools/write access; uploaded text is untrusted data, not instructions.

## 17.3 Evaluation and fail-safe

> 1\. Build a reviewed ground-truth set of representative authorised document types, with variation in scan quality/language/layout.
>
> 2\. Measure field-level precision/recall/accuracy and correction rate by field; record model/engine version.
>
> 3\. Create adversarial tests for hidden text, prompt injection, hallucinated dates/amounts, cross-institution context leakage and stale policy retrieval.
>
> 4\. Run deterministic rules after extraction and show differences against source images. Human review decides whether a candidate value is accepted.
>
> 5\. If OCR/LLM is down, submissions and core workflows continue with manual entry; show the AI feature as unavailable, not as failed verification.
>
> 6\. Keep version, provider, latency and error metrics; redact personal/financial data from traces.

# 18. Testing matrix and release gates

## 18.1 Mandatory end-to-end scenarios

> 1\. Institution A cannot read/download/export institution B’s record even with a copied UUID, forged filter or deep link.
>
> 2\. Institution submits a new record; database records immutable submitted version, document hash, actor, time and receipt; officer sees it in assigned queue.
>
> 3\. OCR extracts candidate values; reviewer corrects one field; original extraction and document hash remain; no bank-confirmed badge is created.
>
> 4\. Bank confirmation workflow remains pending until authorised source evidence is received and reviewed; inconclusive response opens an exception.
>
> 5\. Statement import is idempotent; same batch is not duplicated; malformed rows are quarantined/reported; ambiguity does not auto-confirm.
>
> 6\. Observation is raised, institutional response is submitted, case is reassigned, reviewer resolves it with reason and the full timeline remains available.
>
> 7\. Maturity scanner runs twice and creates one logical reminder per schedule key; scheduler outage is detectable and recoverable.
>
> 8\. Renewal/replacement produces a linked record; old instrument remains historically complete; date gap/overlap requires explicit policy handling.
>
> 9\. Release checklist blocks or defers incomplete cases; same-person maker/checker is denied; authority limit and MFA are checked; execution state needs trusted evidence.
>
> 10\. Domain event persists inbox record even if push fails; invalid device registration is cleaned; user acknowledges from inbox; no external “delivered” status is fabricated.
>
> 11\. Production configuration refuses demo seed, fake connectors, simulated clock and test credentials.
>
> 12\. Audit tamper attempt is denied for app roles; signed checkpoint/central log verification detects a changed/deleted event.
>
> 13\. Backups restore database plus object metadata/documents; post-restore hashes, counts and key references are reconciled.
>
> 14\. Push provider outage, email bounce, bank integration timeout, worker restart and database failover create controlled recoverable states and alerts.

## 18.2 Security test checklist

| **Risk class**                     | **Test examples**                                                                                                                                                     |
|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Broken object authorisation (BOLA) | Change IDs in detail/list/search/export/document and notification routes; cross-institution and cross-region attempts.                                                |
| Broken function authorisation      | Call privileged endpoint directly even when UI hides it; downgrade role during open session.                                                                          |
| Mass assignment/property exposure  | Submit server-owned properties and hidden fields; inspect API responses for unwanted account/PII fields.                                                              |
| Authentication/session             | Expired/revoked refresh token, session fixation, MFA brute force, invitation reuse, account recovery abuse.                                                           |
| File/document abuse                | Magic-byte mismatch, oversized files, malformed PDFs, embedded scripts, archive bombs, malware test sample, OCR hidden-text/prompt injection.                         |
| Financial logic                    | Amount precision, date boundary/timezone, duplicate requests, stale update, concurrent approver, out-of-order statement import, reversed payment.                     |
| Notification privacy               | Lock-screen data leakage, forged deep links, push to prior user after logout, token rotation, denied permission and provider outage.                                  |
| Integration safety                 | SSRF, expired/rotated credentials, signature/checksum mismatch, provider timeout, duplicate callback/webhook, replay and rate-limit controls.                         |
| Audit integrity                    | Attempt edit/delete; out-of-order timestamp; missing event in a transaction; checkpoint mismatch; sensitive values in logs.                                           |
| Mobile                             | Insecure local storage, backup leakage, clipboard, screenshots/backgrounding, deep links, certificate validation, root/jailbreak threat model and cache after logout. |
| Operational resilience             | Worker crash, full disk, DB connection exhaustion, delayed queue, key expiry, backup failure and restoration.                                                         |
| Accessibility/usability            | Keyboard navigation, screen reader, focus order, zoom, contrast, target size, form validation, localisation and low bandwidth.                                        |

## 18.3 Set actual SLAs instead of inventing them

No reliable production workload, user count, transaction volume or service level was provided in the research materials. Therefore this report does not invent concurrent-user capacity, p95 response time, OCR accuracy, notification delivery rate, or achieved improvement. AICTE should approve targets after workload discovery and a representative load test. Track KPIs from baseline data rather than claiming unmeasured gains.

# 19. Implementation roadmap with definition of done

| **Phase**                                 | **Build scope**                                                                                                                                                                       | **Exit gate / definition of done**                                                                                              |
|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| 0\. Process discovery                     | Policy catalogue, current amendments, instrument type scope, role mapping, release authority/delegation, integration owners, records inventory, retention and workload/SLA discovery. | Signed business requirements; no disputed release rule used in production; named decision owners.                               |
| 1\. Secure platform foundation            | Repo, CI/CD, approved identity, MFA, session revocation, authorization middleware, role/scope model, audit, DB migrations and environment separation.                                 | Role × action × scope negative tests pass; production config checks work; secrets are not in repository.                        |
| 2\. Core case/instrument workflow         | Institution registry, draft/submission/versioning, document upload quarantine, intake/scrutiny, observations and timeline.                                                            | End-to-end institution-to-officer path works on staging with full audit and no silent record overwrite.                         |
| 3\. Evidence and real verification        | OCR assist; FDR confirmation request/evidence; authorised statement import; reconciliation rules and exception queue.                                                                 | Each evidence state is justified; one real authorised source path is tested or clearly unavailable; no fake success.            |
| 4\. Lifecycle and release                 | Maturity engine, reminder rules, renewal lineage, policy checklist, maker-checker, step-up auth, authority decision and execution evidence.                                           | Official policy versions and role delegation approved; date boundary, duplicate job and same-person tests pass.                 |
| 5\. Notification + mobile parity          | Native app login, shared API client, device registry, FCM/APNs, in-app inbox, web push where supported, deep links, retries and telemetry.                                            | Real supported devices tested. Denied permission/outage path is safe. Provider acceptance not mislabeled as user delivery.      |
| 6\. Production integrations and migration | AICTE registry/API, bank, identity or eSign connectors only after approval; historical data migration and reconciliation.                                                             | Formal integration owner, production credentials, source contracts, runbooks and business sign-off; migration totals reconcile. |
| 7\. Security/accessibility assurance      | ASVS/API/MASVS traceability, VAPT, GIGW review, privacy legal mapping, load test, restore drill, training and runbooks.                                                               | No unresolved release-blocking findings, required certificates/sign-offs complete, rollback/recovery tested.                    |
| 8\. Controlled production pilot           | Limited verified institutions/officials, monitored metrics, issue triage, access review and rollback.                                                                                 | Business/security owners approve expansion based on evidence from the pilot, not assumption.                                    |

## 19.1 Priority order for a student/small team

> 1\. Define the instrument types, exact policy sources, state machine and role/action matrix.
>
> 2\. Implement identity/access controls and tests before bulk data.
>
> 3\. Build the core workflow end-to-end: submit → scrutiny → observation/correction → verification evidence → audit timeline.
>
> 4\. Add real statement/bank evidence process and exceptions; do not fake a connector.
>
> 5\. Implement maturity/reminder engine and release maker-checker.
>
> 6\. Build web and native mobile on the shared API contract; add persistent inbox and real push integration.
>
> 7\. Run security/accessibility tests and restore/incident drills.
>
> 8\. Only after core is stable, add bounded OCR, policy retrieval and analytics.

# 20. Metrics and service operations

## 20.1 Product / business metrics

- Median and 95th-percentile submission-to-first-review time.

- Median and 95th-percentile bank-confirmation/ledger-reconciliation time.

- Share of instruments by evidence source/type; do not collapse incomparable evidence paths into one opaque score.

- Count and age distribution of open observations, unmatched transactions and external verification requests.

- Maturity/renewal obligations due in a chosen horizon and reminder coverage per approved recipient policy.

- Release request processing time; return-for-correction rate; number of approvals blocked by missing requirements.

- OCR field-level error/correction rate measured against human-reviewed samples.

- Reminder metrics separated into event created, provider accepted, device received where observable, opened and acknowledged.

## 20.2 System/operations metrics

- API availability and latency; error rate; database connections/replication lag; queue backlog and oldest event age.

- Scheduler last-success time, missed windows, number of due obligations scanned, failed/deduplicated job counts.

- Provider acceptance/failure, credential expiry, invalid token/endpoint counts, dead-letter events and retry saturation.

- Backup age/failure and restore exercise performance; object/hash reconciliation.

- Role-change audit, MFA enrolment, stale privileged accounts, denied access attempts and suspected BOLA spikes.

- Storage growth, quarantined file count, scan failures, OCR queue size and malware alerts.

## 20.3 Alerting principles

Alert on service degradation that needs action, not every individual business event. Business notification failures should surface to the user/case owner through the inbox and to operations through aggregate health alerts. Every alert needs owner, severity, first-response expectation, runbook and escalation. Tune noisy alerts to avoid operators ignoring them.

# 21. Open decisions requiring formal AICTE answers

| **ID** | **Question / decision**                                                                                                             | **Why it blocks implementation**                                             | **Owner to nominate**                         |
|--------|-------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|-----------------------------------------------|
| D-01   | Which APH versions, amendments, circulars and clause interpretations govern each deposit/FDR type?                                  | Rules engine and required amount/eligibility/release checklist depend on it. | Regulation Bureau policy owner + legal        |
| D-02   | Which role/post can submit, scrutinise, bank-verify, recommend, approve, execute and audit each case? What delegation limits apply? | RBAC and maker-checker must reflect actual legal authority.                  | Process owner / HR / legal                    |
| D-03   | Does the portal replace the current portal or integrate with it? Which system is authoritative per field?                           | Prevents duplicate systems of record and conflicting status.                 | AICTE product/system owner                    |
| D-04   | What official institution registry ID and representative-authorisation process should be used?                                      | Prevents institution impersonation and duplicates.                           | Registry/application owner                    |
| D-05   | How does AICTE provide bank evidence/statement? Which accounts, feed/file formats and verification arrangements are authorised?     | No real bank reconciliation without trusted source data.                     | Finance / bank relationship owner             |
| D-06   | What proof from a bank is sufficient to verify a legacy FDR and current lien/status?                                                | Receipt scans and OCR cannot establish current instrument state.             | Finance/legal + participating banks           |
| D-07   | Are other instruments (BG/e-BG etc.) in scope? Which official verification standard is required?                                    | Avoid unsupported bank/protocol claims.                                      | Policy owner + bank integrations              |
| D-08   | What is the approved identity provider/Parichay onboarding plan and MFA policy?                                                     | Account lifecycle and trust model depend on it.                              | AICTE identity/security team                  |
| D-09   | Hosting/data residency, network, incident monitoring, backups, RPO/RTO, DR and approved vendors?                                    | Free-tier assumptions are unsuitable to establish production.                | CISO/IT/infra/procurement                     |
| D-10   | Which notification channels and business events are official notices, and what fallback/retention applies?                          | Push cannot be assumed a legal notice or guaranteed delivery.                | Process/legal/comms owner                     |
| D-11   | What retention periods and legal hold/deletion rules apply to instruments, bank statements, documents, audit and notification logs? | Retention and disposal must be implemented by class.                         | Records/legal/privacy owner                   |
| D-12   | Which OCR/AI providers or local models may process real documents and under what controls?                                          | Avoid unauthorised disclosure to model providers.                            | Security/privacy/product owner                |
| D-13   | What target workload, concurrent officers/institutions, upload size/volume and service level are expected?                          | Needed to size production hosting and set meaningful SLAs.                   | Business owner + SRE/infra                    |
| D-14   | What GIGW/STQC, accessibility, VAPT/certification and procurement approvals are required before go-live?                            | Engineering readiness does not equal formal acceptance.                      | Digital service owner + STQC/security liaison |

# 22. Risk register with concrete controls

| **Risk**                                     | **Severity** | **Required control / gate**                                                                                                                |
|----------------------------------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Incorrect policy or amount applied           | Critical     | Approved policy register; rule version and effective date; test cases signed by policy owner; no unresolved disputed rule in production.   |
| False FDR verification / reconciliation      | Critical     | Authoritative bank evidence; no OCR-as-proof; source provenance; dual review for exceptions; no mock success.                              |
| Cross-institution leakage                    | Critical     | RBAC+ABAC, object and field-level checks, RLS defence in depth, automated negative tests and independent penetration test.                 |
| Unauthorised release / maker-checker bypass  | Critical     | Explicit decision endpoint/state machine, policy checklist, delegated limits, step-up MFA, database constraints and audit.                 |
| Missed deadline due to push failure          | High         | Server-side scheduler, persistent inbox, queue monitoring, alternate delivery when approved, escalation queue and deadline reconciliation. |
| Fake or stale role remains active            | High         | Time-bounded assignments, access recertification, central revocation, session invalidation and grant/revoke audit.                         |
| Sensitive data exposed through logs/provider | High         | Data minimisation, field redaction, access restrictions, vendor review, key control and incident runbook.                                  |
| Document malware / malicious PDF             | High         | Quarantine, file signature checks, antivirus, sanitisation, isolated OCR and access only after safety pipeline passes.                     |
| Duplicate imports or repeated actions        | High         | Idempotency keys, constraints, batch checksum and transactional outbox; concurrency tests.                                                 |
| Unrecoverable outage/data corruption         | Critical     | Approved RPO/RTO, protected backups, restore drills, source/record reconciliation and continuity SOP.                                      |
| Free provider limit/terms change             | Medium/high  | Production contracts/approved hosting, portability, integration adapter and tested provider-exit plan.                                     |
| Overengineering delays delivery              | High         | Modular monolith, staged scope, no voice, no early multi-agent/text-to-SQL, explicit exit gates.                                           |

# 23. Production go-live gate

Go-live is a formal decision by AICTE business, IT/security, legal/privacy, finance and operations—not a developer checkbox. All applicable items below must have evidence and a named approver.

- Policy register signed off; no unresolved penalty, amount, exemption, tenure or release ambiguity affecting real decisions.

- Official role mapping and delegation limits documented; every privileged action has maker-checker/separation rules where required.

- Institution verification and account recovery processes approved; MFA/session revocation exercised.

- All APIs and documents enforce institution/region/case scope. Negative authorisation tests and independent security review have passed.

- All document upload pipeline checks are operational; private object access and retention have been tested.

- Every bank/identity/notification integration shown as production-enabled has owner, contract, credentials, source provenance, monitoring and production acceptance evidence.

- Historical migration counts and discrepancies reconciled; source data provenance preserved and business sign-off recorded.

- Maturity scheduler, reminder idempotency, failure recovery and escalation tested. In-app inbox continues if push/email fails.

- Release/forfeiture flow, step-up authentication, policy citations, execution evidence and audit are end-to-end tested.

- Production image has no test seeder/demo accounts/fake provider/simulation clock; environment guard test passes.

- Backup restoration, disaster recovery, patching, alerting, incident response and role/access recertification are operational.

- GIGW/accessibility assessment, applicable DPDP analysis, CERT-In obligations and any required STQC/VAPT/certification completed and documented.

- Help/support, institution and officer training, runbooks, monitoring ownership, release rollback and vendor support contacts are ready.

# Appendix A. Research sources (primary / standards owners)

Access date for web-reviewed sources: 23 October 2026. URLs are provided so the team can re-open the authoritative source before implementation; official policy can change and should be rechecked for amendments.

<table>
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Ref</strong></th>
<th><strong>Source and use</strong></th>
<th><strong>URL / notes</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>R1</td>
<td>AICTE Approval Process Handbook 2024–2027, Clause 1.12/Table 1.4 and indexed Clause 6.46 “Release of Security Deposit”. Includes source-indexed amounts and release checklist elements; full current policy corpus still requires an official amendments sweep.</td>
<td>https://aicte-qa.aicte-india.org/sites/default/files/APH%20Final.pdf<br />
The AICTE-hosted PDF endpoint returned a 502 during direct open in this research session; its indexed text exposed Table 1.4 and Clause 6.46. Manually obtain the authoritative full PDF plus corrigenda/notices and have AICTE sign off before implementing policy rules.</td>
</tr>
<tr class="even">
<td>R2</td>
<td>GIGW 3.0 official scope and objective; government website/app framework and WCAG 2.1 reference.</td>
<td>https://guidelines.india.gov.in/scope-and-objective/</td>
</tr>
<tr class="odd">
<td>R3</td>
<td>STQC Website Quality Certification; formal evaluation and certificate process.</td>
<td>https://www.stqc.gov.in/website-quality-certification-0</td>
</tr>
<tr class="even">
<td>R4</td>
<td>CERT-In Directions No. 20(3)/2022-CERT-In dated 28 April 2022; NTP, incident reporting and rolling 180-day log requirements for covered entities.</td>
<td>https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf</td>
</tr>
<tr class="odd">
<td>R5</td>
<td>OWASP Application Security Verification Standard 5.0.0; official standard page says stable release published 30 May 2025.</td>
<td>https://asvs.owasp.org/</td>
</tr>
<tr class="even">
<td>R6</td>
<td>OWASP API Security Top 10 2023; BOLA, authentication, property/function-level authorisation, resource consumption and unsafe API consumption.</td>
<td>https://owasp.org/www-project-api-security/<br />
https://api-security.owasp.org/editions/2023/en/0x11-t10/</td>
</tr>
<tr class="odd">
<td>R7</td>
<td>OWASP Mobile Application Security (MASVS/MASWE/MASTG) for mobile-specific security controls and tests.</td>
<td>https://mas.owasp.org/MASVS/</td>
</tr>
<tr class="even">
<td>R8</td>
<td>Digital Personal Data Protection Act, 2023 — official Gazette text, commencement can be appointed for different provisions on different dates.</td>
<td>https://egazette.gov.in/WriteReadData/2023/248045.pdf</td>
</tr>
<tr class="odd">
<td>R9</td>
<td>MeitY official DPDP Act / Rules portal listing the 2025 Rules, corrigendum and enforcement timeline; the page lists publication date as 14 November 2025.</td>
<td>https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa<br />
Read with the Gazette commencement notifications; no blanket commencement statement.</td>
</tr>
<tr class="even">
<td>R10</td>
<td>MeitY GI Cloud (MeghRaj) adoption and implementation roadmap.</td>
<td>https://meity.gov.in/writereaddata/files/GI-Cloud%20Adoption%20and%20Implementation%20Roadmap%281%29_0.pdf<br />
Reference for government cloud direction; current approved hosting route still requires AICTE confirmation.</td>
</tr>
<tr class="odd">
<td>R11</td>
<td>Firebase Cloud Messaging Android setup; Android 13+ runtime notification permission.</td>
<td>https://firebase.google.com/docs/cloud-messaging/android/get-started</td>
</tr>
<tr class="even">
<td>R12</td>
<td>Firebase message delivery semantics and registration freshness guidance.</td>
<td>https://firebase.google.com/docs/cloud-messaging/understand-delivery<br />
https://firebase.google.com/docs/cloud-messaging/manage-tokens</td>
</tr>
<tr class="odd">
<td>R13</td>
<td>Apple remote notification server, APNs response semantics and push metrics.</td>
<td>https://developer.apple.com/documentation/usernotifications/setting-up-a-remote-notification-server<br />
https://developer.apple.com/documentation/usernotifications/handling-notification-responses-from-apns</td>
</tr>
<tr class="even">
<td>R14</td>
<td>MDN Push API and secure-context requirements for web push/service workers.</td>
<td>https://developer.mozilla.org/en-US/docs/Web/API/Push_API</td>
</tr>
<tr class="odd">
<td>R15</td>
<td>Supplied research report, “AICTE Security Deposit / FDR Management Portal: A Zero-Cost, AI-Agent and Voice-Enabled Build Blueprint”. Domain-workflow ideas reviewed; cost/provider claims were not treated as production guarantees.</td>
<td>User-provided research file in this conversation. Use as design context, not as official authority.</td>
</tr>
<tr class="even">
<td>R16</td>
<td>G.S.R. 843(E), notification under section 1(2) of the DPDP Act, 2023; specifies which Act provisions commence on publication, one year or eighteen months after publication.</td>
<td>https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf</td>
</tr>
<tr class="odd">
<td>R17</td>
<td>G.S.R. 846(E), Digital Personal Data Protection Rules, 2025; Rule 1 sets different start dates for Rules 1–2/17–21, Rule 4 and Rules 3/5–16/22–23.</td>
<td>https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf</td>
</tr>
</tbody>
</table>

## Appendix B. Explicit research limitations

- The official AICTE APH PDF is linked and its Table 1.4 and Clause 6.46 text were available via the search index, but the PDF endpoint returned 502 when opened directly by the research tool. Therefore the listed release checklist is a source-indexed extract, not a substitute for obtaining the complete official document and confirming current amendments with AICTE.

- No universal public API for verifying all legacy paper FDRs was identified in sources reviewed. This is not a claim that no bilateral bank or internal AICTE interface exists; ask the official source owner.

- DPDP commencement is phased. The official portal lists publication as 14 November 2025 while Gazette notifications are dated 13 November 2025; one-year and eighteen-month planning dates are approximate until counsel confirms the legally controlling publication date and all applicable corrigenda. Obtain a current provision-by-provision applicability map.

- FCM/APNs/Web Push are delivery platforms, not guaranteed real-time channels and not automatically legally valid notice. AICTE must define which channels satisfy its official communication process.

- This report provides a target architecture and test plan. It does not assert software has been implemented, integrated, deployed, certified or penetration-tested.

## Appendix C. Short source-to-control traceability

| **Source**                        | **Requirement in this blueprint**                                                                                 | **Evidence expected before go-live**                                                                                               |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| AICTE APH \[R1\]                  | Versioned policy/deposit amount/release rules and document provenance.                                            | Approved rules register, source clause links, effective dates and signed-off test cases.                                           |
| GIGW \[R2\] / STQC \[R3\]         | Accessible government-facing experience and formal quality/certification workflow if required.                    | Accessibility assessment, website quality manual, VA/security reports and any required formal certificate.                         |
| CERT-In \[R4\]                    | Time sync, covered incident-reporting path, 180-day in-jurisdiction logs.                                         | NTP config evidence, named contact, log retention tests and incident runbook.                                                      |
| OWASP ASVS/API \[R5–R6\]          | Web/API security and object-level access tests.                                                                   | Versioned control matrix, automated tests, VAPT closure and risk acceptance log.                                                   |
| OWASP MASVS \[R7\]                | Mobile storage/auth/network/platform/privacy controls.                                                            | Mobile security assessment and remediation report.                                                                                 |
| DPDP Act/Rules \[R8–R9, R16–R17\] | Data inventory, notices/purpose/retention/rights/breach process per applicable provisions and phased start dates. | Provision-level legal applicability memo with exact dates, data map, retention schedule, contracts and approved privacy workflows. |
| FCM/APNs/Web Push \[R11–R14\]     | Real credentials, permission/token lifecycle, delivery status separation and failure handling.                    | Real-device evidence, provider telemetry, permission-denied test and outage/retry test.                                            |
| MeghRaj reference \[R10\]         | Hosting/operations decision owned by government IT/procurement.                                                   | Approved hosting decision, threat model, contract/SLA, DR design and security sign-off.                                            |
