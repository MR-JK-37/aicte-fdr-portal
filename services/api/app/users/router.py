"""Users & Identity Access Management Router (F-01 / F-19 / Exit Gate G-12).

Enforces:
- Maker-checker workflow for role assignments.
- Separation of Duties (SoD): Requester cannot approve their own role assignment;
  nobody can grant themselves a role.
- Step-up verification for privileged role changes.
- Immediate termination of active sessions upon revocation/role change.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.audit import append_audit_entry
from app.auth.deps import get_db, require_permission
from app.auth.security import hash_password, revoke_user_sessions
from app.authz import PermissionVerb, Principal, SeparationOfDutiesError
from app.models.core import AppUser
from app.models.enums import AppRole
from app.models.extensions import (
    RecertificationCampaign,
    RoleAssignmentRequest,
    UserInvitation,
)
from app.problem_json import ForbiddenError, NotFoundError

router = APIRouter(prefix="/v1", tags=["Users & Access (F-01/F-19)"])


# --- Schemas ---


class UserSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    role: AppRole
    institution_id: uuid.UUID | None
    region_id: uuid.UUID | None
    designation: str | None
    mobile_number: str | None
    is_active: bool
    mfa_enrolled: bool
    locked_until: datetime | None
    created_at: datetime


class CreateUserPayload(BaseModel):
    email: str = Field(..., min_length=3, max_length=256)
    full_name: str = Field(..., min_length=2, max_length=128)
    role: AppRole
    institution_id: uuid.UUID | None = None
    region_id: uuid.UUID | None = None
    designation: str | None = None
    mobile_number: str | None = None


class UpdateUserPayload(BaseModel):
    full_name: str | None = None
    designation: str | None = None
    mobile_number: str | None = None
    is_active: bool | None = None


class UserInvitationPayload(BaseModel):
    email: str = Field(..., min_length=3, max_length=256)
    role: AppRole
    institution_id: uuid.UUID | None = None
    region_id: uuid.UUID | None = None


class UserInvitationResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    institution_id: uuid.UUID | None
    status: str
    expires_at: datetime
    created_at: datetime


class RoleAssignmentRequestPayload(BaseModel):
    user_id: uuid.UUID
    requested_role: AppRole
    requested_scope: dict[str, Any] | None = None
    reason: str = Field(..., min_length=10)


class RoleAssignmentRequestResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    requested_role: str
    requested_scope: dict[str, Any] | None
    requested_by: uuid.UUID
    reason: str
    status: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    decision_reason: str | None
    created_at: datetime


class RecertificationCampaignPayload(BaseModel):
    name: str = Field(..., min_length=5)
    due_days: int = Field(30, ge=7, le=90)


class RecertificationCampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    due_date: datetime
    status: str
    created_at: datetime
    completed_at: datetime | None


# --- Endpoints ---


@router.get("/users", response_model=list[UserSummaryResponse])
def list_users(
    role: AppRole | None = Query(None),
    institution_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> list[UserSummaryResponse]:
    """Lists users filtered by institutional scope."""
    stmt = select(AppUser)
    if principal.institution_id:
        stmt = stmt.where(AppUser.institution_id == principal.institution_id)
    elif institution_id:
        stmt = stmt.where(AppUser.institution_id == institution_id)
    if role:
        stmt = stmt.where(AppUser.role == role)

    stmt = stmt.order_by(desc(AppUser.created_at)).limit(limit).offset(offset)
    users = db.execute(stmt).scalars().all()
    return [UserSummaryResponse.model_validate(u) for u in users]


@router.post(
    "/users", response_model=UserSummaryResponse, status_code=status.HTTP_201_CREATED
)
def create_user(
    payload: CreateUserPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> UserSummaryResponse:
    """Creates a new user within principal's administrative boundary."""
    if principal.institution_id and payload.institution_id != principal.institution_id:
        raise ForbiddenError("Cannot create users for another institution")

    existing = db.execute(
        select(AppUser).where(AppUser.email == payload.email.lower().strip())
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists",
        )

    temp_password = secrets.token_urlsafe(16)
    pw_hash = hash_password(temp_password)

    new_id = uuid.uuid4()
    user = AppUser(
        id=new_id,
        keycloak_sub=f"sub-{new_id}",
        email=payload.email.lower().strip(),
        full_name=payload.full_name,
        role=payload.role,
        institution_id=payload.institution_id or principal.institution_id,
        region_id=payload.region_id or principal.region_id,
        designation=payload.designation,
        mobile_number=payload.mobile_number,
        password_hash=pw_hash,
        is_active=True,
    )
    db.add(user)
    db.flush()

    append_audit_entry(
        db,
        action="user.created",
        entity_type="app_user",
        entity_id=str(user.id),
        after={"email": user.email, "role": user.role.value},
        actor_id=str(principal.id),
        institution_id=str(user.institution_id) if user.institution_id else None,
    )
    db.commit()

    return UserSummaryResponse.model_validate(user)


