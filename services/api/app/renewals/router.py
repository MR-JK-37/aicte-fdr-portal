"""Renewal and replacement API router (F-11 / SPEC §6.1)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_current_principal
from app.authz import Principal
from app.db import get_session
from app.models.core import AppUser
from app.renewals.service import (
    LineageCycleError,
    LineageError,
    LineageNotFoundError,
    create_instrument_lineage,
    get_lineage_graph,
)

router = APIRouter(prefix="/v1/instruments", tags=["renewals"])


class LinkLineageRequest(BaseModel):
    predecessor_id: uuid.UUID
    successor_id: uuid.UUID
    relationship_type: str = "RENEWAL"
    policy_allowed_gap_days: int = 0


@router.post("/lineage", status_code=status.HTTP_201_CREATED)
def link_lineage(
    payload: LinkLineageRequest,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        lineage = create_instrument_lineage(
            session,
            payload.predecessor_id,
            payload.successor_id,
            relationship_type=payload.relationship_type,
            policy_allowed_gap_days=payload.policy_allowed_gap_days,
            created_by=user,
        )
        session.commit()
        return {
            "id": str(lineage.id),
            "predecessor_id": str(lineage.predecessor_id),
            "successor_id": str(lineage.successor_id),
            "relationship_type": lineage.relationship_type,
            "gap_days": lineage.gap_days,
            "overlap_days": lineage.overlap_days,
            "is_gap_discrepancy": lineage.is_gap_discrepancy,
        }
    except LineageCycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LineageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LineageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{instrument_id}/lineage")
def get_instrument_lineage(
    instrument_id: uuid.UUID,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        return get_lineage_graph(session, instrument_id)
    except LineageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
