from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.order import OrderStatus, PaymentMethod, PaymentStatus


class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address_id: UUID
    payment_method: PaymentMethod = PaymentMethod.COD


class DeliveryAddressSnapshot(BaseModel):
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


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID | None
    farmer_id: UUID | None
    product_name: str
    product_image_url: str | None
    unit: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    @field_serializer("unit_price", "line_total")
    def serialize_money(self, value: Decimal) -> str:
        return format(value, ".2f")


class OrderListItem(BaseModel):
    id: UUID
    order_number: str
    status: OrderStatus
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    subtotal: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("subtotal", "delivery_fee", "total_amount")
    def serialize_money(self, value: Decimal) -> str:
        return format(value, ".2f")


class OrderResponse(OrderListItem):
    delivery_address: DeliveryAddressSnapshot
    items: list[OrderItemResponse]


class OrderListResponse(BaseModel):
    items: list[OrderListItem]
    page: Annotated[int, Field(ge=1)]
    page_size: Annotated[int, Field(ge=1)]
    total: int
    pages: int
