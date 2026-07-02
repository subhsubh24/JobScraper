"""add users.ai_consent_at (third-party-AI consent — Apple 5.1.2(i))

Revision ID: d4e7a1c9b8f2
Revises: b2c8d4e6f1a5
Create Date: 2026-07-02 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e7a1c9b8f2'
down_revision: Union[str, None] = 'b2c8d4e6f1a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable, no server_default: existing rows become NULL = "never consented", which is
    # the safe default — the app will not send their data to the third-party AI until they
    # explicitly opt in.
    op.add_column('users', sa.Column('ai_consent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'ai_consent_at')
