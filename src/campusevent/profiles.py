"""UC-03 Manage profile (interests and availability).

Business rules:
- BR-14: interests are free text; they are trimmed and compared without regard to upper or lower case,
  so "Football " and "football" are one interest. They are stored in lower case.
- UC-03 5a: at least one interest. UC-03 5b: a slot must end after it starts.
- NFR-04: only students have a profile they can change (the route checks it too).
"""

from __future__ import annotations

from campusevent.auth import AuthService
from campusevent.exceptions import ValidationError
from campusevent.models import Profile, Role, TimeSlot
from campusevent.repositories.profile_repository import InMemoryProfileRepository, ProfileRepository
from campusevent.repositories.unit_of_work import InMemoryUnitOfWork, UnitOfWork

INTEREST_MAX = 60  # profile_interest.interest is VARCHAR(60), like the field on the profile page


class ProfileService:
    def __init__(
        self,
        auth: AuthService,
        profiles: ProfileRepository | None = None,
        uow: UnitOfWork | None = None,
    ) -> None:
        self.auth = auth
        self.profiles = profiles if profiles is not None else InMemoryProfileRepository()
        self.uow = uow if uow is not None else InMemoryUnitOfWork()

    def update_profile(
        self,
        user_id: int,
        interests: list[str],
        availability: list[TimeSlot],
    ) -> Profile:
        """Replace the interests and availability of a student. Nothing is saved if anything is invalid."""
        self.auth.require_role(user_id, Role.STUDENT)  # NFR-04
        profile = Profile(user_id=user_id, interests=_clean_interests(interests), availability=_check_slots(availability))

        self.uow.begin()
        try:
            self.profiles.save(profile)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return self.profiles.get(user_id)

    def get_profile(self, user_id: int) -> Profile:
        """The profile of a user; empty if nothing is saved yet. Raises ``NotFoundError`` for an unknown user."""
        self.auth.get_user(user_id)
        return self.profiles.get(user_id)


def _clean_interests(interests: list[str]) -> list[str]:
    """Trim, join inner spaces, lower-case and drop repeats, keeping the order the student gave (BR-14)."""
    cleaned: list[str] = []
    for interest in interests or []:
        if not isinstance(interest, str):
            raise ValidationError("Interests must be text.")
        # Turkish capital İ: str.lower() gives "i" + a combining dot, so map it to a plain "i" first.
        interest = " ".join(interest.split()).replace("İ", "i").lower()
        if not interest or interest in cleaned:
            continue
        if len(interest) > INTEREST_MAX:
            raise ValidationError(f'"{interest[:20]}…" is too long: an interest can be at most {INTEREST_MAX} characters.')
        cleaned.append(interest)
    if not cleaned:
        raise ValidationError("Add at least one interest.")  # UC-03 5a
    return cleaned


def _check_slots(availability: list[TimeSlot]) -> list[TimeSlot]:
    """Every slot must end after it starts (UC-03 5b). Returned by start time; a repeated slot is kept once."""
    slots: list[TimeSlot] = []
    for slot in availability or []:
        if not isinstance(slot, TimeSlot):
            raise ValidationError("Please enter a valid date and time.")
        if slot.end <= slot.start:
            raise ValidationError("The end time must be after the start time.")
        if slot not in slots:
            slots.append(slot)
    return sorted(slots, key=lambda s: (s.start, s.end))
