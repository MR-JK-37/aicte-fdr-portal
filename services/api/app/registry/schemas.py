import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

FeatureState = Literal["disabled", "sandbox-only", "production-enabled", "degraded"]


class FeatureRegistryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    key: str
    state: FeatureState
    description: str
    acceptance_evidence_ref: str | None
    updated_by: uuid.UUID | None
    updated_at: datetime


class FeatureRegistryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: FeatureState


class ConnectorHealthCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    feature_key: str
    checked_at: datetime
    status: str
    detail: dict | None
