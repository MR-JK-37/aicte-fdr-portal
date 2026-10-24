"""Discrepancy API Router (F-08 / SPEC §14.1 / PS Scenario "Discrepancy Identification").

Key invariants:
1. Surfaces rule-detected discrepancies with severity and rule_version.
2. Rule engine NEVER automatically rejects an instrument or labels an institution as fraud.
3. Officers can generate formal ScrutinyObservations (F-09) from discrepancies.
4. Officers can acknowledge discrepancies with audit logging.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal
from app.models.core import Discrepancy, Instrument, ScrutinyObservation
from app.models.enums import BUREAU_SIDE_ROLES, AppRole, ObservationStatus
from app.outbox.producer import enqueue_outbox_event
from app.problem_json import ForbiddenError, NotFoundError
from app.rules.discrepancies import RULE_VERSION, sync_discrepancies

router = APIRouter(prefix="/v1/instruments", tags=["Discrepancies"])


class DiscrepancyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    instrument_id: uuid.UUID
    field: str
    declared_value: str | None
    extracted_value: str | None
    severity: str
    status: str
    created_at: datetime
    rule_version: str = RULE_VERSION


class GenerateObservationRequest(BaseModel):
    observation_text: str | None = None


class AcknowledgeDiscrepancyRequest(BaseModel):
    reason: str = Field(
        min_length=5,
        description="Rationale for acknowledging discrepancy without observation",
    )


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    instrument_id: uuid.UUID
    officer_id: uuid.UUID | None
    observation: str
    status: str
    created_at: datetime


@router.get(
    "/{instrument_id}/discrepancies",
    response_model=list[DiscrepancyResponse],
)
def get_instrument_discrepancies(
    instrument_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[DiscrepancyResponse]:
    """Lists all identified discrepancies for an instrument."""
    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    # Institution user can only see discrepancies for their own institution
    if (
        principal.role in (AppRole.INSTITUTION_SUBMITTER, AppRole.INSTITUTION_VIEWER)
        and principal.institution_id != instrument.institution_id
    ):
        raise ForbiddenError("Cannot view discrepancies for another institution")

    # Sync and fetch discrepancies
    discs = sync_discrepancies(db, instrument)
    db.commit()

    return [DiscrepancyResponse.model_validate(d) for d in discs]


@router.post(
    "/{instrument_id}/discrepancies/evaluate",
    response_model=list[DiscrepancyResponse],
)
def evaluate_discrepancies(
    instrument_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[DiscrepancyResponse]:
    """Forces re-evaluation of discrepancy rules on an instrument.
    CRITICAL: Does NOT change instrument status to REJECTED.
    """
    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    discs = sync_discrepancies(db, instrument)

    append_audit_entry(
        db,
        action="discrepancy.evaluated",
        entity_type="instrument",
        entity_id=str(instrument.id),
        after={"count": len(discs), "rule_version": RULE_VERSION},
        actor_id=str(principal.id),
        institution_id=str(instrument.institution_id),
    )

    db.commit()
    return [DiscrepancyResponse.model_validate(d) for d in discs]


@router.post(
    "/{instrument_id}/discrepancies/{discrepancy_id}/generate-observation",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_observation_from_discrepancy(
    instrument_id: uuid.UUID,
    discrepancy_id: uuid.UUID,
    payload: GenerateObservationRequest | None = None,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> ObservationResponse:
    """Bureau officer converts an identified discrepancy into a formal ScrutinyObservation (F-09).
    Never automatically rejects the instrument; creates a formal deficiency for review.
    """
    if principal.role not in BUREAU_SIDE_ROLES and principal.role != AppRole.ORG_ADMIN:
        raise ForbiddenError("Only bureau officers may generate scrutiny observations")

    instrument = db.execute(
        select(Instrument).where(Instrument.id == instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    discrepancy = db.execute(
        select(Discrepancy).where(
            Discrepancy.id == discrepancy_id,
            Discrepancy.instrument_id == instrument_id,
        )
    ).scalar_one_or_none()
    if not discrepancy:
        raise NotFoundError("Discrepancy", discrepancy_id)

    obs_text = (
        payload.observation_text
        if payload and payload.observation_text
        else (
            f"Discrepancy detected in field '{discrepancy.field}': "
            f"Declared value '{discrepancy.declared_value}' differs from extracted/expected '{discrepancy.extracted_value}' "
            f"(Severity: {discrepancy.severity}). Clarification or updated document required."
        )
    )

    obs_id = uuid.uuid4()
    obs = ScrutinyObservation(
        id=obs_id,
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        officer_id=principal.id,
        observation=obs_text,
        status=ObservationStatus.OPEN.value,
    )
    db.add(obs)

    discrepancy.status = "OBSERVATION_GENERATED"

    append_audit_entry(
        db,
        action="discrepancy.observation_generated",
        entity_type="discrepancy",
        entity_id=str(discrepancy.id),
        after={
            "observation_id": str(obs.id),
            "instrument_id": str(instrument.id),
            "discrepancy_field": discrepancy.field,
            "status": "OBSERVATION_GENERATED",
        },
        actor_id=str(principal.id),
        institution_id=str(instrument.institution_id),
    )

    enqueue_outbox_event(
        db,
        aggregate_type="observation",
        aggregate_id=obs.id,
        event_type="observation.raised",
        payload={
            "observation_id": str(obs.id),
            "instrument_id": str(instrument.id),
            "institution_id": str(instrument.institution_id),
            "source": "discrepancy_engine",
        },
        dedupe_key=f"discrepancy.obs:{obs.id}",
    )

    res = ObservationResponse.model_validate(obs)
    db.commit()
    return res


@router.post(
    "/{instrument_id}/discrepancies/{discrepancy_id}/acknowledge",
    response_model=DiscrepancyResponse,
)
def acknowledge_discrepancy(
    instrument_id: uuid.UUID,
    discrepancy_id: uuid.UUID,
    payload: AcknowledgeDiscrepancyRequest,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> DiscrepancyResponse:
    """Bureau officer acknowledges/dismisses a discrepancy with documented justification."""
    if principal.role not in BUREAU_SIDE_ROLES and principal.role != AppRole.ORG_ADMIN:
        raise ForbiddenError("Only bureau officers may acknowledge discrepancies")

    discrepancy = db.execute(
        select(Discrepancy).where(
            Discrepancy.id == discrepancy_id,
            Discrepancy.instrument_id == instrument_id,
        )
    ).scalar_one_or_none()
    if not discrepancy:
        raise NotFoundError("Discrepancy", discrepancy_id)

    discrepancy.status = "ACKNOWLEDGED"

    append_audit_entry(
        db,
        action="discrepancy.acknowledged",
        entity_type="discrepancy",
        entity_id=str(discrepancy.id),
        after={
            "status": "ACKNOWLEDGED",
            "reason": payload.reason,
            "acknowledged_by": str(principal.id),
        },
        actor_id=str(principal.id),
        institution_id=str(discrepancy.institution_id),
    )

    res = DiscrepancyResponse.model_validate(discrepancy)
    db.commit()
    return res
