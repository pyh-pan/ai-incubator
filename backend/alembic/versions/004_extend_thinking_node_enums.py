"""Extend thinking node enums

Revision ID: 004
Revises: 003
Create Date: 2026-04-26

"""
from typing import Sequence, Union

from alembic import op


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE thinking_node_kind ADD VALUE IF NOT EXISTS 'followup'")
        op.execute("ALTER TYPE thinking_node_status ADD VALUE IF NOT EXISTS 'needs_context'")
        op.execute("ALTER TYPE thinking_node_status ADD VALUE IF NOT EXISTS 'resolved'")


def downgrade() -> None:
    """Downgrade database."""
    # PostgreSQL enum values cannot be removed without rebuilding dependent columns.
    # Leaving the extended values in place is the least risky downgrade behavior.
    pass
