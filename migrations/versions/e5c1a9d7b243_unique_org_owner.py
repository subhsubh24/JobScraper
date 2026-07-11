"""add UNIQUE(owner_id) on organizations (one owned org per user, enforced at the DB)

Closes the concurrent-double-org race: the app-level ``owned_org()`` check in
``org_billing.create_org`` is not serialized, so two parallel ``POST /api/org`` could both
pass it and insert. A DB unique constraint makes the second insert fail loud (the app catches
it and returns 409), mirroring ``uq_org_member_user`` on ``organization_members``.

Forward-only. Pre-launch the table is empty, so no data backfill/dedup is needed; if this ever
runs against data with a duplicate owner it fails loud (correct — the invariant was violated).

Revision ID: e5c1a9d7b243
Revises: b3d9e1f27a04
Create Date: 2026-07-11
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e5c1a9d7b243"
down_revision = "b3d9e1f27a04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table so SQLite (which can't ALTER TABLE ADD CONSTRAINT) recreates the table
    # with the constraint, while Postgres runs a plain ALTER — the portable idiom.
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.create_unique_constraint("uq_org_owner", ["owner_id"])


def downgrade() -> None:
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_constraint("uq_org_owner", type_="unique")
