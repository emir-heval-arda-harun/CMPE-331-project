"""SqlFacilityRepository and FacilityService against a real PostgreSQL database (task 3.3).

Skipped without TEST_DATABASE_URL (see docs/database/README.md). These tests commit, so every row
they create has a name or e-mail starting with PREFIX and is deleted again after the test.
"""

from __future__ import annotations

from datetime import date, datetime

import psycopg
import pytest
from sqlalchemy import delete, select, text

from campusevent.exceptions import NotFoundError, ValidationError
from campusevent.facilities import FacilityService
from campusevent.models import Facility, FacilityBlock, Role, TimeSlot, User
from campusevent.repositories.db import create_scoped_session
from campusevent.repositories.facility_repository import SqlFacilityRepository
from campusevent.repositories.tables import FacilityBlockRow, FacilityRow, UserRow
from campusevent.repositories.unit_of_work import SqlUnitOfWork

PREFIX = "facility.test."


def at(day: int, hour: int) -> datetime:
    return datetime(2026, 11, day, hour, 0)


@pytest.fixture
def session(engine):
    session = create_scoped_session(engine)
    yield session
    session.remove()
    with engine.begin() as connection:
        ids = select(FacilityRow.id).where(FacilityRow.name.startswith(PREFIX))
        connection.execute(delete(FacilityBlockRow).where(FacilityBlockRow.facility_id.in_(ids)))
        connection.execute(delete(FacilityRow).where(FacilityRow.name.startswith(PREFIX)))
        connection.execute(delete(UserRow).where(UserRow.email.startswith(PREFIX)))


@pytest.fixture
def staff_id(session) -> int:
    row = UserRow(
        email=f"{PREFIX}staff@bilgi.edu.tr",
        full_name="Staff",
        password_hash="argon2-hash",
        role=Role.FACILITY_STAFF.value,
        is_verified=True,
    )
    session.add(row)
    session.commit()
    return row.id


@pytest.fixture
def repo(session) -> SqlFacilityRepository:
    return SqlFacilityRepository(session)


def add(repo, session, staff_id, name, capacity=20) -> Facility:
    facility = repo.add(Facility(0, PREFIX + name, capacity), manager_id=staff_id)
    session.commit()
    return facility


def test_add_get_find_and_list(repo, session, staff_id):
    tennis = add(repo, session, staff_id, "Tennis Court", 4)
    hall = add(repo, session, staff_id, "Event Hall", 50)

    assert repo.get(hall.id) == hall
    assert repo.find_by_name(f"  {PREFIX}EVENT hall ") == hall
    assert repo.find_by_name(PREFIX + "Nowhere") is None
    mine = [f for f in repo.list_all() if f.name.startswith(PREFIX)]
    assert mine == [hall, tennis]  # sorted by name


def test_unknown_facility(repo):
    with pytest.raises(NotFoundError):
        repo.get(-1)
    with pytest.raises(NotFoundError):
        repo.get_for_update(-1)


def test_duplicate_name_becomes_a_validation_error(repo, session, staff_id):
    add(repo, session, staff_id, "Hall")

    with pytest.raises(ValidationError):
        repo.add(Facility(0, PREFIX + "Hall", 10), manager_id=staff_id)
    session.rollback()


def test_blocks_keep_naive_utc_times_and_are_found_by_day(repo, session, staff_id):
    hall = add(repo, session, staff_id, "Hall")
    night = repo.add_block(FacilityBlock(hall.id, TimeSlot(at(2, 23), at(3, 1)), "Cleaning"), created_by=staff_id)
    morning = repo.add_block(FacilityBlock(hall.id, TimeSlot(at(3, 9), at(3, 12)), "Class"), created_by=staff_id)
    session.commit()

    assert night.slot == TimeSlot(at(2, 23), at(3, 1))  # naive, same wall time as stored
    assert repo.blocks_on(hall.id, date(2026, 11, 2)) == [night]
    assert repo.blocks_on(hall.id, date(2026, 11, 3)) == [night, morning]  # the night block reaches into day 3
    assert repo.blocks_on(hall.id, date(2026, 11, 4)) == []


def test_overlapping_blocks_become_a_validation_error(repo, session, staff_id):
    hall = add(repo, session, staff_id, "Hall")
    repo.add_block(FacilityBlock(hall.id, TimeSlot(at(2, 9), at(2, 12)), "Class"), created_by=staff_id)
    session.commit()

    with pytest.raises(ValidationError):
        repo.add_block(FacilityBlock(hall.id, TimeSlot(at(2, 11), at(2, 13)), "Maintenance"), created_by=staff_id)
    session.rollback()


def test_get_for_update_locks_the_facility_row(repo, session, staff_id, test_database_url):
    hall = add(repo, session, staff_id, "Hall")

    repo.get_for_update(hall.id)  # transaction stays open: the row is locked
    plain_url = test_database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(plain_url) as other, pytest.raises(psycopg.errors.LockNotAvailable):
        other.execute("SELECT id FROM facility WHERE id = %s FOR UPDATE NOWAIT", (hall.id,))
    session.rollback()


class StubAuth:
    def __init__(self, staff_id):
        self.staff = User(staff_id, "staff@bilgi.edu.tr", "Staff", Role.FACILITY_STAFF, True)

    def require_role(self, user_id, role):
        return self.staff


def test_service_with_sql_repository_rolls_back_a_refused_block(engine, session, staff_id):
    service = FacilityService(StubAuth(staff_id), SqlFacilityRepository(session), uow=SqlUnitOfWork(session))
    hall = service.add_facility(staff_id, PREFIX + "Hall", 30)
    service.add_block(staff_id, hall.id, TimeSlot(at(2, 9), at(2, 12)), "Class")

    with pytest.raises(ValidationError):
        service.add_block(staff_id, hall.id, TimeSlot(at(2, 10), at(2, 11)), "Maintenance")

    assert service.is_available(hall.id, TimeSlot(at(2, 10), at(2, 11))) is False
    assert service.get_schedule(hall.id, date(2026, 11, 2)) == [TimeSlot(at(2, 9), at(2, 12))]
    with engine.connect() as connection:  # only the committed block is in the database
        count = connection.scalar(text("SELECT count(*) FROM facility_block WHERE facility_id = :id"), {"id": hall.id})
    assert count == 1
