from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.farmer import VerificationStatus


class FarmerVerificationResponse(BaseModel):
    status: VerificationStatus
    submitted_at: datetime
    completed_at: datetime | None
    status_message: str


class FarmerVerificationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: VerificationStatus


class VerificationUpdatedResponse(BaseModel):
    farmer_id: UUID
    status: VerificationStatus
    submitted_at: datetime
    completed_at: datetime | None
    status_message: str
