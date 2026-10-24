"""Admin API over the feature/connector registry (MASTER_PROMPT §3,
§19 F-19): GET list, GET one, PATCH state, GET health checks for a key.

Permission: MASTER_PROMPT §3 requires `configure_integrations` plus an
independent approver (maker-checker) to set state=`production-enabled`,
and §19 F-19's acceptance criterion is "connector cannot be set
`production-enabled` without evidence + second approver". This router
enforces the evidence half (see `patch_feature_state` below) but NOT the
permission/maker-checker half yet — `app.authz` (owned by the parallel
role/RLS workstream) doesn't exist yet. `_require_configure_integrations`
below is a placeholder that fails CLOSED (raises 403 unconditionally)
until that lands, so every route in this router denies every caller
rather than risk a fail-open gap.

DO NOT expose this router to real traffic until `_require_configure_
integrations` is replaced with a real `authorise()` call — it is wired
into the router purely so every route already depends on it and only
one place needs to change later.

Wiring (do in app/main.py — see this phase's report):
    from app.registry.router import router as registry_router
    app.include_router(registry_router)
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.problem_json import ForbiddenError, NotFoundError, UnprocessableEntityError
from app.registry.models import ConnectorHealthCheck, FeatureRegistryEntry
from app.registry.schemas import (
    ConnectorHealthCheckOut,
    FeatureRegistryOut,
    FeatureRegistryPatch,
)

router = APIRouter(prefix="/v1/admin/registry", tags=["admin-registry"])


def _require_configure_integrations() -> None:
    # TODO: wire to authorise() once available (app.authz, owned by the
    # parallel role/RLS workstream this phase) and enforce maker-checker
    # for state=production-enabled transitions per MASTER_PROMPT §3/§19.
    # Until then this must fail CLOSED, not open: every route in this
    # router denies every caller rather than silently allowing them.
    raise ForbiddenError(
        "registry admin endpoints are not yet authorised (authorise() pending); denying by default"
    )


@router.get("", response_model=list[FeatureRegistryOut])
def list_features(
    session: Session = Depends(get_db),
    _: None = Depends(_require_configure_integrations),
) -> list[FeatureRegistryEntry]:
    return list(
        session.execute(select(FeatureRegistryEntry).order_by(FeatureRegistryEntry.key))
        .scalars()
        .all()
    )


@router.get("/{key}", response_model=FeatureRegistryOut)
def get_feature(
    key: str,
    session: Session = Depends(get_db),
    _: None = Depends(_require_configure_integrations),
) -> FeatureRegistryEntry:
    entry = session.execute(
        select(FeatureRegistryEntry).where(FeatureRegistryEntry.key == key)
    ).scalar_one_or_none()
    if entry is None:
        raise NotFoundError(f"no feature_registry entry for key={key!r}")
    return entry


@router.patch("/{key}", response_model=FeatureRegistryOut)
def patch_feature_state(
    key: str,
    patch: FeatureRegistryPatch,
    session: Session = Depends(get_db),
    _: None = Depends(_require_configure_integrations),
) -> FeatureRegistryEntry:
    entry = session.execute(
        select(FeatureRegistryEntry).where(FeatureRegistryEntry.key == key)
    ).scalar_one_or_none()
    if entry is None:
        raise NotFoundError(f"no feature_registry entry for key={key!r}")

    if patch.state == "production-enabled" and not entry.acceptance_evidence_ref:
        raise UnprocessableEntityError(
            "cannot set state=production-enabled without a non-null acceptance_evidence_ref "
            "already recorded on this feature (MASTER_PROMPT §3)"
        )

    entry.state = patch.state
    entry.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/{key}/health-checks", response_model=list[ConnectorHealthCheckOut])
def list_health_checks(
    key: str,
    session: Session = Depends(get_db),
    _: None = Depends(_require_configure_integrations),
) -> list[ConnectorHealthCheck]:
    return list(
        session.execute(
            select(ConnectorHealthCheck)
            .where(ConnectorHealthCheck.feature_key == key)
            .order_by(ConnectorHealthCheck.checked_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )
