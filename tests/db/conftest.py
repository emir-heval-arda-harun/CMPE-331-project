"""Fixtures for the database tests. They need a real PostgreSQL database and are SKIPPED without one.

Set TEST_DATABASE_URL (as an environment variable or in your local .env) to an empty database
that is used only for tests: the tests delete and re-create all tables in it. See
docs/database/README.md. CI runs them on its own PostgreSQL 16 (#36).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values

from campusevent.repositories.db import create_db_engine, normalize_database_url

ROOT = Path(__file__).resolve().parents[2]


def _setting(name: str) -> str | None:
    # dotenv_values only reads .env; unlike load_dotenv it does not change os.environ for the other tests.
    value = os.environ.get(name) or dotenv_values(ROOT / ".env").get(name)
    return normalize_database_url(value) if value else None


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = _setting("TEST_DATABASE_URL")
    if not url:
        if os.environ.get("CI"):  # GitHub Actions sets CI: there a missing database is a broken setup
            pytest.fail("TEST_DATABASE_URL is not set in CI, the database tests would be skipped silently")
        pytest.skip("TEST_DATABASE_URL is not set, database tests skipped (see docs/database/README.md)")
    if url == _setting("DATABASE_URL"):
        pytest.fail("TEST_DATABASE_URL must be a different database than DATABASE_URL: the tests delete all tables")
    return url


@pytest.fixture(scope="session")
def alembic_config(test_database_url) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", test_database_url.replace("%", "%%"))  # "%" is special in .ini files
    return config


@pytest.fixture(scope="session")
def engine(test_database_url, alembic_config):
    """Start every test run from an empty database and build it with the migrations, like on Render."""
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    engine = create_db_engine(test_database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    """A connection inside a transaction that is rolled back after the test, so no test sees the rows of another."""
    with engine.connect() as connection:
        transaction = connection.begin()
        yield connection
        transaction.rollback()
