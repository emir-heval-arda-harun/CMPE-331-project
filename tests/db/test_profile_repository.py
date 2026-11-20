"""SqlProfileRepository and ProfileService (UC-03) against a real PostgreSQL database.

Skipped without TEST_DATABASE_URL (see docs/database/README.md). These tests commit, so every user
they create has an e-mail starting with PREFIX and is deleted again after the test (the profile rows
go with it: ON DELETE CASCADE).
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import delete, select

from campusevent.auth import AuthService
from campusevent.exceptions import ValidationError
from campusevent.models import Profile, Role, TimeSlot, User
from campusevent.notifications import InMemoryEmailSender
from campusevent.profiles import ProfileService
from campusevent.repositories.db import create_scoped_session
from campusevent.repositories.profile_repository import SqlProfileRepository
from campusevent.repositories.tables import AvailabilitySlotRow, UserRow
from campusevent.repositories.unit_of_work import SqlUnitOfWork
from campusevent.repositories.user_repository import SqlUserRepository

PREFIX = "profile.test."


@pytest.fixture
def session(engine):
    session = create_scoped_session(engine)
    yield session
    session.remove()
    with engine.begin() as connection:
        connection.execute(delete(UserRow).where(UserRow.email.startswith(PREFIX)))


@pytest.fixture
def repo(session) -> SqlProfileRepository:
    return SqlProfileRepository(session)


@pytest.fixture
def deniz(session) -> User:
    user = SqlUserRepository(session).add(User(0, f"{PREFIX}deniz@bilgiedu.net", "Deniz", Role.STUDENT, True), "hash")
    session.commit()
    return user


def at(day, hour, hours=1):
    start = datetime(2026, 11, day, hour)
    return TimeSlot(start, start.replace(hour=hour + hours))


def test_user_without_rows_has_an_empty_profile(repo, deniz):
    assert repo.get(deniz.id) == Profile(deniz.id, [], [])


def test_save_and_get_in_naive_utc(repo, session, deniz):
    repo.save(Profile(deniz.id, ["football", "board games"], [at(4, 18), at(3, 17, 2)]))
    session.commit()

    loaded = repo.get(deniz.id)
    assert loaded == Profile(deniz.id, ["board games", "football"], [at(3, 17, 2), at(4, 18)])  # alphabetical
    assert loaded.availability[0].start.tzinfo is None
    stored = session.scalars(select(AvailabilitySlotRow.start_time).where(AvailabilitySlotRow.user_id == deniz.id))
    assert min(stored).isoformat() == "2026-11-03T17:00:00+00:00"  # timestamptz in UTC


def test_save_replaces_the_rows_and_can_keep_an_interest(repo, session, deniz):
    repo.save(Profile(deniz.id, ["football", "chess"], [at(3, 17)]))
    session.commit()

    repo.save(Profile(deniz.id, ["football", "tennis"], []))
    session.commit()

    assert repo.get(deniz.id) == Profile(deniz.id, ["football", "tennis"], [])


def test_profile_service_with_postgresql(session, deniz):
    auth = AuthService(("bilgiedu.net",), InMemoryEmailSender(), SqlUserRepository(session))
    profiles = ProfileService(auth, SqlProfileRepository(session), SqlUnitOfWork(session))

    profiles.update_profile(deniz.id, [" Football ", "FOOTBALL", "Study Group"], [at(3, 17)])
    with pytest.raises(ValidationError):
        profiles.update_profile(deniz.id, [], [])  # nothing is saved

    assert profiles.get_profile(deniz.id) == Profile(deniz.id, ["football", "study group"], [at(3, 17)])
