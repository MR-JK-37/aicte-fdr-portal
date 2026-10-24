# OPEN_DECISIONS.md (SPEC_v3 §21) — safe default the build implements until AICTE answers

Claude Code updates the "Implemented default" and "Status" columns as it builds. Answers come only from AICTE owners — never from a model.

| ID | Decision | Owner (nominate) | Implemented default (until answered) | Status |
|---|---|---|---|---|
| D-01 | Governing APH versions/amendments/circulars per deposit/FDR type; penalty rules | Regulation Bureau policy owner + legal | All rules `draft`; checks depending on them say "policy rule not approved"; penalties BLOCKED | Open |
| D-02 | Role/post mapping, delegation limits, who can approve releases | Process owner / HR / legal | Functional roles; empty delegation limits ⇒ approve action denied | Open |
| D-03 | Replace vs integrate with current portal; authoritative system per field | AICTE product/system owner | System of record for tracked instruments; import tools; no sync claims | Open |
| D-04 | Official institution registry ID + representative-authorisation process | Registry/application owner | CSV import + onboarding review workflow | Open |
| D-05 | Bank evidence/statement route, accounts, formats | Finance / bank relationship owner | Statement-file import | Open |
| D-06 | Sufficient bank proof for legacy FDR existence/lien/status | Finance/legal + banks | Bank-confirmation workflow with attachments; no auto-proof | Open |
| D-07 | Other instruments (BG/e-BG) in scope? | Policy owner + bank integrations | Disabled | Open |
| D-08 | Approved identity provider / Parichay / MFA policy | AICTE identity/security | Keycloak behind OIDC adapter; MFA mandatory for staff | Open |
| D-09 | Hosting/residency/network/RPO/RTO/DR/vendors | CISO/IT/infra/procurement | Portable containers; dev/staging/demo only | Open |
| D-10 | Official notices, channels, fallback, retention, reminder windows | Process/legal/comms owner | Conservative defaults; no claim push is a legal notice; no invented windows | Open |
| D-11 | Retention periods, legal hold, deletion | Records/legal/privacy | No disposal until classes configured | Open |
| D-12 | Approved OCR/AI providers for real documents | Security/privacy/product | Tier S local-only; external Tier P only | Open |
| D-13 | Workload, concurrency, volumes, SLAs | Business owner + SRE | Measure; no invented SLAs | Open |
| D-14 | GIGW/STQC, accessibility, VAPT, procurement approvals | Digital service owner + STQC/security | Checklists only; no certificate claims | Open |
