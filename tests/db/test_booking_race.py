"""Integration test (task 4.2): two requests use the same facility time at the same moment.

Risk R-01 of the Software Design Report (5.3, 7.1): two students book the same slot, or a student books
while facility staff block it. `FacilityService.check_bookable` and `add_block` lock the facility row
(`SELECT ... FOR UPDATE`) inside the request's transaction, so the second request waits until the first
one has committed, then sees its event or block and is refused (BR-06, BR-16, UC-04 alt. 3a, UC-08).

Each test runs the real services of `create_app(database_url=...)` in two threads, so each request has its
own database session, like two web requests. The first request is held inside its transaction (after
the lock, before the commit); the test checks in `pg_stat_activity` that the second one really waits for
a lock, and only then lets the first one finish. Without the lock both would pass the check.

Skipped without TEST_DATABASE_URL (see docs/database/README.md); CI runs them on PostgreSQL 16 (#36).
Every row created here has a name or e-mail starting with PREFIX and is deleted after the test.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime

import pytest
from sqlalchemy import delete, select, text

from campusevent.app import create_app
from campusevent.exceptions import FacilityConflictError
from campusevent.models import Role, TimeSlot
from campusevent.repositories.tables import EventRow, FacilityRow, UserRow

PREFIX = "race.test."
NOW = datetime(2026, 11, 27, 9, 0)  # naive UTC, the clock of EventService
SLOT = TimeSlot(datetime(2026, 12, 10, 15, 0), datetime(2026, 12, 10, 17, 0))
LATER = TimeSlot(datetime(2026, 12, 10, 16, 0), datetime(2026, 12, 10, 18, 0))  # overlaps SLOT
TIMEOUT = 10  # seconds; only reached when something is wrong


@pytest.fixture
def services(engine, test_database_url, fast_hasher):
    services = create_app(
        password_hasher=fast_hasher, secret_key="test", database_url=test_database_url, clock=lambda: NOW
    )
    yield services
    services.end_request()
    services.db_session.get_bind().dispose()
    with engine.begin() as connection:
        facility_ids = select(FacilityRow.id).where(FacilityRow.name.startswith(PREFIX))
        connection.execute(delete(EventRow).where(EventRow.facility_id.in_(facility_ids)))
        connection.execute(delete(FacilityRow).where(FacilityRow.name.startswith(PREFIX)))  # blocks go with it
        connection.execute(delete(UserRow).where(UserRow.email.startswith(PREFIX)))


@pytest.fixture
def people(engine):
    """Two verified students and one facility staff member, written directly (sign-up is tested elsewhere)."""
    ids = {}
    with engine.begin() as connection:
        for name, role in (("ayse", Role.STUDENT), ("mert", Role.STUDENT), ("staff", Role.FACILITY_STAFF)):
            ids[name] = connection.execute(
                UserRow.__table__.insert()
                .values(
                    email=f"{PREFIX}{name}@bilgiedu.net",
                    full_name=name.title(),
                    password_hash="argon2-hash",
                    role=role.value,
                    is_verified=True,
                )
                .returning(UserRow.id)
            ).scalar_one()
    return ids


@pytest.fixture
def hall(services, people):
    facility = services.facilities.add_facility(people["staff"], PREFIX + "Santral Hall", 50)
    services.end_request()
    return facility


def hold_inside_transaction(target, name: str):
    """Make the next call of ``target.<name>`` wait (the row lock is already held then) until released."""
    original = getattr(target, name)
    holding, release = threading.Event(), threading.Event()

    def held(*args, **kwargs):
        setattr(target, name, original)  # only the first request is held
        holding.set()
        assert release.wait(TIMEOUT), "the test never released the first request"
        return original(*args, **kwargs)

    setattr(target, name, held)
    return holding, release


def in_thread(services, request):
    """Run one request in its own thread (own database session) and keep its result or error."""
    outcome = {}

    def run():
        try:
            outcome["result"] = request()
        except Exception as error:  # noqa: BLE001 - the test looks at the error
            outcome["error"] = error
        finally:
            services.end_request()

    thread = threading.Thread(target=run)
    thread.start()
    return thread, outcome


def wait_until_a_request_waits_for_a_lock(engine):
    deadline = time.monotonic() + TIMEOUT
    query = text(
        "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND wait_event_type = 'Lock'"
    )
    while time.monotonic() < deadline:
        with engine.connect() as connection:
            if connection.execute(query).scalar_one() > 0:
                return
        time.sleep(0.05)
    pytest.fail("the second request did not wait for the facility lock")


def race(services, engine, first, second, hold_target, hold_name):
    """Start ``first``, hold it after it took the lock, start ``second``, check that it waits, release."""
    holding, release = hold_inside_transaction(hold_target, hold_name)
    first_thread, first_outcome = in_thread(services, first)
    try:
        assert holding.wait(TIMEOUT), "the first request did not reach its transaction"
        second_thread, second_outcome = in_thread(services, second)
        wait_until_a_request_waits_for_a_lock(engine)
        assert second_thread.is_alive()  # still waiting while the first one holds the lock
    finally:
        release.set()
    first_thread.join(TIMEOUT)
    second_thread.join(TIMEOUT)
    assert not first_thread.is_alive() and not second_thread.is_alive()
    return first_outcome, second_outcome


def events_of(engine, facility_id):
    with engine.connect() as connection:
        return connection.execute(select(EventRow.title).where(EventRow.facility_id == facility_id)).scalars().all()


def test_r01_two_students_book_the_same_slot_at_the_same_moment(services, engine, people, hall):
    """UC-04 alt. 3a, BR-06, BR-16: only one of two requests for overlapping times gets the facility."""

    def book(student, title, slot):
        return lambda: services.events.create_event(people[student], title, "games", hall.id, slot, 20)

    first, second = race(
        services,
        engine,
        book("ayse", "Board game night", SLOT),
        book("mert", "Chess club", LATER),
        services.events.events,
        "add",  # held after check_bookable locked the facility
    )

    assert "error" not in first and first["result"].title == "Board game night"
    assert isinstance(second.get("error"), FacilityConflictError)
    assert events_of(engine, hall.id) == ["Board game night"]  # one booking, the other one left nothing behind


def test_r01_staff_block_waits_for_a_booking_in_progress_and_is_refused(services, engine, people, hall):
    """UC-08 step 2, BR-06: a block started while a student books the same time does not get in."""
    first, second = race(
        services,
        engine,
        lambda: services.events.create_event(people["ayse"], "Board game night", "games", hall.id, SLOT, 20),
        lambda: services.facilities.add_block(people["staff"], hall.id, LATER, "Maintenance"),
        services.events.events,
        "add",
    )

    assert "error" not in first
    assert isinstance(second.get("error"), FacilityConflictError)
    assert services.facilities.get_blocks(hall.id, SLOT.start.date()) == []
    services.end_request()


def test_r01_booking_waits_for_a_block_in_progress_and_is_refused(services, engine, people, hall):
    """UC-08 postcondition, BR-06: a student cannot book a time that staff are blocking at the same moment."""
    first, second = race(
        services,
        engine,
        lambda: services.facilities.add_block(people["staff"], hall.id, SLOT, "Maintenance"),
        lambda: services.events.create_event(people["ayse"], "Board game night", "games", hall.id, LATER, 20),
        services.facilities.facilities,
        "add_block",  # held after add_block locked the facility
    )

    assert "error" not in first and first["result"].reason == "Maintenance"
    assert isinstance(second.get("error"), FacilityConflictError)
    assert events_of(engine, hall.id) == []
