"""Add project more_info

Revision ID: 003
Revises: 002
Create Date: 2026-04-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database."""
    op.add_column("projects", sa.Column("more_info", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade database."""
    op.drop_column("projects", "more_info")
