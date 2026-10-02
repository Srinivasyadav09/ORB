from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.customer import normalize_phone

AddressName = Annotated[str, Field(min_length=1, max_length=120)]
AddressLine = Annotated[str, Field(min_length=1, max_length=255)]
AddressCityState = Annotated[str, Field(min_length=1, max_length=120)]
AddressPostalCode = Annotated[str, Field(min_length=1, max_length=32)]
AddressCountry = Annotated[str, Field(min_length=1, max_length=120)]
AddressLabel = Annotated[str, Field(min_length=1, max_length=40)]
Latitude = Annotated[Decimal, Field(ge=Decimal("-90"), le=Decimal("90"))]
Longitude = Annotated[Decimal, Field(ge=Decimal("-180"), le=Decimal("180"))]


class AddressFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: AddressName
    phone: Annotated[str, Field(min_length=8, max_length=20)]
    address_line_1: AddressLine
    address_line_2: Annotated[str | None, Field(max_length=255)] = None
    city: AddressCityState
    state: AddressCityState
    postal_code: AddressPostalCode
    country: AddressCountry
    latitude: Latitude | None = None
    longitude: Longitude | None = None
    label: AddressLabel | None = None
    is_default: bool = False

    @field_validator(
        "full_name",
        "address_line_1",
        "address_line_2",
        "city",
        "state",
        "postal_code",
        "country",
        "label",
        mode="before",
    )
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, value: object) -> object:
        return normalize_phone(value)

    @model_validator(mode="after")
    def validate_coordinate_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class AddressCreateRequest(AddressFields):
    pass


class AddressUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: AddressName | None = None
    phone: Annotated[str, Field(min_length=8, max_length=20)] | None = None
    address_line_1: AddressLine | None = None
    address_line_2: Annotated[str | None, Field(max_length=255)] = None
    city: AddressCityState | None = None
    state: AddressCityState | None = None
    postal_code: AddressPostalCode | None = None
    country: AddressCountry | None = None
    latitude: Latitude | None = None
    longitude: Longitude | None = None
    label: AddressLabel | None = None
    is_default: bool | None = None

    @field_validator(
        "full_name",
        "address_line_1",
        "address_line_2",
        "city",
        "state",
        "postal_code",
        "country",
        "label",
        mode="before",
    )
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, value: object) -> object:
        return normalize_phone(value)

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one address field to update")
        for field in (
            "full_name",
            "phone",
            "address_line_1",
            "city",
            "state",
            "postal_code",
            "country",
        ):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        coordinate_fields = {"latitude", "longitude"} & self.model_fields_set
        if coordinate_fields and coordinate_fields != {"latitude", "longitude"}:
            raise ValueError("latitude and longitude must be updated together")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    phone: str
    address_line_1: str
    address_line_2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    latitude: Decimal | None
    longitude: Decimal | None
    label: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime
