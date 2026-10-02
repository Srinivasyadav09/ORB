from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from app.models.farmer import VerificationStatus
from app.models.user import UserRole

Password = Annotated[
    SecretStr,
    Field(min_length=8, max_length=128, json_schema_extra={"format": "password"}),
]


class CustomerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    profile_image_url: str | None = None


class FarmerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    farm_name: str | None = None
    farm_location: str
    farm_description: str | None = None
    farm_image_url: str | None = None
    verification_status: VerificationStatus
    verification_submitted_at: datetime
    verification_completed_at: datetime | None = None


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    phone: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    customer_profile: CustomerProfileResponse | None = None
    farmer_profile: FarmerProfileResponse | None = None


class CustomerRegistrationRequest(BaseModel):
    email: EmailStr
    password: Password
    full_name: Annotated[str, Field(min_length=2, max_length=120)]
    phone: Annotated[str, Field(min_length=8, max_length=20)]

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().casefold() if isinstance(value, str) else value

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value: object) -> object:
        if isinstance(value, str):
            value = "".join(char for char in value.strip() if char not in " ()-")
            if value and value[0] != "+":
                value = "+" + value
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = value[1:] if value.startswith("+") else value
        if not digits.isdigit() or not 8 <= len(digits) <= 15 or digits.startswith("0"):
            raise ValueError("Enter a valid phone number")
        return value

    @field_validator("password")
    @classmethod
    def reject_blank_password(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("Password must not be blank")
        return value


class FarmerRegistrationRequest(CustomerRegistrationRequest):
    farm_name: Annotated[str | None, Field(min_length=2, max_length=160)] = None
    farm_location: Annotated[str, Field(min_length=2, max_length=300)]
    farm_description: Annotated[str | None, Field(max_length=4000)] = None
    farm_image_url: Annotated[str | None, Field(max_length=2048)] = None

    @field_validator("farm_name", "farm_location", "farm_description", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().casefold() if isinstance(value, str) else value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: CurrentUserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: Annotated[str, Field(min_length=1)]


class LogoutResponse(BaseModel):
    message: str
