#!/usr/bin/env python3
"""One-shot schema creation. Run once against your production DATABASE_URL.

    DATABASE_URL='postgresql://...' python scripts/init_db.py

Creates all tables (idempotent). The API also auto-creates on cold start when
AUTO_CREATE_TABLES=1 (default), so this script is mainly for explicit control or when
you disable auto-create in favor of alembic migrations.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import DATABASE_URL, engine  # noqa: E402
from src.db.models import Base  # noqa: E402


def main() -> None:
    Base.metadata.create_all(bind=engine)
    target = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
    print(f"Schema created/verified on {target}")


if __name__ == "__main__":
    main()
