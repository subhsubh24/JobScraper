"""add aggregate_events (privacy-safe aggregate product analytics — counts only)

Revision ID: b2c8d4e6f1a5
Revises: a1b7c2f9e0d3
Create Date: 2026-07-01 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c8d4e6f1a5'
down_revision: Union[str, None] = 'a1b7c2f9e0d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'aggregate_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_type', 'event_date', name='uq_aggregate_event_day'),
    )


def downgrade() -> None:
    op.drop_table('aggregate_events')
