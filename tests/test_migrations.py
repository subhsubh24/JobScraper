"""Migrations are REAL and stay in lock-step with the models (BUILDS != WORKS for schema).

A change that adds/renames a model column but forgets the matching Alembic migration would
deploy a schema that doesn't match the code. These tests fail loud in the gate before that
ships, which is the precondition for auto-applying migrations on deploy safely:
  1. `alembic upgrade head` on a fresh throwaway DB builds EVERY table the models declare.
  2. No structural drift (added/removed table or column) between head and Base.metadata.

Honest scope: verified against sqlite for speed/portability — a fast guard for the common
"forgot the migration" mistake. The staged migrate-on-deploy CI job runs `alembic upgrade
head` against the real Postgres, where cross-dialect specifics (native ENUMs, etc.) apply.
"""
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from src.db.models import Base

ROOT = Path(__file__).resolve().parent.parent


def _alembic_cfg() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    return cfg


def test_upgrade_head_builds_full_schema(tmp_path, monkeypatch):
    db = tmp_path / "mig.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    command.upgrade(_alembic_cfg(), "head")
    eng = create_engine(f"sqlite:///{db}")
    built = set(inspect(eng).get_table_names()) - {"alembic_version"}
    want = set(Base.metadata.tables)
    assert built == want, f"migration head != models. missing={want - built} extra={built - want}"


def test_no_structural_drift_between_head_and_models(tmp_path, monkeypatch):
    db = tmp_path / "drift.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    command.upgrade(_alembic_cfg(), "head")
    eng = create_engine(f"sqlite:///{db}")
    with eng.connect() as conn:
        diffs = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    structural = [
        d for d in diffs
        if (d[0] if isinstance(d, tuple) else d[0][0])
        in ("add_table", "remove_table", "add_column", "remove_column")
    ]
    assert not structural, (
        "Model/migration drift — models changed but no migration was added. Run: "
        f"alembic revision --autogenerate -m '<change>'. Drift: {structural}"
    )
