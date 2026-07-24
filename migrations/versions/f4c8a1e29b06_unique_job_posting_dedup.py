"""add UNIQUE(user_id, title, company_name, url) on job_postings (atomic dedup backstop)

Closes the concurrent double-add race on ``create_job``: the app-level idempotency guard in
``asgi.py`` reads (``existing is None``) then INSERTs, and that check is not serialized — two
genuinely-simultaneous identical POSTs can both pass it and both INSERT, double-firing the paid
re-score / free-tier usage-count / analytics side-effects the guard exists to prevent. This DB
unique constraint makes the loser's insert fail loud (IntegrityError, caught in create_job and
recovered as a dedup — returns the existing row) instead of creating a duplicate. Mirrors
``uq_org_owner`` on organizations and ``uq_org_member_user`` on organization_members.

NOTE (NULL semantics): SQL treats NULLs as DISTINCT, so this constraint does NOT deduplicate rows
with a NULL ``url``; those keep relying on the sequential read-guard (which renders ``url IS NULL``
and matches). The concurrent NULL-url double-add is a far narrower residual — the double-submit /
network-retry / offline-replay case that motivates the guard almost always carries a real url.

Forward-only. The read-guard has prevented sequential duplicates since it shipped, and pre-launch
the table holds ~0 real rows, so no backfill/dedup step is needed; if this ever runs against data
that already violates the invariant it fails loud (correct — the invariant was violated), matching
the ``uq_org_owner`` migration's stance.

Revision ID: f4c8a1e29b06
Revises: e5c1a9d7b243
Create Date: 2026-07-24
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f4c8a1e29b06"
down_revision = "e5c1a9d7b243"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table so SQLite (which can't ALTER TABLE ADD CONSTRAINT) recreates the table
    # with the constraint, while Postgres runs a plain ALTER — the portable idiom (same as the
    # uq_org_owner migration).
    with op.batch_alter_table("job_postings") as batch_op:
        batch_op.create_unique_constraint(
            "uq_job_user_title_company_url",
            ["user_id", "title", "company_name", "url"],
        )


def downgrade() -> None:
    with op.batch_alter_table("job_postings") as batch_op:
        batch_op.drop_constraint("uq_job_user_title_company_url", type_="unique")
