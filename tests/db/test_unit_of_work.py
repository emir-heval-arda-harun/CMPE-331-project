"""UnitOfWork (Software Design Report 4.3, 7.1): one transaction per request, shared by all repositories.

The in-memory test needs no database. The SQL tests use TEST_DATABASE_URL and are skipped without it.
"""

from __future__ import annotations

import threading

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from campusevent.repositories.db import create_scoped_session
from campusevent.repositories.tables import UserRow
from campusevent.repositories.unit_of_work import InMemoryUnitOfWork, SqlUnitOfWork

PREFIX = "uow.test."


def test_in_memory_unit_of_work_records_the_calls():
    uow = InMemoryUnitOfWork()

    uow.begin()
    assert uow.active
    uow.commit()
    uow.begin()
    uow.rollback()

    assert (uow.active, uow.commits, uow.rollbacks) == (False, 1, 1)


@pytest.fixture
def session(engine):
    session = create_scoped_session(engine)
    yield session
    session.remove()
    with engine.begin() as connection:  # these tests really commit: delete their rows again
        connection.execute(delete(UserRow).where(UserRow.email.startswith(PREFIX)))


def new_user(name: str) -> UserRow:
    return UserRow(email=f"{PREFIX}{name}@bilgiedu.net", full_name=name, password_hash="argon2-hash")


def stored(engine, name: str) -> int:
    """Count the user from ANOTHER connection: only committed rows are visible there."""
    with engine.connect() as connection:
        query = select(func.count()).select_from(UserRow).where(UserRow.email == f"{PREFIX}{name}@bilgiedu.net")
        return connection.scalar(query)


def test_commit_stores_the_rows(engine, session):
    uow = SqlUnitOfWork(session)

    uow.begin()
    session.add(new_user("ayse"))
    uow.commit()

    assert stored(engine, "ayse") == 1


def test_rollback_stores_nothing(engine, session):
    uow = SqlUnitOfWork(session)

    uow.begin()
    session.add(new_user("mehmet"))
    session.flush()  # the INSERT was sent to the database ...
    uow.rollback()  # ... and is undone

    assert stored(engine, "mehmet") == 0


def test_begin_after_a_read_goes_on_in_the_same_transaction(engine, session):
    uow = SqlUnitOfWork(session)
    session.scalar(select(func.count()).select_from(UserRow))  # a read starts a transaction by itself

    uow.begin()  # no "transaction already begun" error
    session.add(new_user("deniz"))
    uow.commit()

    assert stored(engine, "deniz") == 1


def test_after_a_constraint_error_rollback_makes_the_session_usable_again(engine, session):
    uow = SqlUnitOfWork(session)
    uow.begin()
    session.add(new_user("can"))
    uow.commit()

    uow.begin()
    session.add(UserRow(email=f"{PREFIX}CAN@bilgiedu.net", full_name="Copy", password_hash="argon2-hash"))
    with pytest.raises(IntegrityError) as caught:
        uow.commit()
    uow.rollback()
    assert caught.value.orig.diag.constraint_name == "ux_user_email_lower"  # map this to DuplicateEmailError

    uow.begin()
    session.add(new_user("elif"))
    uow.commit()
    assert stored(engine, "elif") == 1


def test_each_request_thread_gets_its_own_session(session):
    sessions = []
    worker = threading.Thread(target=lambda: sessions.append(session()))
    worker.start()
    worker.join()

    assert session() is session()  # the same request: always the same session
    assert sessions[0] is not session()  # another request (thread): another session
