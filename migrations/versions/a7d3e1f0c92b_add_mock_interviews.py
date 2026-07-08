"""add mock_interviews (interview coaching — the north-star pillar, ROADMAP Track A surface 3)

Revision ID: a7d3e1f0c92b
Revises: f1a2b3c4d5e6
Create Date: 2026-07-08 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7d3e1f0c92b'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mock_interviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('questions', sa.JSON(), nullable=False),
        sa.Column('answers', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['job_id'], ['job_postings.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_mock_interviews_user_id'), 'mock_interviews', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_mock_interviews_job_id'), 'mock_interviews', ['job_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_mock_interviews_job_id'), table_name='mock_interviews')
    op.drop_index(op.f('ix_mock_interviews_user_id'), table_name='mock_interviews')
    op.drop_table('mock_interviews')
