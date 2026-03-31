"""
Alembic Environment Configuration

Uses shared.db.Base and shared.config.settings as source of truth.
"""

import asyncio
from logging.config import fileConfig
import logging
import os
import sys

from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── PATH SETUP ──
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── CONFIG + MODELS ──
from shared.db import Base
from shared.config import settings

# ── ALEMBIC CONFIG ──
config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")
logger.setLevel(logging.INFO)

logger.info("Alembic env.py booting…")
logger.info("Loaded metadata tables: %s", list(Base.metadata.tables.keys()))

target_metadata = Base.metadata


def _normalize_sync_url(url: str) -> str:
    """Convert async SQLAlchemy URLs to sync equivalents."""
    replacements = {
        "+asyncpg": "",
        "+aiomysql": "+pymysql",
        "+asyncmy": "+pymysql",
    }
    for needle, repl in replacements.items():
        if needle in url:
            url = url.replace(needle, repl)
    return url


def get_database_url(sync: bool = True) -> str:
    """Fetch DB URL from settings and optionally coerce to sync driver."""
    raw_url = str(settings.DATABASE_URL)
    if not raw_url:
        raise RuntimeError("No DATABASE_URL found in settings")
    if sync:
        return _normalize_sync_url(raw_url)
    return raw_url


# Force Alembic config to use SYNC driver
SYNC_DATABASE_URL = get_database_url(sync=True)
config.set_main_option("sqlalchemy.url", SYNC_DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url(sync=True)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create async engine and associate a connection with Alembic."""
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = get_database_url(sync=False)

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    logger.info("Running migrations in ONLINE mode")
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
