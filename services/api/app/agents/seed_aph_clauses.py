"""Synthetic placeholder APH clauses for development/demo/testing — see
app.models.rag.AphClauseChunk's docstring. Clause 6.46 reuses the one
citation the source blueprint actually quotes (Blueprint.txt line 371);
the rest are invented IDs/text for pipeline development, never real
regulatory text.
"""

from sqlalchemy.orm import Session

from app.agents.rag import ingest_clause

SYNTHETIC_CLAUSES = [
    {
        "clause_id": "APH 2024-27, cl. 6.46",
        "title": "Release of security deposit on maturity",
        "text": (
            "An institution's security deposit instrument becomes eligible "
            "for release only after it has reached its declared maturity date and the competent "
            "authority has recorded no pending scrutiny observations against the file."
        ),
    },
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


def seed(session: Session) -> int:
    count = 0
    for clause in SYNTHETIC_CLAUSES:
        ingest_clause(session, **clause)
        count += 1
    session.flush()
    return count
