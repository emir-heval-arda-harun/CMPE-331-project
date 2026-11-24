"""ProfileRepository: interests and availability of a student (layer 3, UC-03).

A profile has no row of its own: it is the ``profile_interest`` and ``availability_slot`` rows of a user
(Software Design Report, section 6). ``save`` replaces all of them, as in the UC-03 sequence diagram.

``InMemoryProfileRepository`` is used by the requirement tests, ``SqlProfileRepository`` in production.
The SQL version returns the interests in alphabetical order, because the table keeps no order; the
in-memory version keeps the order they were saved in. Both return the slots by start time.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, scoped_session

from campusevent.models import Profile, TimeSlot
from campusevent.repositories.facility_repository import _from_db, _to_db  # the team time rule (naive UTC)
from campusevent.repositories.tables import AvailabilitySlotRow, ProfileInterestRow


class ProfileRepository(Protocol):
    def get(self, user_id: int) -> Profile:
        """The stored profile, or an empty one if the user has not saved a profile yet."""
        ...

    def save(self, profile: Profile) -> None:
        """Replace all interests and availability slots of ``profile.user_id``."""
        ...


class InMemoryProfileRepository:
    """Profiles kept in a dictionary (requirement tests and development). Hands out copies."""

    def __init__(self) -> None:
        self._profiles: dict[int, Profile] = {}

    def get(self, user_id: int) -> Profile:
        stored = self._profiles.get(user_id)
        if stored is None:
            return Profile(user_id=user_id)
        return Profile(user_id, list(stored.interests), list(stored.availability))

    def save(self, profile: Profile) -> None:
        self._profiles[profile.user_id] = Profile(
            profile.user_id, list(profile.interests), sorted(profile.availability, key=lambda s: (s.start, s.end))
        )


# --------------------------------------------------------------------------- #
# PostgreSQL
# --------------------------------------------------------------------------- #
class SqlProfileRepository:
    """Profiles in PostgreSQL. Shares the scoped session of ``SqlUnitOfWork`` (one transaction per request)."""

    def __init__(self, session: scoped_session[Session]) -> None:
        self.session = session

    def get(self, user_id: int) -> Profile:
        interests = self.session.scalars(
            select(ProfileInterestRow.interest)
            .where(ProfileInterestRow.user_id == user_id)
            .order_by(ProfileInterestRow.interest)
        ).all()
        slots = self.session.scalars(
            select(AvailabilitySlotRow)
            .where(AvailabilitySlotRow.user_id == user_id)
            .order_by(AvailabilitySlotRow.start_time, AvailabilitySlotRow.end_time, AvailabilitySlotRow.id)
        ).all()
        return Profile(
            user_id=user_id,
            interests=list(interests),
            availability=[TimeSlot(_from_db(row.start_time), _from_db(row.end_time)) for row in slots],
        )

    def save(self, profile: Profile) -> None:
        # Delete first and flush, so an interest that is kept is not inserted while its old row still exists.
        self.session.execute(delete(ProfileInterestRow).where(ProfileInterestRow.user_id == profile.user_id))
        self.session.execute(delete(AvailabilitySlotRow).where(AvailabilitySlotRow.user_id == profile.user_id))
        self.session.add_all(
            [ProfileInterestRow(user_id=profile.user_id, interest=interest) for interest in profile.interests]
            + [
                AvailabilitySlotRow(user_id=profile.user_id, start_time=_to_db(s.start), end_time=_to_db(s.end))
                for s in profile.availability
            ]
        )
        self.session.flush()  # constraint errors come out here, inside the repository
