"""Observations & Casework Router (F-09 / F-25 / SPEC §6.3)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal
from app.lifecycle import apply_observation_transition
from app.models.core import Instrument, ScrutinyObservation
from app.models.enums import ObservationStatus
from app.models.workflow import CaseComment
from app.outbox.producer import enqueue_outbox_event
from app.problem_json import ForbiddenError, NotFoundError

router = APIRouter(prefix="/v1", tags=["Observations & Casework"])


# --- Schemas ---
class CreateObservationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: uuid.UUID
    observation: str = Field(..., min_length=5, max_length=2048)


class RespondObservationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    response_text: str = Field(..., min_length=5, max_length=2048)
    attachment_doc_id: uuid.UUID | None = None


class ResolveObservationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    resolution_code: str = Field(..., min_length=3, max_length=64)
    reason: str = Field(..., min_length=5, max_length=1024)


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    instrument_id: uuid.UUID
    officer_id: uuid.UUID | None
    observation: str
    status: str
    created_at: datetime


class CreateCommentRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    entity_type: str = Field(default="instrument", max_length=64)
    comment: str = Field(..., min_length=1, max_length=4096)
    is_internal: bool = False


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    entity_type: str
    author_id: uuid.UUID
    institution_id: uuid.UUID | None
    comment: str
    is_internal: bool
    created_at: datetime


# --- Observation Endpoints ---
@router.post(
    "/observations",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def raise_observation(
    payload: CreateObservationRequest,
    principal: Principal = Depends(
        require_permission(PermissionVerb.RAISE_OBSERVATION)
    ),
    db: Session = Depends(get_db),
) -> ObservationResponse:
    """Scrutiny / Regional officer raises an observation on an instrument (F-09)."""
    instrument = db.execute(
        select(Instrument).where(Instrument.id == payload.instrument_id)
    ).scalar_one_or_none()
    if not instrument:
        raise NotFoundError("Instrument", payload.instrument_id)

    obs = ScrutinyObservation(
        id=uuid.uuid4(),
        institution_id=instrument.institution_id,
        instrument_id=instrument.id,
        officer_id=principal.id,
        observation=payload.observation,
        status=ObservationStatus.OPEN.value,
    )
    db.add(obs)
    db.flush()

    append_audit_entry(
        db,
        action="observation.raised",
        entity_type="observation",
        entity_id=str(obs.id),
        after={
            "status": ObservationStatus.OPEN.value,
            "instrument_id": str(instrument.id),
            "observation": payload.observation,
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
        },
        dedupe_key=f"observation.raised:{obs.id}",
    )

    res = ObservationResponse.model_validate(obs)
    db.commit()
    return res


@router.get("/observations", response_model=list[ObservationResponse])
def list_observations(
    instrument_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[ObservationResponse]:
    stmt = select(ScrutinyObservation)
    if instrument_id:
        stmt = stmt.where(ScrutinyObservation.instrument_id == instrument_id)
    if status_filter:
        stmt = stmt.where(ScrutinyObservation.status == status_filter.upper())
    stmt = stmt.order_by(desc(ScrutinyObservation.created_at))
    return list(db.execute(stmt).scalars().all())


@router.get("/observations/{observation_id}", response_model=ObservationResponse)
def get_observation(
    observation_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> ObservationResponse:
    obs = db.execute(
        select(ScrutinyObservation).where(ScrutinyObservation.id == observation_id)
    ).scalar_one_or_none()
    if not obs:
        raise NotFoundError("ScrutinyObservation", observation_id)
    return obs


@router.post(
    "/observations/{observation_id}/send-to-institution",
    response_model=ObservationResponse,
)
def send_observation_to_institution(
    observation_id: uuid.UUID,
    principal: Principal = Depends(
        require_permission(PermissionVerb.RAISE_OBSERVATION)
    ),
    db: Session = Depends(get_db),
) -> ObservationResponse:
    """Transitions observation OPEN -> AWAITING_INSTITUTION."""
    obs = db.execute(
        select(ScrutinyObservation).where(ScrutinyObservation.id == observation_id)
    ).scalar_one_or_none()
    if not obs:
        raise NotFoundError("ScrutinyObservation", observation_id)

    role_str = (
        principal.role.value
        if hasattr(principal.role, "value")
        else str(principal.role)
    )
    apply_observation_transition(
        db,
        obs,
        ObservationStatus.AWAITING_INSTITUTION,
        actor_role=role_str,
        actor_id=str(principal.id),
        reason="Observation dispatched to institution for clarification/compliance",
        reason_code="DISPATCH_TO_INSTITUTION",
    )
    res = ObservationResponse.model_validate(obs)
    db.commit()
    return res


@router.post(
    "/observations/{observation_id}/respond", response_model=ObservationResponse
)
def respond_to_observation(
    observation_id: uuid.UUID,
    payload: RespondObservationRequest,
    principal: Principal = Depends(
        require_permission(PermissionVerb.RESPOND_OBSERVATION)
    ),
    db: Session = Depends(get_db),
) -> ObservationResponse:
    """Institution responds to observation (AWAITING_INSTITUTION -> RESPONSE_RECEIVED)."""
    obs = db.execute(
        select(ScrutinyObservation).where(ScrutinyObservation.id == observation_id)
    ).scalar_one_or_none()
    if not obs:
        raise NotFoundError("ScrutinyObservation", observation_id)

    # Institution scope check
    if principal.institution_id and principal.institution_id != obs.institution_id:
        raise ForbiddenError("Cannot respond to another institution's observation")

    # Save response as a case comment
    comment = CaseComment(
        id=uuid.uuid4(),
        case_id=obs.instrument_id,
        entity_type="observation",
        author_id=principal.id,
        institution_id=obs.institution_id,
        comment=payload.response_text,
        is_internal=False,
    )
    db.add(comment)

    role_str = (
        principal.role.value
        if hasattr(principal.role, "value")
        else str(principal.role)
    )
    apply_observation_transition(
        db,
        obs,
        ObservationStatus.RESPONSE_RECEIVED,
        actor_role=role_str,
        actor_id=str(principal.id),
        reason=payload.response_text,
        reason_code="INSTITUTION_RESPONSE",
    )

    res = ObservationResponse.model_validate(obs)
    db.commit()
    return res


@router.post(
    "/observations/{observation_id}/resolve", response_model=ObservationResponse
)
def resolve_observation(
    observation_id: uuid.UUID,
    payload: ResolveObservationRequest,
    principal: Principal = Depends(
        require_permission(PermissionVerb.RAISE_OBSERVATION)
    ),
    db: Session = Depends(get_db),
) -> ObservationResponse:
    """Officer resolves observation (UNDER_REVIEW or RESPONSE_RECEIVED -> RESOLVED)."""
    obs = db.execute(
        select(ScrutinyObservation).where(ScrutinyObservation.id == observation_id)
    ).scalar_one_or_none()
    if not obs:
        raise NotFoundError("ScrutinyObservation", observation_id)

    role_str = (
        principal.role.value
        if hasattr(principal.role, "value")
        else str(principal.role)
    )

    # Move to UNDER_REVIEW first if in RESPONSE_RECEIVED
    if obs.status == ObservationStatus.RESPONSE_RECEIVED.value:
        apply_observation_transition(
            db,
            obs,
            ObservationStatus.UNDER_REVIEW,
            actor_role=role_str,
            actor_id=str(principal.id),
            reason="Beginning review of institution response",
            reason_code="BEGIN_REVIEW",
        )

    apply_observation_transition(
        db,
        obs,
        ObservationStatus.RESOLVED,
        actor_role=role_str,
        actor_id=str(principal.id),
        reason=payload.reason,
        reason_code=payload.resolution_code,
    )

    res = ObservationResponse.model_validate(obs)
    db.commit()
    return res


# --- Casework Comments (F-25: Internal Notes vs Institution-Visible) ---
@router.post(
    "/cases/{case_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_case_comment(
    case_id: uuid.UUID,
    payload: CreateCommentRequest,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> CommentResponse:
    """Posts a casework comment.
    Bureau officers can set is_internal=True.
    Institution users can ONLY post is_internal=False.
    """
    # Guard: institution users cannot post internal comments
    is_internal = payload.is_internal
    if principal.institution_id and is_internal:
        raise ForbiddenError("Institution users cannot create internal staff notes")

    # Inherit institution_id from case entity if bureau officer
    inst_id = principal.institution_id
    if not inst_id:
        inst = db.execute(
            select(Instrument).where(Instrument.id == case_id)
        ).scalar_one_or_none()
        if inst:
            inst_id = inst.institution_id
        else:
            obs = db.execute(
                select(ScrutinyObservation).where(ScrutinyObservation.id == case_id)
            ).scalar_one_or_none()
            if obs:
                inst_id = obs.institution_id

    comment = CaseComment(
        id=uuid.uuid4(),
        case_id=case_id,
        entity_type=payload.entity_type,
        author_id=principal.id,
        institution_id=inst_id,
        comment=payload.comment,
        is_internal=is_internal,
    )
    db.add(comment)
    db.flush()

    append_audit_entry(
        db,
        action="case.comment_added",
        entity_type="case",
        entity_id=str(case_id),
        after={
            "comment_id": str(comment.id),
            "is_internal": is_internal,
            "entity_type": payload.entity_type,
        },
        actor_id=str(principal.id),
        institution_id=str(principal.institution_id)
        if principal.institution_id
        else None,
    )

    res = CommentResponse.model_validate(comment)
    db.commit()
    return res


@router.get("/cases/{case_id}/comments", response_model=list[CommentResponse])
def get_case_comments(
    case_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[CommentResponse]:
    """Retrieves casework comments.
    Enforces that institution users NEVER receive internal comments (is_internal=True).
    Bureau roles see both internal notes and institution-visible comments.
    """
    stmt = select(CaseComment).where(CaseComment.case_id == case_id)

    # Extra defense-in-depth on top of DB RLS
    if principal.institution_id:
        stmt = stmt.where(CaseComment.is_internal.is_(False))

    stmt = stmt.order_by(CaseComment.created_at.asc())
    comments = db.execute(stmt).scalars().all()
    return list(comments)
