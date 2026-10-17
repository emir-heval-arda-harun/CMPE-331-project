"""Domain models shared by all CampusEvent services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    STUDENT = "student"
    FACILITY_STAFF = "facility_staff"


class EventStatus(str, Enum):
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
    status: EventStatus = EventStatus.OPEN


@dataclass
class ActivityRecord:
    event_id: int
    title: str
    category: str
    slot: TimeSlot
    facility_id: int
