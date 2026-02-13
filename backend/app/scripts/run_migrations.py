"""
Run Alembic migrations in a deployment-friendly way.

This script is meant to be executed at process start on platforms like Railway,
where you may not have a separate "release" phase.

It uses a Postgres advisory lock to avoid running migrations concurrently when
multiple instances start at the same time.

Usage (from `backend/`):
    python -m app.scripts.run_migrations
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.config import settings

logger = logging.getLogger(__name__)

# 64-bit constant used for advisory lock. Must be stable across deploys.
_LOCK_KEY = 2_026_02_13_07_13  # arbitrary, but constant


def _alembic_config() -> Config:
    """
    Load alembic.ini from the backend folder even if cwd differs.
    """
    backend_dir = Path(__file__).resolve().parents[2]  # .../backend
    alembic_ini = (backend_dir / "alembic.ini").resolve()  # .../backend/alembic.ini

    cfg = Config(str(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg


def main() -> None:
    # Make logs visible during deploy.
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT pg_advisory_lock(:k)"), {"k": _LOCK_KEY})
        except Exception as e:
            # If advisory locks are not available, still try to migrate.
            logger.warning("Could not acquire advisory lock; continuing without it: %s", e)

        try:
            logger.info("Running Alembic migrations (upgrade head)...")
            command.upgrade(_alembic_config(), "head")
            logger.info("Migrations completed.")
        finally:
            try:
                conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _LOCK_KEY})
            except Exception:
                pass


if __name__ == "__main__":
    main()
