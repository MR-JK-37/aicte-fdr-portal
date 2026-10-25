"""Search & Saved Views Router (F-17 / Exit Gate G-15).

Features:
- GET /v1/search: Scope-isolated universal search across instruments and observations.
  - Sensitive identifiers (FDR numbers) searched solely via deterministic blind index (HMAC-SHA256).
  - Property invariant: Never returns rows outside the authenticated principal's institutional scope.
  - Cursor pagination and result limiting.
- Saved Views CRUD: Manage personalized search presets and filtered views.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, desc, or_, select
from sqlalchemy.orm import Session

from app.auth.deps import get_db, require_permission
from app.authz import PermissionVerb, Principal, mask_identifier
from app.config import settings
from app.models.core import Instrument, ScrutinyObservation
from app.models.extensions import SavedView
from app.problem_json import NotFoundError

router = APIRouter(prefix="/v1", tags=["Search & Views (F-17)"])


def compute_blind_index(val: str) -> str:
    key = settings.jwt_secret.encode("utf-8")
    return hmac.new(
        key, val.strip().upper().encode("utf-8"), hashlib.sha256
    ).hexdigest()


# --- Schemas ---


class SearchResultItem(BaseModel):
    id: str
    entity_type: str  # instrument, observation
    title: str
    subtitle: str | None
    reference_id: str
    status: str
    deep_link: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    total_matches: int


class SavedViewPayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    entity_type: str = Field(default="instrument")
    filter_criteria: dict[str, Any] = Field(default_factory=dict)
    is_pinned: bool = False


class SavedViewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    entity_type: str
    filter_criteria: dict[str, Any]
    is_pinned: bool
    created_at: datetime
    updated_at: datetime


# --- Endpoints ---


@router.get("/search", response_model=SearchResponse)
def search_scoped_records(
    q: str = Query(
        ..., min_length=1, max_length=128, description="Search query string"
    ),
    limit: int = Query(25, ge=1, le=100),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Universal scoped search. Identifier search executed via blind index only (Exit Gate G-15)."""
    trimmed = q.strip()
    blind_idx = compute_blind_index(trimmed)

    results: list[SearchResultItem] = []

    # 1. Search Instruments
    inst_stmt = select(Instrument)
    # Scope filter (CRITICAL for G-15 property: never returns out-of-scope rows)
    if principal.institution_id:
        inst_stmt = inst_stmt.where(
            Instrument.institution_id == principal.institution_id
        )

    # Match by blind index or status
    inst_stmt = inst_stmt.where(
        or_(
            Instrument.blind_index == blind_idx,
            Instrument.instrument_number.ilike(f"%{trimmed}%"),
            Instrument.status.cast(String).ilike(f"%{trimmed}%"),
        )
    ).limit(limit)

    instruments = db.execute(inst_stmt).scalars().all()
    for inst in instruments:
        results.append(
            SearchResultItem(
                id=str(inst.id),
                entity_type="instrument",
                title=f"FDR {mask_identifier(inst.instrument_number)}",
                subtitle=f"Status: {inst.status.value if hasattr(inst.status, 'value') else str(inst.status)} · Amount: ₹{inst.amount:,.2f}",
                reference_id=mask_identifier(inst.instrument_number),
                status=inst.status.value
                if hasattr(inst.status, "value")
                else str(inst.status),
                deep_link=f"/instruments/{inst.id}",
            )
        )

    # 2. Search Observations
    obs_stmt = select(ScrutinyObservation)
    if principal.institution_id:
        obs_stmt = obs_stmt.join(
            Instrument, ScrutinyObservation.instrument_id == Instrument.id
        ).where(Instrument.institution_id == principal.institution_id)

    obs_stmt = obs_stmt.where(
        or_(
            ScrutinyObservation.observation.ilike(f"%{trimmed}%"),
            ScrutinyObservation.status.ilike(f"%{trimmed}%"),
        )
    ).limit(limit)

    observations = db.execute(obs_stmt).scalars().all()
    for obs in observations:
        results.append(
            SearchResultItem(
                id=str(obs.id),
                entity_type="observation",
                title=f"Observation: {obs.observation[:40]}...",
                subtitle=f"Status: {obs.status}",
                reference_id=obs.id.hex[:8],
                status=obs.status,
                deep_link=f"/observations/{obs.id}",
            )
        )

    return SearchResponse(
        query=q,
        results=results[:limit],
        total_matches=len(results),
    )


# --- Saved Views CRUD ---


@router.get("/saved-views", response_model=list[SavedViewResponse])
def list_saved_views(
    entity_type: str | None = Query(None),
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[SavedViewResponse]:
    """Lists saved views created by the current user."""
    stmt = select(SavedView).where(SavedView.user_id == principal.id)
    if entity_type:
        stmt = stmt.where(SavedView.entity_type == entity_type)
    stmt = stmt.order_by(desc(SavedView.is_pinned), desc(SavedView.updated_at))

    views = db.execute(stmt).scalars().all()
    return [SavedViewResponse.model_validate(v) for v in views]


@router.post(
    "/saved-views",
    response_model=SavedViewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_view(
    payload: SavedViewPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> SavedViewResponse:
    """Creates a new personalized saved view preset."""
    view = SavedView(
        id=uuid.uuid4(),
        user_id=principal.id,
        name=payload.name,
        entity_type=payload.entity_type,
        filter_criteria=payload.filter_criteria,
        is_pinned=payload.is_pinned,
    )
    db.add(view)
    db.commit()
    return SavedViewResponse.model_validate(view)


@router.get("/saved-views/{view_id}", response_model=SavedViewResponse)
def get_saved_view(
    view_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> SavedViewResponse:
    """Gets a specific saved view."""
    view = db.get(SavedView, view_id)
    if not view or view.user_id != principal.id:
        raise NotFoundError("SavedView", view_id)
    return SavedViewResponse.model_validate(view)


@router.patch("/saved-views/{view_id}", response_model=SavedViewResponse)
def update_saved_view(
    view_id: uuid.UUID,
    payload: SavedViewPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> SavedViewResponse:
    """Updates an existing saved view."""
    view = db.get(SavedView, view_id)
    if not view or view.user_id != principal.id:
        raise NotFoundError("SavedView", view_id)

    view.name = payload.name
    view.entity_type = payload.entity_type
    view.filter_criteria = payload.filter_criteria
    view.is_pinned = payload.is_pinned
    view.updated_at = datetime.now(UTC)

    db.commit()
    return SavedViewResponse.model_validate(view)


@router.delete("/saved-views/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_view(
    view_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
):
    """Deletes a saved view."""
    view = db.get(SavedView, view_id)
    if not view or view.user_id != principal.id:
        raise NotFoundError("SavedView", view_id)
    db.delete(view)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