@router.get("/users/{user_id}", response_model=UserSummaryResponse)
def get_user(
    user_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> UserSummaryResponse:
    """Gets user profile details."""
    user = db.get(AppUser, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    if principal.institution_id and user.institution_id != principal.institution_id:
        raise NotFoundError("User", user_id)

    return UserSummaryResponse.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserSummaryResponse)
def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> UserSummaryResponse:
    """Updates user information or deactivates user (terminating sessions immediately)."""
    user = db.get(AppUser, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    if principal.institution_id and user.institution_id != principal.institution_id:
        raise NotFoundError("User", user_id)

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.designation is not None:
        user.designation = payload.designation
    if payload.mobile_number is not None:
        user.mobile_number = payload.mobile_number
    if payload.is_active is not None:
        user.is_active = payload.is_active
        if not payload.is_active:
            # Immediate session revocation on deactivation (MASTER_PROMPT_V2 §7)
            revoke_user_sessions(db, user_id=user.id)

    user.updated_at = datetime.now(UTC)
    db.flush()

    append_audit_entry(
        db,
        action="user.updated",
        entity_type="app_user",
        entity_id=str(user.id),
        after={"is_active": user.is_active},
        actor_id=str(principal.id),
        institution_id=str(user.institution_id) if user.institution_id else None,
    )
    db.commit()

    return UserSummaryResponse.model_validate(user)


@router.post("/users/{user_id}/unlock", status_code=status.HTTP_200_OK)
def unlock_user_account(
    user_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
):
    """Unlocks a locked user account and clears failed login attempts."""
    user = db.get(AppUser, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    if principal.institution_id and user.institution_id != principal.institution_id:
        raise NotFoundError("User", user_id)

    user.locked_until = None
    user.failed_login_attempts = 0
    db.flush()

    append_audit_entry(
        db,
        action="user.unlocked",
        entity_type="app_user",
        entity_id=str(user.id),
        actor_id=str(principal.id),
        institution_id=str(user.institution_id) if user.institution_id else None,
    )
    db.commit()
    return {"status": "unlocked", "user_id": str(user.id)}


# --- Maker-Checker Role Assignment Requests ---


@router.post(
    "/role-assignments/requests",
    response_model=RoleAssignmentRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def request_role_assignment(
    payload: RoleAssignmentRequestPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> RoleAssignmentRequestResponse:
    """Maker initiates a role assignment request (G-12: nobody can grant themselves a role)."""
    # SoD: Nobody can request or grant themselves a role
    if payload.user_id == principal.id:
        raise SeparationOfDutiesError(
            "Cannot initiate a role assignment request for your own account"
        )

    target_user = db.get(AppUser, payload.user_id)
    if not target_user:
        raise NotFoundError("User", payload.user_id)

    req = RoleAssignmentRequest(
        id=uuid.uuid4(),
        user_id=payload.user_id,
        requested_role=payload.requested_role.value,
        requested_scope=payload.requested_scope,
        requested_by=principal.id,
        reason=payload.reason,
        status="PENDING",
    )
    db.add(req)
    db.flush()

    append_audit_entry(
        db,
        action="role_assignment.requested",
        entity_type="role_assignment_request",
        entity_id=str(req.id),
        after={
            "user_id": str(payload.user_id),
            "requested_role": payload.requested_role.value,
        },
        actor_id=str(principal.id),
    )
    db.commit()

    return RoleAssignmentRequestResponse(
        id=req.id,
        user_id=req.user_id,
        requested_role=req.requested_role,
        requested_scope=req.requested_scope,
        requested_by=req.requested_by,
        reason=req.reason,
        status=req.status,
        reviewed_by=req.reviewed_by,
        reviewed_at=req.reviewed_at,
        decision_reason=req.decision_reason,
        created_at=req.created_at,
    )


@router.post(
    "/role-assignments/{request_id}/approve",
    response_model=RoleAssignmentRequestResponse,
)
def approve_role_assignment(
    request_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> RoleAssignmentRequestResponse:
    """Checker approves role assignment (SoD: approver != requester)."""
    req = db.get(RoleAssignmentRequest, request_id)
    if not req:
        raise NotFoundError("RoleAssignmentRequest", request_id)

    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already in {req.status} status",
        )

    # SoD Check: Approver cannot be the requester
    if req.requested_by == principal.id:
        raise SeparationOfDutiesError(
            "Requester cannot approve their own role assignment request"
        )

    # Step-up assurance check
    if not principal.step_up_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "step_up_required",
                "message": "Step-up MFA required to approve role assignment",
            },
        )

    target_user = db.get(AppUser, req.user_id)
    if not target_user:
        raise NotFoundError("User", req.user_id)

    # Apply new role and revoke active sessions
    old_role = target_user.role
    target_user.role = AppRole(req.requested_role)
    target_user.updated_at = datetime.now(UTC)

    # Immediately revoke active sessions so new role takes effect cleanly
    revoke_user_sessions(db, user_id=target_user.id)

    req.status = "APPROVED"
    req.reviewed_by = principal.id
    req.reviewed_at = datetime.now(UTC)
    req.decision_reason = "Approved by authorized security officer"

    append_audit_entry(
        db,
        action="role_assignment.approved",
        entity_type="role_assignment_request",
        entity_id=str(req.id),
        before={
            "role": old_role.value if hasattr(old_role, "value") else str(old_role)
        },
        after={"role": req.requested_role},
        actor_id=str(principal.id),
    )
    db.commit()

    return RoleAssignmentRequestResponse(
        id=req.id,
        user_id=req.user_id,
        requested_role=req.requested_role,
        requested_scope=req.requested_scope,
        requested_by=req.requested_by,
        reason=req.reason,
        status=req.status,
        reviewed_by=req.reviewed_by,
        reviewed_at=req.reviewed_at,
        decision_reason=req.decision_reason,
        created_at=req.created_at,
    )


@router.post(
    "/role-assignments/{request_id}/reject",
    response_model=RoleAssignmentRequestResponse,
)
def reject_role_assignment(
    request_id: uuid.UUID,
    reason: str = Query(..., min_length=5),
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> RoleAssignmentRequestResponse:
    """Checker rejects role assignment."""
    req = db.get(RoleAssignmentRequest, request_id)
    if not req:
        raise NotFoundError("RoleAssignmentRequest", request_id)

    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already in {req.status} status",
        )

    req.status = "REJECTED"
    req.reviewed_by = principal.id
    req.reviewed_at = datetime.now(UTC)
    req.decision_reason = reason

    append_audit_entry(
        db,
        action="role_assignment.rejected",
        entity_type="role_assignment_request",
        entity_id=str(req.id),
        after={"reason": reason},
        actor_id=str(principal.id),
    )
    db.commit()

    return RoleAssignmentRequestResponse(
        id=req.id,
        user_id=req.user_id,
        requested_role=req.requested_role,
        requested_scope=req.requested_scope,
        requested_by=req.requested_by,
        reason=req.reason,
        status=req.status,
        reviewed_by=req.reviewed_by,
        reviewed_at=req.reviewed_at,
        decision_reason=req.decision_reason,
        created_at=req.created_at,
    )


# --- Invitations ---


@router.get("/invitations", response_model=list[UserInvitationResponse])
def list_invitations(
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> list[UserInvitationResponse]:
    """Lists pending user invitations."""
    stmt = select(UserInvitation)
    if principal.institution_id:
        stmt = stmt.where(UserInvitation.institution_id == principal.institution_id)
    stmt = stmt.order_by(desc(UserInvitation.created_at)).limit(50)

    invites = db.execute(stmt).scalars().all()
    return [
        UserInvitationResponse(
            id=i.id,
            email=i.email,
            role=i.role,
            institution_id=i.institution_id,
            status=i.status,
            expires_at=i.expires_at,
            created_at=i.created_at,
        )
        for i in invites
    ]


@router.post(
    "/invitations",
    response_model=UserInvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    payload: UserInvitationPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> UserInvitationResponse:
    """Sends a new role invitation."""
    now = datetime.now(UTC)
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    invite = UserInvitation(
        id=uuid.uuid4(),
        email=payload.email.lower().strip(),
        role=payload.role.value,
        institution_id=payload.institution_id or principal.institution_id,
        region_id=payload.region_id or principal.region_id,
        invited_by=principal.id,
        token_hash=token_hash,
        status="PENDING",
        expires_at=now + timedelta(days=7),
    )
    db.add(invite)
    db.commit()

    return UserInvitationResponse(
        id=invite.id,
        email=invite.email,
        role=invite.role,
        institution_id=invite.institution_id,
        status=invite.status,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
    )


# --- Recertification Campaigns ---


@router.get(
    "/recertification-campaigns", response_model=list[RecertificationCampaignResponse]
)
def list_recertification_campaigns(
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> list[RecertificationCampaignResponse]:
    """Lists periodic access recertification campaigns."""
    stmt = (
        select(RecertificationCampaign)
        .order_by(desc(RecertificationCampaign.created_at))
        .limit(20)
    )
    campaigns = db.execute(stmt).scalars().all()
    return [
        RecertificationCampaignResponse(
            id=c.id,
            name=c.name,
            due_date=c.due_date,
            status=c.status,
            created_at=c.created_at,
            completed_at=c.completed_at,
        )
        for c in campaigns
    ]


@router.post(
    "/recertification-campaigns",
    response_model=RecertificationCampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recertification_campaign(
    payload: RecertificationCampaignPayload,
    principal: Principal = Depends(require_permission(PermissionVerb.MANAGE_ROLES)),
    db: Session = Depends(get_db),
) -> RecertificationCampaignResponse:
    """Launches an access recertification campaign."""
    now = datetime.now(UTC)
    campaign = RecertificationCampaign(
        id=uuid.uuid4(),
        name=payload.name,
        due_date=now + timedelta(days=payload.due_days),
        status="ACTIVE",
        created_by=principal.id,
    )
    db.add(campaign)
    db.commit()

    return RecertificationCampaignResponse(
        id=campaign.id,
        name=campaign.name,
        due_date=campaign.due_date,
        status=campaign.status,
        created_at=campaign.created_at,
        completed_at=campaign.completed_at,
    )


# --- Institution Users Sub-resource ---


@router.get(
    "/institutions/{institution_id}/users", response_model=list[UserSummaryResponse]
)
def get_institution_users(
    institution_id: uuid.UUID,
    principal: Principal = Depends(require_permission(PermissionVerb.VIEW)),
    db: Session = Depends(get_db),
) -> list[UserSummaryResponse]:
    """Gets users belonging to a specific institution."""
    if principal.institution_id and principal.institution_id != institution_id:
        raise ForbiddenError("Cannot view users for another institution")

    stmt = (
        select(AppUser)
        .where(AppUser.institution_id == institution_id)
        .order_by(AppUser.created_at.desc())
    )
    users = db.execute(stmt).scalars().all()
    return [UserSummaryResponse.model_validate(u) for u in users]


@router.post(
    "/institutions/{institution_id}/users",
    response_model=UserSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_institution_user(
    institution_id: uuid.UUID,
    payload: CreateUserPayload,
    principal: Principal = Depends(
        require_permission(PermissionVerb.MANAGE_INSTITUTION_USERS)
    ),
    db: Session = Depends(get_db),
) -> UserSummaryResponse:
    """Enrolls a new user under a specific institution."""
    if principal.institution_id and principal.institution_id != institution_id:
        raise ForbiddenError("Cannot add users for another institution")

    payload_with_inst = CreateUserPayload(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        institution_id=institution_id,
        region_id=payload.region_id,
        designation=payload.designation,
        mobile_number=payload.mobile_number,
    )
    return create_user(payload=payload_with_inst, principal=principal, db=db)
