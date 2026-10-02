"""Add customer orders and immutable checkout snapshots.

Revision ID: 20260924_0006
Revises: 20260924_0005
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260924_0006"
down_revision: Union[str, None] = "20260924_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

order_status = postgresql.ENUM(
    "CONFIRMED",
    "PROCESSING",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
    name="order_status",
    create_type=False,
)
payment_method = postgresql.ENUM("COD", name="payment_method", create_type=False)
payment_status = postgresql.ENUM("PENDING", name="payment_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    order_status.create(bind, checkfirst=True)
    payment_method.create(bind, checkfirst=True)
    payment_status.create(bind, checkfirst=True)

    op.create_table(
        "orders",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("status", order_status, server_default="CONFIRMED", nullable=False),
        sa.Column("payment_method", payment_method, nullable=False),
        sa.Column(
            "payment_status", payment_status, server_default="PENDING", nullable=False
        ),
        sa.Column("subtotal", sa.Numeric(precision=24, scale=2), nullable=False),
        sa.Column(
            "delivery_fee",
            sa.Numeric(precision=24, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("total_amount", sa.Numeric(precision=24, scale=2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), server_default="INR", nullable=False
        ),
        sa.Column("delivery_full_name", sa.String(length=120), nullable=False),
        sa.Column("delivery_phone", sa.String(length=20), nullable=False),
        sa.Column("delivery_address_line_1", sa.String(length=255), nullable=False),
        sa.Column("delivery_address_line_2", sa.String(length=255), nullable=True),
        sa.Column("delivery_city", sa.String(length=120), nullable=False),
        sa.Column("delivery_state", sa.String(length=120), nullable=False),
        sa.Column("delivery_postal_code", sa.String(length=32), nullable=False),
        sa.Column("delivery_country", sa.String(length=120), nullable=False),
        sa.Column("delivery_latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "delivery_longitude", sa.Numeric(precision=9, scale=6), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("subtotal >= 0", name="ck_orders_subtotal_nonnegative"),
        sa.CheckConstraint(
            "delivery_fee >= 0", name="ck_orders_delivery_fee_nonnegative"
        ),
        sa.CheckConstraint(
            "total_amount = subtotal + delivery_fee",
            name="ck_orders_total_matches_components",
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("order_number", name="uq_orders_order_number"),
    )
    op.create_index(
        "ix_orders_customer_created_at", "orders", ["customer_id", "created_at"]
    )
    op.create_index("ix_orders_status", "orders", ["status"])

    op.create_table(
        "order_items",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_name", sa.String(length=160), nullable=False),
        sa.Column("product_image_url", sa.String(length=2048), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=24, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price > 0", name="ck_order_items_price_positive"),
        sa.CheckConstraint(
            "line_total = unit_price * quantity",
            name="ck_order_items_total_matches_quantity",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_order_items_product_id", table_name="order_items")
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_customer_created_at", table_name="orders")
    op.drop_table("orders")
    payment_status.drop(op.get_bind(), checkfirst=True)
    payment_method.drop(op.get_bind(), checkfirst=True)
    order_status.drop(op.get_bind(), checkfirst=True)
