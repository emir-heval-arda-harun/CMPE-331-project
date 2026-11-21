"""FacilityRepository: facilities and their blocks (layer 3, task 3.3, UC-07 and UC-08).

``InMemoryFacilityRepository`` is used by the requirement tests, ``SqlFacilityRepository`` in
production. Both return the domain objects of ``campusevent.models``; the services never see a
``*Row``.

Times: the domain uses naive datetimes in UTC (``tests/helpers.slot``). The SQL repository stores
them as ``timestamptz`` in UTC and turns the values it reads back into naive UTC.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, scoped_session

from campusevent.exceptions import NotFoundError, ValidationError
from campusevent.models import Facility, FacilityBlock, TimeSlot
from campusevent.repositories.tables import FacilityBlockRow, FacilityRow


def day_range(day: date) -> tuple[datetime, datetime]:
    """The half-open range ``[day 00:00, next day 00:00)`` of one day."""
    start = datetime.combine(day, time.min)
    return start, start + timedelta(days=1)


class FacilityRepository(Protocol):
    def add(self, facility: Facility, manager_id: int) -> Facility:
        """Store a new facility; the ``id`` of the argument is ignored and the stored facility returned."""
        ...

    def get(self, facility_id: int) -> Facility:
        """Raise ``NotFoundError`` for an unknown id."""
        ...

    def get_for_update(self, facility_id: int) -> Facility:
        """Like ``get`` but locks the facility row until the end of the transaction (SELECT ... FOR UPDATE)."""
        ...

    def find_by_name(self, name: str) -> Facility | None:
        """Case-insensitive lookup, ``None`` if there is no such facility."""
        ...

    def list_all(self) -> list[Facility]:
        """All facilities, sorted by name."""
        ...

    def add_block(self, block: FacilityBlock, created_by: int) -> FacilityBlock:
        """Store a new block; returns it with its ``id``."""
        ...

    def get_block(self, block_id: int) -> FacilityBlock:
        """Raise ``NotFoundError`` for an unknown id."""
        ...

    def remove_block(self, block_id: int) -> None:
        """Delete the block; raise ``NotFoundError`` for an unknown id."""
        ...

    def blocks_on(self, facility_id: int, day: date) -> list[FacilityBlock]:
        """Blocks of the facility that overlap that day, sorted by start time."""
        ...


class InMemoryFacilityRepository:
    """Facilities kept in dictionaries (requirement tests and development)."""

    def __init__(self) -> None:
        self._facilities: dict[int, Facility] = {}
        self._managers: dict[int, int] = {}
        self._blocks: dict[int, tuple[FacilityBlock, int]] = {}  # block id -> (block, created_by)
        self._next_id = 1
        self._next_block_id = 1

    def add(self, facility: Facility, manager_id: int) -> Facility:
        stored = Facility(id=self._next_id, name=facility.name, capacity=facility.capacity)
        self._next_id += 1
        self._facilities[stored.id] = stored
        self._managers[stored.id] = manager_id
        return stored

    def get(self, facility_id: int) -> Facility:
        try:
            return self._facilities[facility_id]
        except KeyError:
            raise NotFoundError(f"Facility {facility_id} does not exist") from None

    def get_for_update(self, facility_id: int) -> Facility:
        return self.get(facility_id)  # no concurrent requests in memory, so nothing to lock

    def find_by_name(self, name: str) -> Facility | None:
        wanted = name.strip().lower()
        return next((f for f in self._facilities.values() if f.name.lower() == wanted), None)

    def list_all(self) -> list[Facility]:
        return sorted(self._facilities.values(), key=lambda f: f.name.lower())

    def add_block(self, block: FacilityBlock, created_by: int) -> FacilityBlock:
        self.get(block.facility_id)
        stored = FacilityBlock(block.facility_id, block.slot, block.reason, id=self._next_block_id)
        self._next_block_id += 1
        self._blocks[stored.id] = (stored, created_by)
        return stored

    def get_block(self, block_id: int) -> FacilityBlock:
        try:
            return self._blocks[block_id][0]
        except KeyError:
            raise NotFoundError(f"Block {block_id} does not exist") from None

    def remove_block(self, block_id: int) -> None:
        self.get_block(block_id)
        del self._blocks[block_id]

    def blocks_on(self, facility_id: int, day: date) -> list[FacilityBlock]:
        whole_day = TimeSlot(*day_range(day))
        found = [b for b, _ in self._blocks.values() if b.facility_id == facility_id and b.slot.overlaps(whole_day)]
        return sorted(found, key=lambda b: b.slot.start)


# --------------------------------------------------------------------------- #
# PostgreSQL
# --------------------------------------------------------------------------- #
def _to_db(value: datetime) -> datetime:
    """Naive UTC (domain) -> aware UTC (timestamptz)."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _from_db(value: datetime) -> datetime:
    """Aware datetime from PostgreSQL -> naive UTC (domain)."""
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


