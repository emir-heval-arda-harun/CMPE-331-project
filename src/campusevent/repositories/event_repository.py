"""Event storage for task 3.4 (UC-04 to UC-06, UC-09 to UC-11).

``EventRepository`` is the interface used by ``EventService``. ``active_on`` is also the method
``FacilityService`` needs (see ``ActiveEventSource`` in facilities.py), so the same repository
object is passed to both services in app.py.
"""

from __future__ import annotations

import copy
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, scoped_session, selectinload

from campusevent.exceptions import FacilityConflictError, NotFoundError
from campusevent.models import Event, EventStatus, TimeSlot
from campusevent.repositories.tables import ACTIVE_EVENT_STATUSES, EventParticipantRow, EventRow

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

    def list_by_organizer(self, user_id: int) -> list[Event]:
        """Every event the user organized, in any status."""
        ...

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

    def list_by_organizer(self, user_id: int) -> list[Event]:
        return [copy.deepcopy(e) for e in self._events.values() if e.organizer_id == user_id]

    def active_on(self, facility_id: int, day: date) -> list[Event]:
        whole_day = TimeSlot(datetime.combine(day, time.min), datetime.combine(day, time.min) + timedelta(days=1))
        return [
            copy.deepcopy(e)
            for e in self._events.values()
            if e.facility_id == facility_id and e.status in ACTIVE_STATUSES and e.slot.overlaps(whole_day)
        ]


# --------------------------------------------------------------------------- #
# PostgreSQL (production). Same pattern as docs/database/README.md "Writing a Sql*Repository".
# --------------------------------------------------------------------------- #
def _to_db(value: datetime) -> datetime:
    """Naive UTC (domain) -> timezone-aware UTC (timestamptz column)."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _from_db(value: datetime) -> datetime:
    """timestamptz from the database -> naive UTC (domain)."""
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _translate(error: IntegrityError) -> None:
    """Turn a known constraint violation into a domain error; other errors are re-raised by the caller."""
    constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
    if constraint == "ex_event_facility_no_overlap":  # BR-06, BR-16
        raise FacilityConflictError("The facility is not available in this time slot.") from error


class SqlEventRepository:
    def __init__(self, session: scoped_session[Session]) -> None:
        self.session = session

    # ------------------------------------------------------------------ #
    def add(self, event: Event) -> Event:
        row = EventRow(
            organizer_id=event.organizer_id,
            facility_id=event.facility_id,
            title=event.title,
            category=event.category,
            description=event.description,
            start_time=_to_db(event.slot.start),
            end_time=_to_db(event.slot.end),
            capacity=event.capacity,
            status=event.status.value,
            reviewed_by=event.reviewed_by,
            reviewed_at=_to_db(event.reviewed_at) if event.reviewed_at else None,
            rejection_reason=event.rejection_reason,
        )
        row.participants = [
            EventParticipantRow(user_id=user_id, joined_at=datetime.now(timezone.utc))
            for user_id in event.participant_ids
        ]
        try:
            self.session.add(row)
            self.session.flush()  # constraint errors come out here, inside the repository
        except IntegrityError as error:
            _translate(error)
            raise
        return self._to_domain(row)

    def get(self, event_id: int) -> Event:
        return self._to_domain(self._get_row(event_id))

    def get_for_update(self, event_id: int) -> Event:
        """SELECT ... FOR UPDATE: join/leave/cancel on one event run one after the other."""
        return self._to_domain(self._get_row(event_id, for_update=True))

    def save(self, event: Event) -> None:
        row = self._get_row(event.id)
        row.facility_id = event.facility_id
        row.title = event.title
        row.category = event.category
        row.description = event.description
        row.start_time = _to_db(event.slot.start)
        row.end_time = _to_db(event.slot.end)
        row.capacity = event.capacity
        row.status = event.status.value
        row.reviewed_by = event.reviewed_by
        row.reviewed_at = _to_db(event.reviewed_at) if event.reviewed_at else None
        row.rejection_reason = event.rejection_reason

        wanted = list(event.participant_ids)
        for participant in list(row.participants):
            if participant.user_id not in wanted:
                row.participants.remove(participant)  # delete-orphan removes the row
        present = {participant.user_id for participant in row.participants}
        for user_id in wanted:
            if user_id not in present:
                row.participants.append(EventParticipantRow(user_id=user_id, joined_at=datetime.now(timezone.utc)))
        try:
            self.session.flush()
        except IntegrityError as error:
            _translate(error)
            raise

    # ------------------------------------------------------------------ #
    def list_by_status(self, statuses: Iterable[EventStatus]) -> list[Event]:
        values = [EventStatus(s).value for s in statuses]
        stmt = (
            select(EventRow)
            .options(selectinload(EventRow.participants))
            .where(EventRow.status.in_(values))
            .order_by(EventRow.start_time, EventRow.id)
        )
        return [self._to_domain(row) for row in self.session.scalars(stmt)]

    def list_by_participant(self, user_id: int) -> list[Event]:
        stmt = (
            select(EventRow)
            .options(selectinload(EventRow.participants))
            .join(EventParticipantRow, EventParticipantRow.event_id == EventRow.id)
            .where(EventParticipantRow.user_id == user_id)
            .order_by(EventRow.start_time, EventRow.id)
        )
        return [self._to_domain(row) for row in self.session.scalars(stmt)]

    def list_by_organizer(self, user_id: int) -> list[Event]:
        stmt = (
            select(EventRow)
            .options(selectinload(EventRow.participants))
            .where(EventRow.organizer_id == user_id)
            .order_by(EventRow.start_time, EventRow.id)
        )
        return [self._to_domain(row) for row in self.session.scalars(stmt)]

    def active_on(self, facility_id: int, day: date) -> list[Event]:
        """Pending/open/full events of the facility that overlap that UTC day (index ix_event_facility_id_start_time)."""
        day_start = datetime.combine(day, time.min, tzinfo=timezone.utc)
        stmt = (
            select(EventRow)
            .options(selectinload(EventRow.participants))
            .where(
                EventRow.facility_id == facility_id,
                EventRow.status.in_(ACTIVE_EVENT_STATUSES),
                EventRow.start_time < day_start + timedelta(days=1),
                EventRow.end_time > day_start,
            )
            .order_by(EventRow.start_time, EventRow.id)
        )
        return [self._to_domain(row) for row in self.session.scalars(stmt)]

    # ------------------------------------------------------------------ #
    def _get_row(self, event_id: int, for_update: bool = False) -> EventRow:
        if for_update:
            row = self.session.get(EventRow, event_id, with_for_update=True, populate_existing=True)
        else:
            row = self.session.get(EventRow, event_id)
        if row is None:
            raise NotFoundError(f"Event {event_id} does not exist")
        return row

    @staticmethod
    def _to_domain(row: EventRow) -> Event:
        return Event(
            id=row.id,
            organizer_id=row.organizer_id,
            title=row.title,
            category=row.category,
            facility_id=row.facility_id,
            slot=TimeSlot(_from_db(row.start_time), _from_db(row.end_time)),
            capacity=row.capacity,
            description=row.description or "",
            participant_ids=[p.user_id for p in row.participants],
            status=EventStatus(row.status),
            reviewed_by=row.reviewed_by,
            reviewed_at=_from_db(row.reviewed_at) if row.reviewed_at else None,
            rejection_reason=row.rejection_reason or "",
        )
