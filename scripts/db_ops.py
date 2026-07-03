#!/usr/bin/env python3
"""On-demand prod DB reconciliation (auto-migrate incident recovery).

MODE env: diagnose (read-only) | upgrade | reconcile. Reads DATABASE_URL.
- diagnose : print alembic_version + missing tables/columns vs the models. Changes nothing.
- upgrade  : `alembic upgrade head`, then diagnose. The clean fix when the DB is genuinely behind.
- reconcile: create_all (missing tables + indexes) + ADD missing columns + create missing indexes
             + `alembic stamp head`, then diagnose. ADDITIVE-ONLY (never drops). Use when a plain
             upgrade would conflict because create_all already made some tables.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, inspect, text  # noqa: E402
from src.db.models import Base  # noqa: E402

MODE = os.getenv("MODE", "diagnose")
_URL = os.environ["DATABASE_URL"]
if _URL.startswith("postgres://"):
    _URL = _URL.replace("postgres://", "postgresql://", 1)


def _scan(engine):
    insp = inspect(engine)
    live_tables = set(insp.get_table_names())
    missing_tables, missing_cols = [], []
    for tname, tbl in Base.metadata.tables.items():
        if tname not in live_tables:
            missing_tables.append(tname)
            continue
        live_cols = {c["name"] for c in insp.get_columns(tname)}
        for col in tbl.columns:
            if col.name not in live_cols:
                missing_cols.append((tname, col))
    return missing_tables, missing_cols


def _alembic(*args):
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=str(ROOT), check=True,
                   env={**os.environ, "DATABASE_URL": _URL})


def _diagnose(engine):
    with engine.connect() as conn:
        try:
            version = conn.execute(text("select version_num from alembic_version")).scalar()
        except Exception as exc:  # noqa: BLE001
            version = f"(no alembic_version: {exc})"
    mt, mc = _scan(engine)
    print("alembic_version:", version)
    print("MISSING TABLES:", mt)
    print("MISSING COLUMNS:", [f"{t}.{c.name}" for t, c in mc])
    return mt, mc


def _reconcile(engine):
    mt, mc = _scan(engine)
    print("before -> missing_tables:", mt, "| missing_cols:", [f"{t}.{c.name}" for t, c in mc])
    Base.metadata.create_all(bind=engine, checkfirst=True)  # missing tables (+ their indexes)
    with engine.begin() as conn:
        for tname, col in mc:
            coltype = col.type.compile(dialect=engine.dialect)
            nullable = "" if col.nullable else " NOT NULL"
            default = ""
            if col.server_default is not None:  # required so a NOT NULL add works on populated rows
                arg = getattr(col.server_default, "arg", None)
                default = f" DEFAULT {getattr(arg, 'text', arg)}"
            conn.execute(text(
                f'ALTER TABLE {tname} ADD COLUMN IF NOT EXISTS "{col.name}" {coltype}{default}{nullable}'))
            print(f"  + column {tname}.{col.name} {coltype}{default}{nullable}")
    for tbl in Base.metadata.tables.values():  # missing indexes (e.g. a new unique column)
        for idx in tbl.indexes:
            try:
                idx.create(bind=engine, checkfirst=True)
            except Exception as exc:  # noqa: BLE001
                print(f"  index {idx.name}: {exc}")
    _alembic("stamp", "head")
    print("stamped head")


def main():
    engine = create_engine(_URL)
    if MODE == "diagnose":
        _diagnose(engine)
    elif MODE == "upgrade":
        _alembic("upgrade", "head")
        print("=== after upgrade ===")
        _diagnose(engine)
    elif MODE == "reconcile":
        _reconcile(engine)
        print("=== after reconcile ===")
        _diagnose(engine)
    else:
        sys.exit(f"unknown MODE {MODE}")


if __name__ == "__main__":
    main()
