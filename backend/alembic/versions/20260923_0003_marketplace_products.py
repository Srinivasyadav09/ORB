"""Add product marketplace and category catalog.

Revision ID: 20260923_0003
Revises: 20260923_0002
Create Date: 2026-09-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260923_0003"
down_revision: Union[str, None] = "20260923_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

product_status = postgresql.ENUM("DRAFT", "ACTIVE", "INACTIVE", name="product_status", create_type=False)
product_unit = postgresql.ENUM(
    "kg", "g", "bunch", "piece", "dozen", "litre", name="product_unit", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    product_status.create(bind, checkfirst=True)
    product_unit.create(bind, checkfirst=True)

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("uq_categories_name_lower", "categories", [sa.text("lower(name)")], unique=True)
    op.create_index(
        "ix_categories_name_trgm",
        "categories",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("farmer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("unit", product_unit, nullable=False),
        sa.Column("available_quantity", sa.Numeric(precision=12, scale=3), nullable=False, server_default="0"),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("status", product_status, nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("price > 0", name="ck_products_price_positive"),
        sa.CheckConstraint("available_quantity >= 0", name="ck_products_quantity_nonnegative"),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_products_farmer_id", "products", ["farmer_id"])
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_status", "products", ["status"])
    op.create_index("ix_products_created_at", "products", ["created_at"])
    op.create_index("ix_products_price", "products", ["price"])
    op.create_index(
        "ix_products_name_trgm",
        "products",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_products_description_trgm",
        "products",
        ["description"],
        postgresql_using="gin",
        postgresql_ops={"description": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_products_description_trgm", table_name="products")
    op.drop_index("ix_products_name_trgm", table_name="products")
    op.drop_index("ix_products_price", table_name="products")
    op.drop_index("ix_products_created_at", table_name="products")
    op.drop_index("ix_products_status", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_index("ix_products_farmer_id", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_categories_name_trgm", table_name="categories")
    op.drop_index("uq_categories_name_lower", table_name="categories")
    op.drop_table("categories")
    product_unit.drop(op.get_bind(), checkfirst=True)
    product_status.drop(op.get_bind(), checkfirst=True)
