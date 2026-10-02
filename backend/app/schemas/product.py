from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.models.farmer import VerificationStatus
from app.models.product import ProductStatus, ProductUnit

ProductName = Annotated[str, Field(min_length=2, max_length=160)]
ProductPrice = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
ProductQuantity = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=3)]
ProductDescription = Annotated[str | None, Field(max_length=4000)]
ImageReference = Annotated[str | None, Field(max_length=2048)]


def validate_image_reference(value: object) -> object:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        return None
    if len(value) > 2048 or any(ord(char) < 32 for char in value):
        raise ValueError("Image reference must be at most 2048 characters")
    parsed = urlsplit(value)
    if parsed.scheme:
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Image reference must use HTTP or HTTPS")
    elif not value.startswith("/") or value.startswith("//"):
        raise ValueError("Image reference must be an HTTP URL or an absolute path")
    return value


class ProductCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ProductName
    description: ProductDescription = None
    category_id: UUID
    price: ProductPrice
    unit: ProductUnit
    available_quantity: ProductQuantity = Decimal("0")
    image_url: ImageReference = None
    status: ProductStatus = ProductStatus.DRAFT

    @field_validator("name", "description", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("image_url", mode="before")
    @classmethod
    def validate_image(cls, value: object) -> object:
        return validate_image_reference(value)

    @field_validator("status")
    @classmethod
    def validate_initial_status(cls, value: ProductStatus) -> ProductStatus:
        if value == ProductStatus.INACTIVE:
            raise ValueError("A new product must start as DRAFT or ACTIVE")
        return value

    @field_validator("description")
    @classmethod
    def empty_description_is_none(cls, value: str | None) -> str | None:
        return value or None


class ProductUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ProductName | None = None
    description: ProductDescription = None
    category_id: UUID | None = None
    price: ProductPrice | None = None
    unit: ProductUnit | None = None
    available_quantity: ProductQuantity | None = None
    image_url: ImageReference = None
    status: ProductStatus | None = None

    @field_validator("name", "description", mode="before")
    @classmethod
    def trim_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("image_url", mode="before")
    @classmethod
    def validate_image(cls, value: object) -> object:
        return validate_image_reference(value)

    @field_validator("description")
    @classmethod
    def empty_description_is_none(cls, value: str | None) -> str | None:
        return value or None

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one product field to update")
        for field in (
            "name",
            "category_id",
            "price",
            "unit",
            "available_quantity",
            "status",
        ):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ProductCategorySummary(BaseModel):
    id: UUID
    name: str


class ProductFarmerSummary(BaseModel):
    id: UUID
    full_name: str
    farm_name: str | None
    farm_location: str
    farm_image_url: str | None
    verification_status: VerificationStatus


class ProductListItem(BaseModel):
    id: UUID
    name: str
    price: Decimal
    unit: ProductUnit
    available_quantity: Decimal
    is_available: bool
    status: ProductStatus
    image_url: str | None
    category: ProductCategorySummary
    farmer: ProductFarmerSummary
    created_at: datetime
    updated_at: datetime

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> str:
        return format(value, ".2f")

    @field_serializer("available_quantity")
    def serialize_quantity(self, value: Decimal) -> str:
        return format(value, ".3f")


class ProductResponse(ProductListItem):
    description: str | None


class ProductDetailResponse(ProductResponse):
    pass


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    page: int
    page_size: int
    total: int
    pages: int
