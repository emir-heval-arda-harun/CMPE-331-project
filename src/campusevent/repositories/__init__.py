"""Layer 3: data access and integration (Software Design Report, section 3).

- ``db``: connection to PostgreSQL (engine and sessions) from ``DATABASE_URL``
- ``tables``: SQLAlchemy mappings of the 8 tables (``UserRow``, ``EventRow``, ...)

The repository and ``UnitOfWork`` interfaces with their SQL and in-memory implementations are
added here by the backend tasks (3.2 to 3.4). Only this package talks to the database.
"""
