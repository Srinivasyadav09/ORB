from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.order_item import OrderItem


class OrderStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, Enum):
    COD = "COD"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_number", name="uq_orders_order_number"),
        CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_nonnegative"),
        CheckConstraint("delivery_fee >= 0", name="ck_orders_delivery_fee_nonnegative"),
        CheckConstraint(
            "total_amount = subtotal + delivery_fee",
            name="ck_orders_total_matches_components",
        ),
        Index("ix_orders_customer_created_at", "customer_id", "created_at"),
        Index("ix_orders_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    order_number: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(
            OrderStatus,
            name="order_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=OrderStatus.CONFIRMED,
        server_default=OrderStatus.CONFIRMED.value,
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(
            PaymentMethod,
            name="payment_method",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(
            PaymentStatus,
            name="payment_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(24, 2, asdecimal=True), nullable=False
    )
    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(24, 2, asdecimal=True),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 2, asdecimal=True), nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR", server_default="INR"
    )
    delivery_full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    delivery_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    delivery_address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    delivery_address_line_2: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    delivery_city: Mapped[str] = mapped_column(String(120), nullable=False)
    delivery_state: Mapped[str] = mapped_column(String(120), nullable=False)
    delivery_postal_code: Mapped[str] = mapped_column(String(32), nullable=False)
    delivery_country: Mapped[str] = mapped_column(String(120), nullable=False)
    delivery_latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6, asdecimal=True), nullable=True
    )
    delivery_longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6, asdecimal=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", passive_deletes=True
    )
