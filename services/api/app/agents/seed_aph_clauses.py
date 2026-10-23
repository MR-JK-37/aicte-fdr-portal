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
            "[SYNTHETIC PLACEHOLDER] An institution's security deposit instrument becomes eligible "
            "for release only after it has reached its declared maturity date and the competent "
            "authority has recorded no pending scrutiny observations against the file."
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 6.12",
        "title": "Leased-campus security deposit multiplier",
        "text": (
            "[SYNTHETIC PLACEHOLDER] Where an institution's campus land is held on lease rather than "
            "in freehold, the required security deposit under Table 1.4 is multiplied by the factor "
            "prescribed in the applicable year's handbook."
        ),
    },
    {
        "clause_id": "APH 2024-27, cl. 7.03",
        "title": "Penalty for delayed security deposit submission",
        "text": (
            "[SYNTHETIC PLACEHOLDER] A delay in submitting the required security deposit attracts a "
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
