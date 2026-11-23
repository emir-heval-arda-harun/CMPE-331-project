"""SqlEventRepository and EventService against a real PostgreSQL database (task 3.4).

Skipped without TEST_DATABASE_URL (see docs/database/README.md). These tests commit, so every row
they create has a name or e-mail starting with PREFIX and is deleted again after the test.
"""

from __future__ import annotations

from datetime import date, datetime

import psycopg
import pytest
from sqlalchemy import delete, func, select

from campusevent.events import EventService
from campusevent.exceptions import FacilityConflictError, NotFoundError
from campusevent.facilities import FacilityService
from campusevent.models import Event, EventStatus, Role, TimeSlot, User
from campusevent.repositories.db import create_scoped_session
from campusevent.repositories.event_repository import SqlEventRepository
from campusevent.repositories.facility_repository import SqlFacilityRepository
from campusevent.repositories.tables import EventRow, FacilityRow, UserRow
from campusevent.repositories.unit_of_work import SqlUnitOfWork

PREFIX = "event.test."
NOW = datetime(2026, 10, 31, 12, 0)


def at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, day, hour, minute)


@pytest.fixture
def session(engine):
    session = create_scoped_session(engine)
    yield session
    session.remove()
    with engine.begin() as connection:
        facilities = select(FacilityRow.id).where(FacilityRow.name.startswith(PREFIX))
        connection.execute(delete(EventRow).where(EventRow.facility_id.in_(facilities)))  # participants cascade
        connection.execute(delete(FacilityRow).where(FacilityRow.name.startswith(PREFIX)))
        connection.execute(delete(UserRow).where(UserRow.email.startswith(PREFIX)))


def _user(session, name: str, role: Role) -> int:
    row = UserRow(
        email=f"{PREFIX}{name}@bilgiedu.net",
        full_name=name.title(),
        password_hash="argon2-hash",
        role=role.value,
        is_verified=True,
    )
    session.add(row)
    session.commit()
    return row.id


@pytest.fixture
def people(session) -> dict[str, int]:
    return {
        "ece": _user(session, "ece", Role.STUDENT),
        "can": _user(session, "can", Role.STUDENT),
        "admin": _user(session, "admin", Role.ADMIN),
    }


@pytest.fixture
def hall_id(session) -> int:
    row = FacilityRow(manager_id=_user(session, "staff", Role.FACILITY_STAFF), name=PREFIX + "Hall", capacity=30)
    session.add(row)
    session.commit()
    return row.id


@pytest.fixture
def repo(session) -> SqlEventRepository:
    return SqlEventRepository(session)


def _event(organizer: int, facility: int, start: datetime, end: datetime, status=EventStatus.PENDING) -> Event:
    return Event(
        id=0,
        organizer_id=organizer,
        title="Board games",
        category="games",
        facility_id=facility,
        slot=TimeSlot(start, end),
        capacity=4,
        participant_ids=[organizer],
        status=status,
    )


def test_add_and_get_keep_naive_utc_and_the_participants(repo, session, people, hall_id):
    added = repo.add(_event(people["ece"], hall_id, at(2, 18), at(2, 20)))
    session.commit()

    loaded = repo.get(added.id)
    assert loaded.slot == TimeSlot(at(2, 18), at(2, 20))
    assert loaded.slot.start.tzinfo is None  # naive UTC in the domain, timestamptz in the table
    assert loaded.participant_ids == [people["ece"]]  # BR-05: the organizer takes part
    assert loaded.status == EventStatus.PENDING


def test_unknown_event_is_not_found(repo):
    with pytest.raises(NotFoundError):
        repo.get(987654321)


def test_overlapping_active_event_becomes_a_facility_conflict(repo, session, people, hall_id):
    repo.add(_event(people["ece"], hall_id, at(2, 18), at(2, 20)))
    session.commit()

    with pytest.raises(FacilityConflictError):  # ex_event_facility_no_overlap (BR-06, BR-16)
        repo.add(_event(people["can"], hall_id, at(2, 19), at(2, 21)))
    session.rollback()

    back_to_back = repo.add(_event(people["can"], hall_id, at(2, 20), at(2, 21)))  # [start, end)
    session.commit()
    assert back_to_back.id > 0


