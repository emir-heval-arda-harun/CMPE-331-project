"""UnitOfWork: the transaction of one request (Software Design Report 3.1, 4.3 and 7.1).

Services never open transactions on the database themselves. A writing service method does:

    self.uow.begin()
    try:
        facility = self.facilities.get_for_update(facility_id)  # SELECT ... FOR UPDATE (row lock)
        ...                                                     # check the rules, then add / save
        self.uow.commit()
    except Exception:
        self.uow.rollback()  # nothing of the failed request is stored
        raise

``SqlUnitOfWork`` and all ``Sql*Repository`` objects get the same scoped session
(``db.create_scoped_session``), which gives one SQLAlchemy session per request. So every repository
call between ``begin()`` and ``commit()`` is part of one database transaction.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.orm import Session, scoped_session


class UnitOfWork(Protocol):
    def begin(self) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class SqlUnitOfWork:
    """UnitOfWork on the shared SQLAlchemy session (production)."""

    def __init__(self, session: scoped_session[Session]) -> None:
        self.session = session  # the registry; self.session() is the session of the current request

    def begin(self) -> None:
        current = self.session()
        # SQLAlchemy opens a transaction by itself at the first query of a session ("autobegin").
        # If the service already read something in this request, that transaction simply goes on.
        if not current.in_transaction():
            current.begin()

    def commit(self) -> None:
        self.session().commit()

    def rollback(self) -> None:
        self.session().rollback()


class InMemoryUnitOfWork:
    """UnitOfWork for the in-memory repositories of the tests. There is no database, so it only
    records the calls; services check every rule before they change data (fail fast)."""

    def __init__(self) -> None:
        self.active = False
        self.commits = 0
        self.rollbacks = 0

    def begin(self) -> None:
        self.active = True

    def commit(self) -> None:
        self.active = False
        self.commits += 1

    def rollback(self) -> None:
        self.active = False
        self.rollbacks += 1
