"""Policy API router (F-13 / SPEC §2.1-2.3, §21)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_principal
from app.authz import Principal
from app.db import get_session
from app.models.core import AppUser
from app.models.workflow import PolicyVersion
from app.policy.loader import load_policy_drafts
from app.policy.service import (
    MakerCheckerViolation,
    PolicyBlockedError,
    PolicyError,
    PolicyPermissionError,
    StepUpRequiredError,
    approve_policy_version,
)

router = APIRouter(prefix="/v1/policies", tags=["policy"])


class PolicyVersionResponse(BaseModel):
    id: uuid.UUID
    policy_id: str
    document: str
    clause: str | None = None
    source_url: str | None = None
    document_hash: str | None = None
    scope: str | None = None
    status: str
    blocked_reason: str | None = None
    author_id: uuid.UUID | None = None
    approver_id: uuid.UUID | None = None
    step_up_verified: bool
    version_number: int
    changelog: str | None = None
    config_payload: dict[str, Any]

    model_config = {"from_attributes": True}


class PolicyApprovalRequest(BaseModel):
    step_up_token: str | None = None


@router.get("", response_model=list[PolicyVersionResponse])
def list_policies(
    policy_id: str | None = Query(None),
    status: str | None = Query(None),
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    stmt = select(PolicyVersion)
    if policy_id:
        stmt = stmt.where(PolicyVersion.policy_id == policy_id)
    if status:
        stmt = stmt.where(PolicyVersion.status == status)
    stmt = stmt.order_by(PolicyVersion.policy_id, PolicyVersion.version_number.desc())
    return session.execute(stmt).scalars().all()


@router.get("/{policy_version_id}", response_model=PolicyVersionResponse)
def get_policy_detail(
    policy_version_id: uuid.UUID,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    pv = session.get(PolicyVersion, policy_version_id)
    if not pv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy version not found"
        )
    return pv


@router.post("/import-drafts", status_code=status.HTTP_200_OK)
def import_drafts(
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    loaded = load_policy_drafts(session)
    session.commit()
    return {
        "message": f"Successfully loaded {len(loaded)} drafts",
        "count": len(loaded),
    }


@router.post("/{policy_version_id}/approve", response_model=PolicyVersionResponse)
def approve_policy(
    policy_version_id: uuid.UUID,
    payload: PolicyApprovalRequest,
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_current_principal),
):
    try:
        user = session.get(AppUser, principal.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        pv = approve_policy_version(
            session,
            policy_version_id,
            user,
            step_up_token=payload.step_up_token,
        )
        session.commit()
        return pv
    except MakerCheckerViolation as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except StepUpRequiredError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PolicyBlockedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PolicyPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PolicyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
