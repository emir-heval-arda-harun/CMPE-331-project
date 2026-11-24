"""Domain models shared by all CampusEvent services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    STUDENT = "student"
    FACILITY_STAFF = "facility_staff"
    ADMIN = "admin"  # reviews event requests (UC-12)


class EventStatus(str, Enum):
    PENDING = "pending"  # waiting for admin review (UC-12); holds the facility slot, not listed
    REJECTED = "rejected"  # refused by an admin or not reviewed before the start time
    OPEN = "open"
    FULL = "full"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TimeSlot:
    start: datetime
    end: datetime

    def overlaps(self, other: TimeSlot) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass
class User:
    id: int
    email: str
    full_name: str
    role: Role = Role.STUDENT
    is_verified: bool = False


@dataclass
class VerificationCode:
    """A one-time e-mail verification code (UC-01). Only its hash is stored; the code itself is only in
    the e-mail. Only the latest code of a user counts, so sending a new code makes the older ones useless."""

    id: int
    user_id: int
    code_hash: str
    expires_at: datetime  # naive UTC, 15 minutes after sending
    used: bool = False
    attempts: int = 0  # wrong codes typed for this code; after 5 it stops working (pentest P2, #30)

    def is_valid(self, now: datetime) -> bool:
        return not self.used and now < self.expires_at


@dataclass
class Profile:
    user_id: int
    interests: list[str] = field(default_factory=list)  # free-text event categories
    availability: list[TimeSlot] = field(default_factory=list)


@dataclass
class Facility:
    id: int
    name: str
    capacity: int


@dataclass
class FacilityBlock:
    """A period in which a facility cannot be used (class, maintenance, ...)."""

    facility_id: int
    slot: TimeSlot
    reason: str
    id: int | None = None  # given by the repository when the block is stored


@dataclass
class Event:
    id: int
    organizer_id: int
    title: str
    category: str  # free text, for example "football", "study group", "board games"
    facility_id: int
    slot: TimeSlot
    capacity: int
    description: str = ""
    participant_ids: list[int] = field(default_factory=list)
    status: EventStatus = EventStatus.PENDING
    reviewed_by: int | None = None  # admin who approved/rejected; None if not reviewed or expired
    reviewed_at: datetime | None = None
    rejection_reason: str = ""


@dataclass
class ActivityRecord:
    event_id: int
    title: str
    category: str
    slot: TimeSlot
    facility_id: int
