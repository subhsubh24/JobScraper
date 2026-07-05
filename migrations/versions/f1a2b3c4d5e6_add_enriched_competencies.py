"""add enriched_competencies (Track A profile enrichment from linked public sources)

Revision ID: f1a2b3c4d5e6
Revises: d4e7a1c9b8f2
Create Date: 2026-07-05 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'd4e7a1c9b8f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'enriched_competencies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('skill', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=30), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=False),
        sa.Column('evidence', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id', 'skill', 'source_type', name='uq_enriched_user_skill_source'
        ),
    )
    op.create_index(
        op.f('ix_enriched_competencies_user_id'),
        'enriched_competencies',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_enriched_competencies_user_id'), table_name='enriched_competencies'
    )
    op.drop_table('enriched_competencies')
