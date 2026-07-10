"""add organizations + organization_members (team-seat B2B2C tier)

Revision ID: b3d9e1f27a04
Revises: a7d3e1f0c92b
Create Date: 2026-07-10 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3d9e1f27a04'
down_revision: Union[str, None] = 'a7d3e1f0c92b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('seats_purchased', sa.Integer(), server_default='0', nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_organizations_owner_id'), 'organizations', ['owner_id'], unique=False)
    op.create_index(
        op.f('ix_organizations_stripe_customer_id'), 'organizations',
        ['stripe_customer_id'], unique=False,
    )
    op.create_index(
        op.f('ix_organizations_stripe_subscription_id'), 'organizations',
        ['stripe_subscription_id'], unique=False,
    )

    op.create_table(
        'organization_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('org_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_org_member_user'),
    )
    op.create_index(
        op.f('ix_organization_members_org_id'), 'organization_members', ['org_id'], unique=False
    )
    op.create_index(
        op.f('ix_organization_members_user_id'), 'organization_members', ['user_id'], unique=False
    )
    op.create_index(
        'ix_org_member_org_active', 'organization_members', ['org_id', 'active'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_org_member_org_active', table_name='organization_members')
    op.drop_index(op.f('ix_organization_members_user_id'), table_name='organization_members')
    op.drop_index(op.f('ix_organization_members_org_id'), table_name='organization_members')
    op.drop_table('organization_members')
    op.drop_index(op.f('ix_organizations_stripe_subscription_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_stripe_customer_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_owner_id'), table_name='organizations')
    op.drop_table('organizations')
