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
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.farmer import Farmer


class ProductStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ProductUnit(str, Enum):
    KG = "kg"
    G = "g"
    BUNCH = "bunch"
    PIECE = "piece"
    DOZEN = "dozen"
    LITRE = "litre"


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_products_price_positive"),
        CheckConstraint(
            "available_quantity >= 0", name="ck_products_quantity_nonnegative"
        ),
        Index("ix_products_farmer_id", "farmer_id"),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_status", "status"),
        Index("ix_products_created_at", "created_at"),
        Index("ix_products_price", "price"),
        Index(
            "ix_products_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "ix_products_description_trgm",
            "description",
            postgresql_using="gin",
            postgresql_ops={"description": "gin_trgm_ops"},
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    farmer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), nullable=False
    )
    unit: Mapped[ProductUnit] = mapped_column(
        SAEnum(
            ProductUnit,
            name="product_unit",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    available_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3, asdecimal=True), nullable=False, default=0
    )
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[ProductStatus] = mapped_column(
        SAEnum(
            ProductStatus,
            name="product_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ProductStatus.DRAFT,
        server_default=ProductStatus.DRAFT.value,
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

    farmer: Mapped["Farmer"] = relationship()
    category: Mapped["Category"] = relationship(back_populates="products")

    @property
    def is_available(self) -> bool:
        return self.status == ProductStatus.ACTIVE and self.available_quantity > 0
