"""add referrals (invite loop) + user referral_code/bonus_prep_packs

Revision ID: c3f2a9b41d77
Revises: 982b72c07154
Create Date: 2026-06-30 03:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f2a9b41d77'
down_revision: Union[str, None] = '982b72c07154'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New columns on users. bonus_prep_packs is NOT NULL with a server_default so existing
    # rows backfill to 0 cleanly on the live Postgres.
    op.add_column('users', sa.Column('referral_code', sa.String(length=16), nullable=True))
    op.add_column(
        'users',
        sa.Column('bonus_prep_packs', sa.Integer(), server_default='0', nullable=False),
    )
    op.create_index(
        op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True
    )

    op.create_table(
        'referrals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('referrer_id', sa.String(length=36), nullable=False),
        sa.Column('referred_id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['referred_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_referrals_referrer_id'), 'referrals', ['referrer_id'], unique=False
    )
    op.create_index(
        op.f('ix_referrals_referred_id'), 'referrals', ['referred_id'], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_referrals_referred_id'), table_name='referrals')
    op.drop_index(op.f('ix_referrals_referrer_id'), table_name='referrals')
    op.drop_table('referrals')
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.drop_column('users', 'bonus_prep_packs')
    op.drop_column('users', 'referral_code')
