"""Unit tests of FacilityService (task 3.3, UC-07 and UC-08).

AuthService (task 3.2) and the event repository (task 3.4) are not written yet, so these tests use
small stand-ins for them. The requirement tests (test_uc07, test_uc08) run against the real
services once those tasks are merged.
"""

from datetime import date

import pytest

from campusevent.exceptions import FacilityConflictError, NotFoundError, PermissionDeniedError, ValidationError
from campusevent.facilities import FacilityService
from campusevent.models import Event, EventStatus, Role, TimeSlot, User
from campusevent.repositories.facility_repository import day_range
from campusevent.repositories.unit_of_work import InMemoryUnitOfWork
from tests.helpers import slot

STAFF, STUDENT = 1, 2


class StubAuth:
    users = {
        STAFF: User(STAFF, "staff@bilgi.edu.tr", "Staff", Role.FACILITY_STAFF, True),
        STUDENT: User(STUDENT, "ali@bilgiedu.net", "Ali", Role.STUDENT, True),
    }

    def require_role(self, user_id, role):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError()
        if user.role is not role:
            raise PermissionDeniedError()
        return user


class StubEvents:
    def __init__(self):
        self.events: list[Event] = []

    def book(self, facility_id, when, status=EventStatus.OPEN):
        event = Event(len(self.events) + 1, STUDENT, "Game", "board games", facility_id, when, 6, status=status)
        self.events.append(event)
        return event

    def active_on(self, facility_id, day):
        whole_day = TimeSlot(*day_range(day))
        return [e for e in self.events if e.facility_id == facility_id and e.slot.overlaps(whole_day)]


@pytest.fixture
def events():
    return StubEvents()


@pytest.fixture
def uow():
    return InMemoryUnitOfWork()


@pytest.fixture
def service(events, uow):
    return FacilityService(StubAuth(), events=events, uow=uow)


@pytest.fixture
def hall(service):
    return service.add_facility(STAFF, "Santral Event Hall", 50)


# ---------------------------------------------------------------- UC-08
def test_staff_adds_facility(service, uow):
    court = service.add_facility(STAFF, "  Dorm Basketball Court ", 30)

    assert (court.name, court.capacity) == ("Dorm Basketball Court", 30)
    assert service.get_facility(court.id) == court
    assert uow.commits == 1


def test_student_cannot_add_facility_or_block(service, hall):
    with pytest.raises(PermissionDeniedError):
        service.add_facility(STUDENT, "Fake Court", 10)
    with pytest.raises(PermissionDeniedError):
        service.add_block(STUDENT, hall.id, slot(hour=9), "Class")


@pytest.mark.parametrize("capacity", [1, 0, -5, 2.5, "10", True])
def test_capacity_must_be_a_whole_number_of_at_least_2(service, capacity):
    with pytest.raises(ValidationError):
        service.add_facility(STAFF, "Room", capacity)


def test_smallest_capacity_and_longest_name_are_accepted(service):
    facility = service.add_facility(STAFF, "x" * 100, 2)  # boundary values: capacity 2, name 100 characters

    assert (len(facility.name), facility.capacity) == (100, 2)


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
def test_name_is_required_and_short(service, name):
    with pytest.raises(ValidationError):
        service.add_facility(STAFF, name, 10)


def test_facility_names_are_unique_without_regard_to_case(service, hall, uow):
    with pytest.raises(ValidationError):
        service.add_facility(STAFF, "santral event HALL", 20)
    assert uow.rollbacks == 1


def test_block_makes_the_facility_unavailable(service, hall):
    block = service.add_block(STAFF, hall.id, slot(hour=9, hours=3), "Physical education class")

    assert block.reason == "Physical education class"
    assert service.is_available(hall.id, slot(hour=10)) is False
    assert service.is_available(hall.id, slot(hour=12)) is True  # [9, 12) ends where 12:00 starts
    assert service.get_blocks(hall.id, date(2026, 11, 2)) == [block]


def test_overlapping_blocks_are_rejected(service, hall):
    service.add_block(STAFF, hall.id, slot(hour=9, hours=3), "Class")

    with pytest.raises(ValidationError):
        service.add_block(STAFF, hall.id, slot(hour=11, hours=2), "Maintenance")


def test_block_over_a_booked_event_is_rejected(service, hall, events):
    events.book(hall.id, slot(hour=18, hours=2))

    with pytest.raises(FacilityConflictError):
        service.add_block(STAFF, hall.id, slot(hour=19), "Maintenance")


@pytest.mark.parametrize("reason", ["", "  ", "r" * 201])
def test_block_needs_a_short_reason(service, hall, reason):
    with pytest.raises(ValidationError):
        service.add_block(STAFF, hall.id, slot(hour=9), reason)


def test_block_must_end_after_it_starts(service, hall):
    when = slot(hour=9)
    with pytest.raises(ValidationError):
        service.add_block(STAFF, hall.id, TimeSlot(when.end, when.start), "Class")


def test_block_of_unknown_facility(service):
    with pytest.raises(NotFoundError):
        service.add_block(STAFF, 99, slot(hour=9), "Class")


