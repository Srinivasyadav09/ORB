"""Create the initial empty schema baseline.

Revision ID: 20260923_0001
Revises:
Create Date: 2026-09-23
"""
from typing import Sequence, Union

from alembic import op  # noqa: F401

revision: str = "20260923_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No application tables are part of Phase 2."""
    pass


def downgrade() -> None:
    """There are no application tables to remove in this revision."""
    pass
