"""Layer 3: data access and integration (Software Design Report, section 3).

- ``db``: connection to PostgreSQL (engine, one session per request) from ``DATABASE_URL``
- ``tables``: SQLAlchemy mappings of the 8 tables (``UserRow``, ``EventRow``, ...)
- ``unit_of_work``: the ``UnitOfWork`` interface with ``SqlUnitOfWork`` and ``InMemoryUnitOfWork``

The repository interfaces with their SQL and in-memory implementations are added here by the
backend tasks (3.2 to 3.4); see docs/database/README.md. Only this package talks to the database.
"""
