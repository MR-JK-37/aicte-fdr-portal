from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sub: str
    user_id: str
    email: str
    role: str
    institution_id: str | None = None
    exp: int


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileResponse


class StepUpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    otp_code: str = Field(min_length=6, max_length=6, description="6-digit TOTP code")


class StepUpResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    step_up_valid_until: datetime
    message: str


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    email: str
    full_name: str
    role: str
    institution_id: str | None = None
    region_id: str | None = None
    mfa_enrolled: bool
    step_up_valid: bool
    step_up_valid_until: datetime | None = None
    delegation_limit: Decimal | None = None


class UserPermissionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str
    permissions: list[str]


class SessionInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    device: str
    ip_address: str
    created_at: datetime
    current: bool = False