class SqlFacilityRepository:
    """Facilities in PostgreSQL. Shares the scoped session of ``SqlUnitOfWork`` (one transaction per request)."""

    def __init__(self, session: scoped_session[Session]) -> None:
        self.session = session

    @staticmethod
    def _facility(row: FacilityRow) -> Facility:
        return Facility(id=row.id, name=row.name, capacity=row.capacity)

    @staticmethod
    def _block(row: FacilityBlockRow) -> FacilityBlock:
        return FacilityBlock(
            facility_id=row.facility_id,
            slot=TimeSlot(_from_db(row.start_time), _from_db(row.end_time)),
            reason=row.reason,
            id=row.id,
        )

    def add(self, facility: Facility, manager_id: int) -> Facility:

        row = FacilityRow(manager_id=manager_id, name=facility.name, capacity=facility.capacity)
        try:
            self.session.add(row)
            self.session.flush()  # constraint errors come out here, inside the repository
        except IntegrityError as error:  # the service's UnitOfWork rolls the transaction back
            if _constraint(error) == "uq_facility_name":
                raise ValidationError(f'A facility named "{facility.name}" already exists') from error
            raise
        return self._facility(row)

    def get(self, facility_id: int) -> Facility:

        row = self.session.get(FacilityRow, facility_id)
        if row is None:
            raise NotFoundError(f"Facility {facility_id} does not exist")
        return self._facility(row)

    def get_for_update(self, facility_id: int) -> Facility:

        row = self.session.get(FacilityRow, facility_id, with_for_update=True)  # SELECT ... FOR UPDATE
        if row is None:
            raise NotFoundError(f"Facility {facility_id} does not exist")
        return self._facility(row)

    def find_by_name(self, name: str) -> Facility | None:

        row = self.session.scalars(
            select(FacilityRow).where(func.lower(FacilityRow.name) == name.strip().lower())
        ).first()
        return self._facility(row) if row else None

    def list_all(self) -> list[Facility]:

        rows = self.session.scalars(select(FacilityRow).order_by(func.lower(FacilityRow.name)))
        return [self._facility(row) for row in rows]

    def add_block(self, block: FacilityBlock, created_by: int) -> FacilityBlock:

        row = FacilityBlockRow(
            facility_id=block.facility_id,
            created_by=created_by,
            start_time=_to_db(block.slot.start),
            end_time=_to_db(block.slot.end),
            reason=block.reason,
        )
        try:
            self.session.add(row)
            self.session.flush()
        except IntegrityError as error:
            if _constraint(error) == "ex_facility_block_no_overlap":
                raise ValidationError("The block overlaps another block of this facility") from error
            raise
        return self._block(row)

    def get_block(self, block_id: int) -> FacilityBlock:
        row = self.session.get(FacilityBlockRow, block_id)
        if row is None:
            raise NotFoundError(f"Block {block_id} does not exist")
        return self._block(row)

    def remove_block(self, block_id: int) -> None:
        row = self.session.get(FacilityBlockRow, block_id)
        if row is None:
            raise NotFoundError(f"Block {block_id} does not exist")
        self.session.delete(row)
        self.session.flush()

    def blocks_on(self, facility_id: int, day: date) -> list[FacilityBlock]:
        start, end = (_to_db(value) for value in day_range(day))
        rows = self.session.scalars(
            select(FacilityBlockRow)
            .where(
                FacilityBlockRow.facility_id == facility_id,
                FacilityBlockRow.start_time < end,
                FacilityBlockRow.end_time > start,
            )
            .order_by(FacilityBlockRow.start_time)
        )
        return [self._block(row) for row in rows]


def _constraint(error: IntegrityError) -> str | None:
    diag = getattr(error.orig, "diag", None)
    return getattr(diag, "constraint_name", None)
