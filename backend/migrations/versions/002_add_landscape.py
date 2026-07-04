"""add landscape

Revision ID: 002_add_landscape
Revises: 001_initial_schema
Create Date: 2026-07-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_landscape'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add landscape column to transport_records with default "DEFAULT"
    op.add_column(
        'transport_records',
        sa.Column('landscape', sa.String(length=50), nullable=False, server_default='DEFAULT')
    )


def downgrade() -> None:
    op.drop_column('transport_records', 'landscape')
