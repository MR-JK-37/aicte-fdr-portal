"""APH clause corpus for the Compliance RAG agent.

Two tiers, never conflated (app.models.rag.AphClauseChunk.synthetic_placeholder
distinguishes them, and app.agents.rag tags every synthetic chunk
`[SYNTHETIC PLACEHOLDER]` in the LLM context and strips it only from the
rendered answer, never from the retrieval record):

- SYNTHETIC_CLAUSES: invented IDs/text for pipeline development. Never
  real regulatory text — do not cite as AICTE policy.
- SOURCE_INDEXED_CLAUSES: `synthetic_placeholder=False`. Text quoted
  from docs/spec/SPEC_v3.md §2.1/§2.3, which is itself a source-indexed
  extraction of the real AICTE-hosted Approval Process Handbook
  2024-2027 (Table 1.4, Clause 6.46) — real AICTE text, but the
  official PDF returned 502 when opened directly during that research
  session (SPEC_v3.md line 30), so this is read from the handbook's own
  search index, not a reviewed full-document copy. Each entry below
  keeps SPEC_v3's accuracy caveat inline in `text` for exactly that
  reason: it is meaningfully better-sourced than a placeholder, but
  still not a substitute for AICTE policy-owner sign-off before any
  penalty/amount/eligibility decision is automated from it (CLAUDE.md
  non-negotiable #7).
"""

from sqlalchemy.orm import Session

from app.agents.rag import ingest_clause

SYNTHETIC_CLAUSES = [
    {
        "clause_id": "APH 2024-27, cl. 6.08",
        "title": "Joint account creation and lien marking",
        "text": (
            "All Security Deposit Fixed Deposit Receipts (FDRs) must be "
            "established in the joint names of the sponsoring Trust/Society and the Regional Officer, "
            "AICTE. A clear and irrevocable lien in favour of AICTE must be marked by the issuing bank."
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 6.12",
        "title": "Leased-campus security deposit multiplier",
        "text": (
            "Where an institution's campus land is held on lease rather than "
            "in freehold, the required security deposit under Table 1.4 is multiplied by the factor "
            "prescribed in the applicable year's handbook."
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 6.15",
        "title": "Validity period and tenure of security deposit",
        "text": (
            "Fixed Deposit Receipts submitted towards security deposit must "
            "have a minimum initial validity and tenure of 8 to 10 years (or as specified for the program category) "
            "and must be maintained without break until official discharge."
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 6.22",
        "title": "Prohibition of premature withdrawal or encashment",
        "text": (
            "Institutions are strictly prohibited from prematurely withdrawing, "
            "encashing, pledging, or hypothecating any security deposit FDR without prior written approval "
            "and No Objection Certificate (NOC) issued by the AICTE Competent Authority."
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 6.30",
        "title": "Bank Guarantee in lieu of FDR",
        "text": (
            "Bank Guarantees submitted in lieu of FDR must be issued by a "
            "scheduled commercial bank, with an operative claim clause valid across the entire statutory "
            "period plus an additional claim period of twelve months."
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 6.38",
        "title": "Interest accrual and auto-renewal",
        "text": (
            "Interest accrued on joint FDR accounts shall automatically compound "
            "and reinvest upon cumulative renewal unless specific regulatory exemption is granted."
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 7.03",
        "title": "Penalty for delayed security deposit submission",
        "text": (
            "A delay in submitting the required security deposit attracts a "
            "graded penalty on the shortfall amount, escalating with the duration of the delay."
        ),
    },
]

_ACCURACY_BOUNDARY = (
    " [Source-indexed extract from the official AICTE-hosted Approval Process "
    "Handbook 2024-2027; the direct PDF could not be opened for full review, so "
    "this is read from the handbook's own search index, not a reviewed complete "
    "document. Confirm current amendments and case applicability with the AICTE "
    "policy owner before relying on this for a penalty, amount, or eligibility "
    "decision.]"
)

SOURCE_INDEXED_CLAUSES = [
    {
        "clause_id": "APH 2024-27, cl. 6.46",
        "title": "Release of Security Deposit — required document and clearance path",
        "text": (
            "Clause 6.46 ('Release of Security Deposit') requires, for an "
            "institution's release request: an application/request letter for FDR or RTGS "
            "release; Affidavit 6 with the institution's and Trust/Society/Company's details and "
            "the FDR/RTGS details; a copy of the FDR to be released (or, for an RPGF corpus fund, "
            "DD copies, or online payment proof); a copy of the latest Letter of Approval (LoA) or "
            "Extension of Approval (EoA); and clearances from PGRC, the Vigilance Cell and other "
            "relevant AICTE cells/bureaus. For FDR/RPGF, release requires a No Objection Certificate "
            "(NOC) from the Approval Bureau; for RTGS, a sanction order issued by the Council — these "
            "two authorisation paths are distinct and must not be substituted for each other. Where "
            "financial embezzlement involving a government body or bank exists on the file, no "
            "release is permitted until an NOC is received from that body. The Council may separately "
            "initiate penal action for security-deposit norm violations." + _ACCURACY_BOUNDARY
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 6.46 (clearance evidence rule)",
        "title": "Release clearances — what counts as resolved",
        "text": (
            "Each required clearance (PGRC, Vigilance Cell, other relevant AICTE cells) on a release "
            "file must be explicitly resolved with its own source, responsible cell, received date and "
            "outcome. An empty clearance queue, missing data, or an integration outage must never be "
            "read as 'cleared' — a clearance is only satisfied when a specific resolving record says so. "
            "A release checklist item is one of SATISFIED, NOT SATISFIED, PENDING SOURCE or NOT "
            "APPLICABLE, each with the deciding user, evidence link, rule version and reason; "
            "'all documents uploaded' is not equivalent to clearance, approval or release." + _ACCURACY_BOUNDARY
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 1.12 / Table 1.4",
        "title": "Security deposit amounts by programme and level",
        "text": (
            "Table 1.4 of the handbook lists security deposit amounts by programme and level: "
            "Engineering and Technology — Diploma/Post-Diploma Rs 15 lakh, Undergraduate Rs 35 lakh, "
            "PG Diploma/PG Degree Rs 15 lakh. Planning, Applied Arts and Crafts, Design, and Hotel "
            "Management and Catering Technology — Rs 15 lakh at every listed level. Computer "
            "Applications (e.g. BCA/MCA) and Management (e.g. BBA/MBA) — no Diploma/Post-Diploma tier "
            "listed, Undergraduate Rs 5 lakh, PG Diploma/PG Degree Rs 15 lakh. The handbook states the "
            "amount is doubled where the institution's campus building or land is held on lease rather "
            "than freehold, and that the amount remains with the Council for 10 years, with the "
            "principal returned at the end of the term subject to possible extension and/or forfeiture "
            "in specified circumstances. These are the table's own figures for the programmes it lists "
            "— they are not a universal rule for every institution or programme category, and "
            "applicability, exemptions, conversions, historical deposits and later amendments must be "
            "assessed for each case, not inferred from the table alone." + _ACCURACY_BOUNDARY
        ),
    },
]


def seed(session: Session) -> int:
    count = 0
    for clause in SYNTHETIC_CLAUSES:
        ingest_clause(session, **clause)
        count += 1
    for clause in SOURCE_INDEXED_CLAUSES:
        ingest_clause(session, synthetic_placeholder=False, **clause)
        count += 1
    session.flush()
    return count
