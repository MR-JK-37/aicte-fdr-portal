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
    # Required only when the account already has TOTP enrolled; checked by the
    # endpoint, not this schema (which account exists isn't known yet here).
    totp_code: str | None = Field(default=None, min_length=6, max_length=6)
    device_label: str | None = Field(default=None, max_length=128)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: UserProfileResponse


class DevAccountOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    role: str
    full_name: str


class DevLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    device_label: str | None = Field(default=None, max_length=128)


class MfaEnrolStartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    secret: str
    provisioning_uri: str


class MfaEnrolConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    secret: str
    totp_code: str = Field(min_length=6, max_length=6)


class MfaEnrolConfirmResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    recovery_codes: list[str]


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
    device_label: str | None = None
    ip_area: str | None = None
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    current: bool = False


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Optional: web clients send the refresh token via the fdr_refresh cookie instead.
    refresh_token: str | None = None


class NavItemOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    label_key: str
    icon_key: str
    route: str
    required_permission: str | None = None


class NavigationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    landing_route: str
    web_sidebar: list[NavItemOut]
    mobile_tabs: list[NavItemOut]


class ProfileCompletionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    label_key: str
    complete: bool
    optional: bool = False


class ProfileCompletionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    percent: int
    items: list[ProfileCompletionItem]


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str | None = Field(default=None, min_length=1, max_length=256)
    designation: str | None = Field(default=None, max_length=128)
    mobile_number: str | None = Field(default=None, max_length=20)
    preferred_language: str | None = Field(default=None, max_length=8)
