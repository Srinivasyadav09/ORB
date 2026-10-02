from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

CartQuantity = Annotated[int, Field(strict=True, gt=0)]


class CartItemAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    quantity: CartQuantity


class CartItemQuantityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: CartQuantity


class CartItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    product_image_url: str | None
    unit: str
    unit_price: Decimal
    quantity: int
    available_stock: Decimal
    line_total: Decimal
    is_available: bool
    availability_reason: str | None

    @field_serializer("unit_price", "line_total")
    def serialize_money(self, value: Decimal) -> str:
        return format(value, ".2f")

    @field_serializer("available_stock")
    def serialize_stock(self, value: Decimal) -> str:
        return format(value, ".3f")


class CartResponse(BaseModel):
    id: UUID
    items: list[CartItemResponse]
    item_count: int
    subtotal: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime

    @field_serializer("subtotal", "delivery_fee", "total_amount")
    def serialize_subtotal(self, value: Decimal) -> str:
        return format(value, ".2f")
