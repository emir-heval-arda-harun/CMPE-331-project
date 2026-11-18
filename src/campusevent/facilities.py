"""UC-07 View facility schedule & conflict check, UC-08 Manage facility schedule (task 3.3).

Business rules:
- BR-06: a facility cannot be used by two active events, or by an event and a block, at the same time.
- BR-09: only facility staff manage facilities and blocks.
- BR-10: blocks of one facility do not overlap each other.
- BR-16 (CR-01): a pending request holds its slot like an open or full event; rejected, cancelled
  and completed events free it.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

from campusevent.auth import AuthService
from campusevent.exceptions import FacilityConflictError, ValidationError
from campusevent.models import Event, EventStatus, Facility, FacilityBlock, Role, TimeSlot
from campusevent.repositories.facility_repository import FacilityRepository, InMemoryFacilityRepository
from campusevent.repositories.unit_of_work import InMemoryUnitOfWork, UnitOfWork

# Events in these states occupy their facility slot (BR-06, BR-16).
ACTIVE_STATUSES = (EventStatus.PENDING, EventStatus.OPEN, EventStatus.FULL)

NAME_MAX = 100  # facility.name is VARCHAR(100)
REASON_MAX = 200  # facility_block.reason is VARCHAR(200)
MIN_CAPACITY = 2  # UC-08 alt. 1b


class ActiveEventSource(Protocol):
    """The part of ``EventRepository`` (task 3.4) that FacilityService needs (class diagram: ``active_on``)."""

    def active_on(self, facility_id: int, day: date) -> list[Event]:
        """Pending, open and full events of the facility that overlap that day."""
        ...


class FacilityService:
    def __init__(
        self,
        auth: AuthService,
        facilities: FacilityRepository | None = None,
        events: ActiveEventSource | None = None,
        uow: UnitOfWork | None = None,
    ) -> None:
        self.auth = auth
        self.facilities = facilities if facilities is not None else InMemoryFacilityRepository()
        # The event repository is created in app.py together with EventService (task 3.4).
        # Until it is passed in, no event occupies a slot.
        self.events = events
        self.uow = uow if uow is not None else InMemoryUnitOfWork()

    # ------------------------------------------------------------------ #
    # UC-08 Manage facility schedule (facility staff)
    # ------------------------------------------------------------------ #
    def add_facility(self, staff_id: int, name: str, capacity: int) -> Facility:
        self.auth.require_role(staff_id, Role.FACILITY_STAFF)  # BR-09
        name = (name or "").strip()
        if not name:
            raise ValidationError("Please enter the name of the facility.")
        if len(name) > NAME_MAX:
            raise ValidationError(f"The name can be at most {NAME_MAX} characters long.")
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < MIN_CAPACITY:
            raise ValidationError(f"The capacity must be a whole number of at least {MIN_CAPACITY}.")

        self.uow.begin()
        try:
            if self.facilities.find_by_name(name) is not None:
                raise ValidationError(f'A facility named "{name}" already exists.')
            facility = self.facilities.add(Facility(id=0, name=name, capacity=capacity), manager_id=staff_id)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return facility

    def add_block(self, staff_id: int, facility_id: int, slot: TimeSlot, reason: str) -> FacilityBlock:
        """Mark a facility as unavailable (class hours, maintenance, ...)."""
        self.auth.require_role(staff_id, Role.FACILITY_STAFF)  # BR-09
        _check_slot(slot)
        reason = (reason or "").strip()
        if not reason:
            raise ValidationError("Please enter a reason for the block.")
        if len(reason) > REASON_MAX:
            raise ValidationError(f"The reason can be at most {REASON_MAX} characters long.")

        self.uow.begin()
        try:
            self.facilities.get_for_update(facility_id)  # lock: no event is booked while we check
            if any(b.slot.overlaps(slot) for b in self._blocks_during(facility_id, slot)):
                raise ValidationError("The block overlaps another block of this facility.")  # BR-10
            if any(e.slot.overlaps(slot) for e in self._events_during(facility_id, slot)):
                # BR-06: an event and a block never share a slot. The event has to be cancelled first.
                raise FacilityConflictError("An event is already booked in this time. Cancel it first.")
            block = self.facilities.add_block(FacilityBlock(facility_id, slot, reason), created_by=staff_id)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return block

    # ------------------------------------------------------------------ #
    # UC-07 View facility schedule and check conflicts
    # ------------------------------------------------------------------ #
    def list_facilities(self) -> list[Facility]:
        """All facilities sorted by name (Create Event dropdown, facility names on the pages)."""
        return self.facilities.list_all()

    def get_facility(self, facility_id: int) -> Facility:
        """Raises ``NotFoundError`` for an unknown id."""
        return self.facilities.get(facility_id)

    def get_blocks(self, facility_id: int, day: date) -> list[FacilityBlock]:
        """The blocks of one day with their reasons (Facility Management page)."""
        self.facilities.get(facility_id)
        return self.facilities.blocks_on(facility_id, day)

    def get_schedule(self, facility_id: int, day: date) -> list[TimeSlot]:
        """Return every busy slot (blocks and events) of the facility on that day."""
        self.facilities.get(facility_id)
        busy = [b.slot for b in self.facilities.blocks_on(facility_id, day)]
        busy += [e.slot for e in self._active_events(facility_id, day)]
        return sorted(set(busy), key=lambda s: (s.start, s.end))

    def is_available(self, facility_id: int, slot: TimeSlot) -> bool:
        self.facilities.get(facility_id)
        return not self._conflicts(facility_id, slot)

    def check_bookable(self, facility_id: int, slot: TimeSlot, capacity: int) -> Facility:
        """Used by ``EventService.create_event`` (UC-04) INSIDE its transaction: locks the facility
        row, then checks the slot and the capacity. Raises ``NotFoundError``, ``ValidationError``
        or ``FacilityConflictError``; returns the facility when the event can be booked."""
        facility = self.facilities.get_for_update(facility_id)
        _check_slot(slot)
        if capacity > facility.capacity:
            raise ValidationError(f"The capacity is larger than the capacity of the facility ({facility.capacity}).")
        if self._conflicts(facility_id, slot):
            raise FacilityConflictError("The facility is not available in this time slot.")
        return facility

    # ------------------------------------------------------------------ #
    def _conflicts(self, facility_id: int, slot: TimeSlot) -> bool:
        return any(b.slot.overlaps(slot) for b in self._blocks_during(facility_id, slot)) or any(
            e.slot.overlaps(slot) for e in self._events_during(facility_id, slot)
        )

    def _blocks_during(self, facility_id: int, slot: TimeSlot) -> list[FacilityBlock]:
        return [b for day in _days(slot) for b in self.facilities.blocks_on(facility_id, day)]

    def _events_during(self, facility_id: int, slot: TimeSlot) -> list[Event]:
        return [e for day in _days(slot) for e in self._active_events(facility_id, day)]

    def _active_events(self, facility_id: int, day: date) -> list[Event]:
        if self.events is None:
            return []
        return [e for e in self.events.active_on(facility_id, day) if e.status in ACTIVE_STATUSES]


def _check_slot(slot: TimeSlot) -> None:
    if slot.end <= slot.start:
        raise ValidationError("The end time must be after the start time.")


def _days(slot: TimeSlot) -> list[date]:
    """Every calendar day the half-open slot ``[start, end)`` touches."""
    last = (slot.end - timedelta(microseconds=1)).date()
    days, day = [], slot.start.date()
    while day <= last:
        days.append(day)
        day += timedelta(days=1)
    return days
