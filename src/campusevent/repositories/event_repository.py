"""Event storage for task 3.4 (UC-04 to UC-06, UC-09 to UC-11).

``EventRepository`` is the interface used by ``EventService``. ``active_on`` is also the method
``FacilityService`` needs (see ``ActiveEventSource`` in facilities.py), so the same repository
object is passed to both services in app.py.
"""

from __future__ import annotations

import copy
from datetime import date, datetime, time, timedelta
from typing import Iterable, Protocol

from campusevent.exceptions import NotFoundError
from campusevent.models import Event, EventStatus, TimeSlot

# Events in these states occupy their facility slot (BR-06, BR-16).
ACTIVE_STATUSES = (EventStatus.PENDING, EventStatus.OPEN, EventStatus.FULL)


class EventRepository(Protocol):
    def add(self, event: Event) -> Event:
        """Store a new event (its ``id`` is ignored) and return it with the new id."""
        ...

    def get(self, event_id: int) -> Event:
        """Raises ``NotFoundError`` for an unknown id."""
        ...

    def get_for_update(self, event_id: int) -> Event:
        """Like ``get`` but locks the row until the transaction ends (join/leave/cancel)."""
        ...

    def save(self, event: Event) -> None:
        """Write back the changed fields and the participant list of an existing event."""
        ...

    def list_by_status(self, statuses: Iterable[EventStatus]) -> list[Event]: ...

    def list_by_participant(self, user_id: int) -> list[Event]: ...

    def active_on(self, facility_id: int, day: date) -> list[Event]:
        """Pending, open and full events of the facility that overlap that day."""
        ...


class InMemoryEventRepository:
    def __init__(self) -> None:
        self._events: dict[int, Event] = {}
        self._next_id = 1

    def add(self, event: Event) -> Event:
        stored = copy.deepcopy(event)
        stored.id = self._next_id
        self._next_id += 1
        self._events[stored.id] = stored
        return copy.deepcopy(stored)

    def get(self, event_id: int) -> Event:
        if event_id not in self._events:
            raise NotFoundError("Event not found.")
        return copy.deepcopy(self._events[event_id])

    def get_for_update(self, event_id: int) -> Event:
        return self.get(event_id)  # no concurrency in memory

    def save(self, event: Event) -> None:
        if event.id not in self._events:
            raise NotFoundError("Event not found.")
        self._events[event.id] = copy.deepcopy(event)

    def list_by_status(self, statuses: Iterable[EventStatus]) -> list[Event]:
        wanted = set(statuses)
        return [copy.deepcopy(e) for e in self._events.values() if e.status in wanted]

    def list_by_participant(self, user_id: int) -> list[Event]:
        return [copy.deepcopy(e) for e in self._events.values() if user_id in e.participant_ids]

    def active_on(self, facility_id: int, day: date) -> list[Event]:
        whole_day = TimeSlot(datetime.combine(day, time.min), datetime.combine(day, time.min) + timedelta(days=1))
        return [
            copy.deepcopy(e)
            for e in self._events.values()
            if e.facility_id == facility_id and e.status in ACTIVE_STATUSES and e.slot.overlaps(whole_day)
        ]
