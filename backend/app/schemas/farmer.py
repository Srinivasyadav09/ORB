from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.models.farmer import VerificationStatus
from app.schemas.customer import ProfileName, ProfilePhone, normalize_phone


class FarmerResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    phone: str | None
    farm_name: str | None
    farm_location: str
    farm_description: str | None
    farm_image_url: str | None
    verification_status: VerificationStatus
    verification_submitted_at: datetime
    verification_completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PublicFarmerResponse(BaseModel):
    id: UUID
    full_name: str
    farm_name: str | None
    farm_location: str
    farm_description: str | None
    farm_image_url: str | None
    is_verified: bool


class FarmerUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: ProfileName | None = None
    farm_name: Annotated[str | None, Field(min_length=2, max_length=160)] = None
    phone: ProfilePhone | None = None
    farm_location: Annotated[str | None, Field(min_length=2, max_length=300)] = None
    farm_description: Annotated[str | None, Field(max_length=4000)] = None
    farm_image_url: Annotated[str | None, Field(max_length=2048)] = None

    @field_validator(
        "full_name", "farm_name", "farm_location", "farm_description", mode="before"
    )
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, value: object) -> object:
        return normalize_phone(value)

    @field_validator("farm_image_url", mode="before")
    @classmethod
    def trim_url(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one profile field to update")
        for field in ("full_name", "phone", "farm_location"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class AdminFarmerResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    phone: str | None
    farm_name: str | None
    farm_location: str
    farm_description: str | None
    farm_image_url: str | None
    verification_status: VerificationStatus
    verification_submitted_at: datetime
    verification_completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AdminFarmerListResponse(BaseModel):
    items: list[AdminFarmerResponse]
    page: int
    page_size: int
    total: int
    pages: int
