from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ProfileName = Annotated[str, Field(min_length=2, max_length=120)]
ProfilePhone = Annotated[str, Field(min_length=8, max_length=20)]


def normalize_phone(value: object) -> object:
    if not isinstance(value, str):
        return value
    value = "".join(char for char in value.strip() if char not in " ()-")
    if value and not value.startswith("+"):
        value = "+" + value
    digits = value[1:] if value.startswith("+") else value
    if not digits.isdigit() or not 8 <= len(digits) <= 15 or digits.startswith("0"):
        raise ValueError("Enter a valid phone number")
    return value


class CustomerResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None
    profile_image_url: str | None
    created_at: datetime
    updated_at: datetime


class CustomerUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: ProfileName | None = None
    phone: ProfilePhone | None = None
    profile_image_url: Annotated[str | None, Field(max_length=2048)] = None

    @field_validator("full_name", mode="before")
    @classmethod
    def trim_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, value: object) -> object:
        return normalize_phone(value)

    @field_validator("profile_image_url", mode="before")
    @classmethod
    def trim_image_url(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_non_null_fields(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one profile field to update")
        for field in ("full_name", "phone"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        if self.full_name is not None and len(self.full_name) < 2:
            raise ValueError("full_name must contain at least 2 characters")
        return self
