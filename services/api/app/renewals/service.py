"""Renewal and replacement lineage service (F-11 / SPEC §6.1 / §18.1 Scenario 8).

Handles:
1. Linkage of predecessor and successor instruments.
2. DAG cycle prevention (no self-links, no circular dependencies).
3. Date gap/overlap calculation:
   - gap_days = max(0, successor.issue_date - predecessor.maturity_date)
   - overlap_days = max(0, predecessor.maturity_date - successor.issue_date)
   - If gap_days > allowed_gap (default 0 days): automatically creates a
     Discrepancy and a draft ScrutinyObservation.
4. Old instrument transitions to SUPERSEDED only when new instrument
   reaches ACTIVE_TRACKING or ACTIVE under approved checks.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.lifecycle import apply_transition
from app.models.core import AppUser, Discrepancy, Instrument, ScrutinyObservation
from app.models.enums import InstrumentStatus
from app.models.workflow import InstrumentLineage
from app.outbox.producer import enqueue_outbox_event


class LineageError(Exception):
    pass


class LineageCycleError(LineageError):
    pass


class LineageNotFoundError(LineageError):
    pass


def assert_no_cycle(
    session: Session, predecessor_id: uuid.UUID, successor_id: uuid.UUID
) -> None:
    """Checks for cycles in the instrument lineage graph using DFS.
    Rejects self-links and any path that would make successor an ancestor of predecessor.
    """
    if predecessor_id == successor_id:
        raise LineageCycleError(
            "Lineage cycle rejected: instrument cannot be its own predecessor or successor"
        )

    visited = set()
    queue = [successor_id]

    while queue:
        current = queue.pop(0)
        if current == predecessor_id:
            raise LineageCycleError(
                f"Lineage cycle rejected: connecting {predecessor_id} to {successor_id} creates a circular dependency"
            )

        if current in visited:
            continue
        visited.add(current)

        # Find all successors of current
        next_succs = (
            session.execute(
                select(InstrumentLineage.successor_id).where(
                    InstrumentLineage.predecessor_id == current
                )
            )
            .scalars()
            .all()
        )
        queue.extend(next_succs)


def calculate_gap_and_overlap(
    predecessor: Instrument, successor: Instrument
) -> tuple[int, int]:
    """Calculates date gap and overlap days between predecessor maturity and successor issue date."""
    if not predecessor.maturity_date or not successor.issue_date:
        return 0, 0

    pred_mat = predecessor.maturity_date.date()
    succ_iss = successor.issue_date.date()

    if succ_iss > pred_mat:
        gap_days = (succ_iss - pred_mat).days
        overlap_days = 0
    elif succ_iss < pred_mat:
        gap_days = 0
        overlap_days = (pred_mat - succ_iss).days
    else:
        gap_days = 0
        overlap_days = 0

    return gap_days, overlap_days


def create_instrument_lineage(
    session: Session,
    predecessor_id: uuid.UUID,
    successor_id: uuid.UUID,
    *,
    relationship_type: str = "RENEWAL",
    policy_allowed_gap_days: int = 0,
    created_by: AppUser | None = None,
) -> InstrumentLineage:
    """Links predecessor and successor instruments and computes gap/overlap."""
    predecessor = session.get(Instrument, predecessor_id)
    if not predecessor:
        raise LineageNotFoundError(f"Predecessor instrument {predecessor_id} not found")

    successor = session.get(Instrument, successor_id)
    if not successor:
        raise LineageNotFoundError(f"Successor instrument {successor_id} not found")

    # Cycle prevention
    assert_no_cycle(session, predecessor_id, successor_id)

    # Check if link already exists
    existing = session.execute(
        select(InstrumentLineage).where(
            InstrumentLineage.predecessor_id == predecessor_id,
            InstrumentLineage.successor_id == successor_id,
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    gap_days, overlap_days = calculate_gap_and_overlap(predecessor, successor)
    is_gap_discrepancy = gap_days > policy_allowed_gap_days

    lineage = InstrumentLineage(
        id=uuid.uuid4(),
        predecessor_id=predecessor_id,
        successor_id=successor_id,
        relationship_type=relationship_type,
        gap_days=gap_days,
        overlap_days=overlap_days,
        policy_allowed_gap_days=policy_allowed_gap_days,
        is_gap_discrepancy=is_gap_discrepancy,
    )
    session.add(lineage)
    session.flush()

    # If gap exceeds allowed threshold, create Discrepancy & ScrutinyObservation
    if is_gap_discrepancy:
        disc = Discrepancy(
            id=uuid.uuid4(),
            institution_id=successor.institution_id,
            instrument_id=successor.id,
            field="renewal_gap_days",
            declared_value=f"gap_days={gap_days}",
            extracted_value=f"allowed_gap={policy_allowed_gap_days}",
            severity="HIGH",
            status="open",
        )
        session.add(disc)

        obs = ScrutinyObservation(
            id=uuid.uuid4(),
            institution_id=successor.institution_id,
            instrument_id=successor.id,
            officer_id=created_by.id if created_by else None,
            observation=f"Security deposit coverage gap of {gap_days} days detected between predecessor {predecessor.instrument_number} and successor {successor.instrument_number} (policy limit: {policy_allowed_gap_days} days).",
            status="OPEN",
        )
        session.add(obs)
        session.flush()

    append_audit_entry(
        session,
        action="instrument.lineage_linked",
        entity_type="instrument_lineage",
        entity_id=str(lineage.id),
        before=None,
        after={
            "predecessor_id": str(predecessor_id),
            "successor_id": str(successor_id),
            "relationship_type": relationship_type,
            "gap_days": gap_days,
            "overlap_days": overlap_days,
            "is_gap_discrepancy": is_gap_discrepancy,
        },
        actor_id=str(created_by.id) if created_by else None,
        institution_id=str(predecessor.institution_id),
    )

    enqueue_outbox_event(
        session,
        aggregate_type="instrument",
        aggregate_id=successor.id,
        event_type="instrument.renewal_linked",
        payload={
            "predecessor_id": str(predecessor_id),
            "successor_id": str(successor_id),
            "relationship_type": relationship_type,
            "gap_days": gap_days,
            "overlap_days": overlap_days,
        },
        dedupe_key=f"instrument.renewal_linked:{predecessor_id}:{successor_id}",
    )

    return lineage


def on_successor_reaches_active(
    session: Session,
    successor: Instrument,
    *,
    actor_role: str = "system",
    actor_id: str | None = None,
) -> list[Instrument]:
    """When a new instrument reaches ACTIVE_TRACKING (or ACTIVE),
    all its direct predecessors transition to SUPERSEDED.
    """
    predecessors = (
        session.execute(
            select(Instrument)
            .join(InstrumentLineage, InstrumentLineage.predecessor_id == Instrument.id)
            .where(InstrumentLineage.successor_id == successor.id)
        )
        .scalars()
        .all()
    )

    superseded: list[Instrument] = []
    for pred in predecessors:
        if pred.status in (
            InstrumentStatus.ACTIVE,
            InstrumentStatus.ACTIVE_TRACKING,
            InstrumentStatus.EXPIRING,
            InstrumentStatus.MATURED,
            InstrumentStatus.RENEWAL_REQUESTED,
            InstrumentStatus.REPLACEMENT_REQUESTED,
        ):
            # Transition to SUPERSEDED
            apply_transition(
                session,
                pred,
                InstrumentStatus.SUPERSEDED,
                actor_role=actor_role,
                actor_id=actor_id,
                reason=f"Superseded by renewal instrument {successor.instrument_number} ({successor.id})",
                reason_code="RENEWAL_SUPERSEDED",
            )
            superseded.append(pred)

    session.flush()
    return superseded


def get_lineage_graph(session: Session, instrument_id: uuid.UUID) -> dict:
    """Returns the lineage DAG around an instrument (predecessors and successors)."""
    instrument = session.get(Instrument, instrument_id)
    if not instrument:
        raise LineageNotFoundError(f"Instrument {instrument_id} not found")

    pred_links = session.execute(
        select(InstrumentLineage, Instrument)
        .join(Instrument, Instrument.id == InstrumentLineage.predecessor_id)
        .where(InstrumentLineage.successor_id == instrument_id)
    ).all()

    succ_links = session.execute(
        select(InstrumentLineage, Instrument)
        .join(Instrument, Instrument.id == InstrumentLineage.successor_id)
        .where(InstrumentLineage.predecessor_id == instrument_id)
    ).all()

    return {
        "instrument_id": str(instrument.id),
        "instrument_number": instrument.instrument_number,
        "status": instrument.status.value,
        "predecessors": [
            {
                "lineage_id": str(link.id),
                "instrument_id": str(pred.id),
                "instrument_number": pred.instrument_number,
                "status": pred.status.value,
                "relationship_type": link.relationship_type,
                "gap_days": link.gap_days,
                "overlap_days": link.overlap_days,
                "is_gap_discrepancy": link.is_gap_discrepancy,
            }
            for link, pred in pred_links
        ],
        "successors": [
            {
                "lineage_id": str(link.id),
                "instrument_id": str(succ.id),
                "instrument_number": succ.instrument_number,
                "status": succ.status.value,
                "relationship_type": link.relationship_type,
                "gap_days": link.gap_days,
                "overlap_days": link.overlap_days,
                "is_gap_discrepancy": link.is_gap_discrepancy,
            }
            for link, succ in succ_links
        ],
    }
