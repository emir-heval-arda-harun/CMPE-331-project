"""SqlUserRepository and AuthService.require_role against a real PostgreSQL database (task 3.2).

Skipped without TEST_DATABASE_URL (see docs/database/README.md). These tests commit, so every user
they create has an e-mail starting with PREFIX and is deleted again after the test.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete

from campusevent.auth import AuthService
from campusevent.exceptions import DuplicateEmailError, NotFoundError, PermissionDeniedError
from campusevent.models import Role, User
from campusevent.notifications import InMemoryEmailSender
from campusevent.repositories.db import create_scoped_session
from campusevent.repositories.tables import UserRow
from campusevent.repositories.user_repository import SqlUserRepository

PREFIX = "user.test."


@pytest.fixture
def session(engine):
    session = create_scoped_session(engine)
    yield session
    session.remove()
    with engine.begin() as connection:
        connection.execute(delete(UserRow).where(UserRow.email.startswith(PREFIX)))


@pytest.fixture
def repo(session) -> SqlUserRepository:
    return SqlUserRepository(session)


def new_user(local: str, role: Role = Role.STUDENT, verified: bool = True) -> User:
    return User(0, f"{PREFIX}{local}@bilgi.edu.tr", local.title(), role, verified)


def test_add_and_get_return_domain_users(repo, session):
    staff = repo.add(new_user("staff", Role.FACILITY_STAFF), "argon2-hash")
    session.commit()

    loaded = repo.get(staff.id)
    assert loaded == User(staff.id, f"{PREFIX}staff@bilgi.edu.tr", "Staff", Role.FACILITY_STAFF, True)
    assert loaded.role is Role.FACILITY_STAFF  # a Role, not the string stored in the table


def test_password_hash_is_stored_but_not_returned(repo, session):
    user = repo.add(new_user("ali", verified=False), "argon2-hash")
    session.commit()

    assert session.get(UserRow, user.id).password_hash == "argon2-hash"
    assert not hasattr(repo.get(user.id), "password_hash")
    assert repo.get(user.id).is_verified is False


def test_unknown_id_raises_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get(-1)


def test_same_email_in_other_case_is_a_duplicate(repo, session):
    repo.add(new_user("ali"), "argon2-hash")
    session.commit()

    with pytest.raises(DuplicateEmailError):
        repo.add(User(0, f"{PREFIX}ALI@bilgi.edu.tr", "Ali", Role.STUDENT, True), "argon2-hash")
    session.rollback()


def test_require_role_with_sql_repository(repo, session):
    auth = AuthService(("bilgi.edu.tr",), InMemoryEmailSender(), repo)
    admin = repo.add(new_user("admin", Role.ADMIN), "argon2-hash")
    student = repo.add(new_user("ali"), "argon2-hash")
    session.commit()

    assert auth.require_role(admin.id, Role.ADMIN) == admin
    with pytest.raises(PermissionDeniedError):
        auth.require_role(student.id, Role.ADMIN)