def test_save_changes_status_and_adds_and_removes_participants(repo, session, people, hall_id):
    event = repo.add(_event(people["ece"], hall_id, at(3, 18), at(3, 19)))
    session.commit()

    event.status = EventStatus.OPEN
    event.reviewed_by = people["admin"]
    event.reviewed_at = at(1, 9)
    event.participant_ids.append(people["can"])
    repo.save(event)
    session.commit()
    loaded = repo.get(event.id)
    assert loaded.status == EventStatus.OPEN
    assert loaded.reviewed_at == at(1, 9)
    assert sorted(loaded.participant_ids) == sorted([people["ece"], people["can"]])

    loaded.participant_ids.remove(people["can"])  # UC-10 leave
    repo.save(loaded)
    session.commit()
    assert repo.get(event.id).participant_ids == [people["ece"]]


def test_lists_by_status_participant_and_organizer(repo, session, people, hall_id):
    pending = repo.add(_event(people["ece"], hall_id, at(4, 10), at(4, 11)))
    opened = repo.add(_event(people["can"], hall_id, at(4, 12), at(4, 13), status=EventStatus.OPEN))
    opened.participant_ids.append(people["ece"])
    repo.save(opened)
    session.commit()

    ids = {e.id for e in repo.list_by_status([EventStatus.OPEN])}
    assert opened.id in ids and pending.id not in ids
    assert [e.id for e in repo.list_by_participant(people["ece"])] == [pending.id, opened.id]  # by start time
    assert [e.id for e in repo.list_by_organizer(people["can"])] == [opened.id]


def test_active_on_finds_events_that_overlap_the_utc_day(repo, session, people, hall_id):
    night = repo.add(_event(people["ece"], hall_id, at(5, 22), at(6, 1)))  # crosses midnight
    cancelled = repo.add(_event(people["can"], hall_id, at(6, 10), at(6, 11), status=EventStatus.CANCELLED))
    session.commit()

    ids = [e.id for e in repo.active_on(hall_id, date(2026, 11, 6))]
    assert ids == [night.id]  # BR-16: cancelled events do not hold the slot
    assert cancelled.id not in ids


def test_get_for_update_locks_the_event_row(repo, session, people, hall_id, test_database_url):
    event = repo.add(_event(people["ece"], hall_id, at(7, 18), at(7, 19)))
    session.commit()

    repo.get_for_update(event.id)  # transaction stays open: two students cannot take the last place
    plain_url = test_database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(plain_url) as other, pytest.raises(psycopg.errors.LockNotAvailable):
        other.execute("SELECT id FROM event WHERE id = %s FOR UPDATE NOWAIT", (event.id,))
    session.rollback()


class StubAuth:
    def __init__(self, people):
        self.people = people

    def require_role(self, user_id, role):
        return User(user_id, "x@bilgiedu.net", "X", role, True)

    def get_user(self, user_id):
        return User(user_id, "x@bilgiedu.net", "X", Role.STUDENT, True)


def test_event_service_with_postgresql_from_request_to_history(engine, session, people, hall_id):
    """create → approve → join → (after the end) completed and in the history, all in PostgreSQL;
    a conflicting request is rolled back and leaves nothing behind."""
    now = [NOW]
    uow = SqlUnitOfWork(session)
    events = SqlEventRepository(session)
    auth = StubAuth(people)
    facilities = FacilityService(auth, SqlFacilityRepository(session), events, uow=uow)
    service = EventService(auth, facilities, events, uow, clock=lambda: now[0])

    event = service.create_event(people["ece"], "Chess night", "Games", hall_id, TimeSlot(at(8, 18), at(8, 20)), 4)
    with pytest.raises(FacilityConflictError):
        service.create_event(people["can"], "Quiz", "games", hall_id, TimeSlot(at(8, 19), at(8, 21)), 4)
    service.approve_event(event.id, people["admin"])
    service.join_event(event.id, people["can"])

    with engine.connect() as connection:  # only the committed event is in the database
        count = connection.scalar(select(func.count()).select_from(EventRow).where(EventRow.facility_id == hall_id))
    assert count == 1

    now[0] = at(9, 0)  # the day after
    history = service.get_activity_history(people["can"])
    assert [record.event_id for record in history] == [event.id]  # UC-09, BR-11
    assert service.get_event(event.id).status == EventStatus.COMPLETED
