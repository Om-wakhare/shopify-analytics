"""
Alembic environment — supports both offline (SQL generation) and
online (direct DB) migration modes.

Uses the sync psycopg2 driver for migrations (Alembic is synchronous).
The app runtime uses asyncpg; we swap the driver scheme here only.
"""
import os
import re
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# Load .env before importing app models (which trigger config validation)
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

# Import all models so Alembic's autogenerate can see them
from app.models.db_models import Base  # noqa: F401  (registers all tables)

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_url(async_url: str) -> str:
    return re.sub(r"postgresql\+asyncpg", "postgresql+psycopg2", async_url)


def _get_url() -> str:
    raw = os.environ.get("DATABASE_URL", "")
    return _sync_url(raw)


def run_migrations_offline() -> None:
    """Generate SQL scripts without a live DB connection."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations directly against the configured database."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _get_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
