"""Alembic environment: connects to the database and runs the migrations in versions/.

The address of the database is taken from (first match wins):
1. ``sqlalchemy.url`` set by a program (the database tests use this for TEST_DATABASE_URL),
2. the ``DATABASE_URL`` environment variable,
3. ``DATABASE_URL`` in the local .env file of the repository.
"""

from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool

from campusevent.repositories.db import create_db_engine, get_database_url
from campusevent.repositories.tables import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Used by "alembic revision --autogenerate" to compare the tables in tables.py with the database.
target_metadata = Base.metadata


def database_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # does not override real variables
    return get_database_url()


def run_migrations_offline() -> None:
    """``alembic upgrade head --sql``: print the SQL instead of running it."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_db_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        # Each migration runs in one transaction: if any statement fails, nothing is changed.
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
