#!/usr/bin/env python3
"""Read-only DB inspection: compare the live database's tables against the SQLAlchemy
models and print the current alembic_version. Used by the db-stamp workflow to PROVE the
stamped baseline actually matches the schema (a stamp only records a version; it applies no
DDL). Never writes anything."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, inspect, text  # noqa: E402
from src.db.models import Base  # noqa: E402


def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL not set")
    engine = create_engine(url)
    live = set(inspect(engine).get_table_names()) - {"alembic_version"}
    want = set(Base.metadata.tables)
    print("LIVE TABLES :", sorted(live))
    print("MODEL TABLES:", sorted(want))
    print("MISSING in DB:", sorted(want - live))
    print("EXTRA in DB :", sorted(live - want))
    with engine.connect() as conn:
        try:
            version = conn.execute(text("select version_num from alembic_version")).scalar()
        except Exception as exc:  # noqa: BLE001
            version = f"(no alembic_version: {exc})"
    print("alembic_version:", version)
    print("SCHEMA_MATCHES_MODELS:", live == want)


if __name__ == "__main__":
    main()
