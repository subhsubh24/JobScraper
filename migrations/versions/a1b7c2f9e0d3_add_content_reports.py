"""add content_reports (user report/flag of AI-generated content)

Revision ID: a1b7c2f9e0d3
Revises: 993d75032689
Create Date: 2026-07-01 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b7c2f9e0d3'
down_revision: Union[str, None] = '993d75032689'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'content_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('content_ref', sa.String(length=64), nullable=True),
        sa.Column('content_excerpt', sa.Text(), nullable=True),
        sa.Column('reason', sa.String(length=30), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='open', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_content_reports_user_id'), 'content_reports', ['user_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_content_reports_user_id'), table_name='content_reports')
    op.drop_table('content_reports')
