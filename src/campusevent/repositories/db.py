"""Database connection (layer 3: data access and integration).

The connection string comes only from the ``DATABASE_URL`` environment variable: on Render it is
set by the managed database (render.yaml), on your computer it is in your local ``.env`` file
(see .env.example and docs/database/README.md). It is never written in the code.

Typical use in the composition root (``app.py``)::

    engine = create_db_engine()
    session_factory = create_session_factory(engine)
    # one session per request, shared by SqlUnitOfWork and all Sql*Repository objects
"""

from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

DRIVER_PREFIX = "postgresql+psycopg://"


def normalize_database_url(url: str) -> str:
    """Make SQLAlchemy use the psycopg 3 driver.

    Render (and most hosts) give ``postgres://...`` or ``postgresql://...``. Without a driver name
    SQLAlchemy would look for the older psycopg2 package, which we do not install.
    """
    url = url.strip()
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return DRIVER_PREFIX + url[len(prefix):]
    return url


def get_database_url(env_var: str = "DATABASE_URL") -> str:
    url = os.environ.get(env_var, "").strip()
    if not url:
        raise RuntimeError(
            f"{env_var} is not set. Copy .env.example to .env and fill in {env_var} (see docs/database/README.md)."
        )
    return normalize_database_url(url)


def create_db_engine(url: str | None = None, **kwargs) -> Engine:
    """Create the engine (the connection pool). Create it once per process, not per request."""
    return create_engine(
        normalize_database_url(url) if url else get_database_url(),
        # Render's free database closes idle connections; check a pooled connection before using it.
        pool_pre_ping=True,
        # Every connection works in UTC: timestamptz values come back in UTC, and a datetime without
        # a time zone is read as UTC (Software Design Report, section 6: all times are stored in UTC).
        connect_args={"options": "-c timezone=UTC"},
        **kwargs,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    # expire_on_commit=False: objects can still be read after commit (e.g. to build the response).
    return sessionmaker(bind=engine, expire_on_commit=False)