# ---------------------------------------------------------------- UC-07
def test_schedule_lists_blocks_and_active_events_sorted(service, hall, events):
    service.add_block(STAFF, hall.id, slot(hour=9, hours=2), "Class")
    pending = events.book(hall.id, slot(hour=18), EventStatus.PENDING)
    full = events.book(hall.id, slot(hour=14), EventStatus.FULL)
    events.book(hall.id, slot(hour=20), EventStatus.CANCELLED)
    events.book(hall.id, slot(hour=21), EventStatus.REJECTED)
    events.book(hall.id, slot(day=3, hour=18))  # another day

    assert service.get_schedule(hall.id, date(2026, 11, 2)) == [slot(hour=9, hours=2), full.slot, pending.slot]


@pytest.mark.parametrize("status", [EventStatus.PENDING, EventStatus.OPEN, EventStatus.FULL])
def test_active_events_hold_their_slot(service, hall, events, status):
    events.book(hall.id, slot(hour=18), status)

    assert service.is_available(hall.id, slot(hour=18)) is False


@pytest.mark.parametrize("status", [EventStatus.CANCELLED, EventStatus.REJECTED, EventStatus.COMPLETED])
def test_inactive_events_free_their_slot(service, hall, events, status):
    events.book(hall.id, slot(hour=18), status)

    assert service.is_available(hall.id, slot(hour=18)) is True


def test_slot_over_midnight_sees_a_block_on_the_next_day(service, hall):
    service.add_block(STAFF, hall.id, slot(day=3, hour=0, hours=2), "Cleaning")

    assert service.is_available(hall.id, slot(day=2, hour=23, hours=2)) is False


def test_list_facilities_sorted_by_name(service):
    service.add_facility(STAFF, "Tennis Court", 4)
    service.add_facility(STAFF, "basketball Court", 20)

    assert [f.name for f in service.list_facilities()] == ["basketball Court", "Tennis Court"]


def test_unknown_facility_is_reported(service):
    with pytest.raises(NotFoundError):
        service.get_schedule(99, date(2026, 11, 2))
    with pytest.raises(NotFoundError):
        service.is_available(99, slot())


# ---------------------------------------------------------------- check_bookable (used by UC-04)
def test_check_bookable_returns_the_facility(service, hall):
    assert service.check_bookable(hall.id, slot(hour=18), 10) == hall


def test_check_bookable_refuses_more_people_than_the_facility_holds(service, hall):
    with pytest.raises(ValidationError):
        service.check_bookable(hall.id, slot(hour=18), 51)


def test_check_bookable_refuses_busy_slots(service, hall, events):
    service.add_block(STAFF, hall.id, slot(hour=9, hours=3), "Class")
    events.book(hall.id, slot(hour=18, hours=2), EventStatus.PENDING)

    with pytest.raises(FacilityConflictError):
        service.check_bookable(hall.id, slot(hour=10), 6)
    with pytest.raises(FacilityConflictError):
        service.check_bookable(hall.id, slot(hour=19), 6)


def test_check_bookable_unknown_facility(service):
    with pytest.raises(NotFoundError):
        service.check_bookable(99, slot(), 6)


# ---------------------------------------------------------------- UC-08 alt. 2b: remove a block (issue #19)
def test_blocks_get_an_id(service, hall):
    first = service.add_block(STAFF, hall.id, slot(hour=9), "Class")
    second = service.add_block(STAFF, hall.id, slot(hour=11), "Class")

    assert first.id is not None and second.id is not None and first.id != second.id
    assert service.get_block(first.id) == first


def test_staff_removes_a_block_and_the_time_is_free_again(service, hall, uow):
    block = service.add_block(STAFF, hall.id, slot(hour=9, hours=3), "Added by mistake")

    removed = service.remove_block(STAFF, block.id)

    assert removed == block
    assert service.get_blocks(hall.id, date(2026, 11, 2)) == []
    assert service.is_available(hall.id, slot(hour=10)) is True
    assert service.check_bookable(hall.id, slot(hour=10), 6) == hall
    assert uow.commits == 3  # add facility, add block, remove block


def test_student_cannot_remove_a_block(service, hall):
    block = service.add_block(STAFF, hall.id, slot(hour=9), "Class")

    with pytest.raises(PermissionDeniedError):
        service.remove_block(STUDENT, block.id)
    assert service.get_blocks(hall.id, date(2026, 11, 2)) == [block]


def test_removing_an_unknown_block(service, hall, uow):
    with pytest.raises(NotFoundError):
        service.remove_block(STAFF, 99)
    assert uow.rollbacks == 1


def test_a_removed_block_cannot_be_removed_twice(service, hall):
    block = service.add_block(STAFF, hall.id, slot(hour=9), "Class")
    service.remove_block(STAFF, block.id)

    with pytest.raises(NotFoundError):
        service.remove_block(STAFF, block.id)


# ---------------------------------------------------------------- bookings with titles (page shows them)
def test_get_bookings_lists_active_events_of_the_day_sorted(service, hall, events):
    late = events.book(hall.id, slot(hour=20), EventStatus.PENDING)
    early = events.book(hall.id, slot(hour=14), EventStatus.OPEN)
    events.book(hall.id, slot(hour=16), EventStatus.CANCELLED)

    assert service.get_bookings(hall.id, date(2026, 11, 2)) == [early, late]
    with pytest.raises(NotFoundError):
        service.get_bookings(99, date(2026, 11, 2))
