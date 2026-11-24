"""SqlUserRepository and AuthService (UC-01, UC-02, require_role) against a real PostgreSQL database.

Skipped without TEST_DATABASE_URL (see docs/database/README.md). These tests commit, so every user
they create has an e-mail starting with PREFIX and is deleted again after the test.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import delete

from campusevent.auth import MAX_FAILED_LOGINS, AuthService
from campusevent.exceptions import (
    AuthenticationError,
    DuplicateEmailError,
    NotFoundError,
    PermissionDeniedError,
    TooManyAttemptsError,
)
from campusevent.models import Role, User, VerificationCode
from campusevent.notifications import InMemoryEmailSender
from campusevent.repositories.db import create_scoped_session
from campusevent.repositories.tables import UserRow
from campusevent.repositories.unit_of_work import SqlUnitOfWork
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


# --------------------------------------------------------------------------- #
# UC-01 and UC-02
# --------------------------------------------------------------------------- #
def test_find_by_email_ignores_case_and_spaces(repo, session):
    ali = repo.add(new_user("ali"), "argon2-hash")
    session.commit()

    assert repo.find_by_email(f"  {PREFIX}ALI@Bilgi.edu.tr ") == ali
    assert repo.find_by_email(f"{PREFIX}nobody@bilgi.edu.tr") is None


def test_password_hash_is_read_by_id(repo, session):
    user = repo.add(new_user("ali"), "argon2-hash")
    session.commit()

    assert repo.get_password_hash(user.id) == "argon2-hash"
    with pytest.raises(NotFoundError):
        repo.get_password_hash(-1)


def test_latest_code_is_the_last_one_saved_in_naive_utc(repo, session):
    user = repo.add(new_user("ali", verified=False), "argon2-hash")
    assert repo.get_latest_code(user.id) is None

    expires = datetime(2026, 11, 20, 12, 15)
    repo.save_code(user.id, "old-code-hash", expires)
    new = repo.save_code(user.id, "new-code-hash", expires + timedelta(minutes=5))
    session.commit()

    latest = repo.get_latest_code(user.id)
    assert latest == new == VerificationCode(new.id, user.id, "new-code-hash", datetime(2026, 11, 20, 12, 20), False, 0)
    assert latest.expires_at.tzinfo is None


def test_mark_code_used_and_mark_verified(repo, session):
    user = repo.add(new_user("ali", verified=False), "argon2-hash")
    code = repo.save_code(user.id, "code-hash", datetime(2026, 11, 20, 12, 15))

    repo.mark_code_used(code.id)
    repo.mark_verified(user.id)
    session.commit()

    assert repo.get_latest_code(user.id).used is True
    assert repo.get(user.id).is_verified is True


def test_register_verify_and_login_with_postgresql(repo, session, fast_hasher):
    sender = InMemoryEmailSender()
    auth = AuthService(
        ("bilgi.edu.tr",), sender, repo, uow=SqlUnitOfWork(session), hasher=fast_hasher, secret_key="test"
    )
    email = f"{PREFIX}ayse@bilgi.edu.tr"

    user = auth.register(email, "S3cure-pass!", "Ayse")
    with pytest.raises(DuplicateEmailError):
        auth.register(email.upper(), "S3cure-pass!", "Ayse")
    auth.verify_email(email, sender.codes[email])
    token = auth.login(email, "S3cure-pass!")

    assert auth.get_user_by_token(token) == User(user.id, email, "Ayse", Role.STUDENT, True)
    assert session.get(UserRow, user.id).password_hash.startswith("$argon2id$")


# --------------------------------------------------------------------------- #
# Limits from the penetration test (migration 0002)
# --------------------------------------------------------------------------- #
def test_wrong_code_attempts_are_counted_in_the_database(repo, session):
    user = repo.add(new_user("ali", verified=False), "argon2-hash")
    code = repo.save_code(user.id, "code-hash", datetime(2026, 11, 20, 12, 15))
    repo.record_wrong_code(code.id)
    repo.record_wrong_code(code.id)
    session.commit()

    assert repo.get_latest_code(user.id).attempts == 2


def test_login_failures_and_pause_in_naive_utc(repo, session):
    user = repo.add(new_user("ali"), "argon2-hash")
    session.commit()
    assert repo.get_login_failures(user.id) == (0, None)

    repo.set_login_failures(user.id, 5, datetime(2026, 11, 20, 12, 1))
    session.commit()
    failures, paused_until = repo.get_login_failures(user.id)
    session.commit()  # get_login_failures locks the row until the end of the transaction
    assert (failures, paused_until) == (5, datetime(2026, 11, 20, 12, 1)) and paused_until.tzinfo is None
    with pytest.raises(NotFoundError):
        repo.get_login_failures(-1)


def test_session_version_goes_up_by_one(repo, session):
    user = repo.add(new_user("ali"), "argon2-hash")
    session.commit()
    assert repo.get_session_version(user.id) == 0

    repo.next_session_version(user.id)
    session.commit()
    assert repo.get_session_version(user.id) == 1
    with pytest.raises(NotFoundError):
        repo.get_session_version(-1)


def test_pause_and_log_out_with_postgresql(repo, session, fast_hasher):
    """P1 and P3 end to end: the failures are kept although every wrong log in answers with an error."""
    sender = InMemoryEmailSender()
    auth = AuthService(
        ("bilgi.edu.tr",), sender, repo, uow=SqlUnitOfWork(session), hasher=fast_hasher, secret_key="test"
    )
    email = f"{PREFIX}deniz@bilgi.edu.tr"
    auth.register(email, "S3cure-pass!", "Deniz")
    auth.verify_email(email, sender.codes[email])
    token = auth.login(email, "S3cure-pass!")

    auth.logout(token)
    with pytest.raises(AuthenticationError):
        auth.get_user_by_token(token)

    for _ in range(MAX_FAILED_LOGINS):
        with pytest.raises(AuthenticationError):
            auth.login(email, "wrong-password")
    with pytest.raises(TooManyAttemptsError):
        auth.login(email, "S3cure-pass!")
