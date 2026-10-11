"""Domain models shared by all CampusEvent services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum


class Role(str, Enum):
    STUDENT = "student"
    CLUB_REPRESENTATIVE = "club_representative"
    FACILITY_STAFF = "facility_staff"


class SkillLevel(IntEnum):
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3


class MatchStatus(str, Enum):
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
    sports: dict[str, SkillLevel] = field(default_factory=dict)
    availability: list[TimeSlot] = field(default_factory=list)


@dataclass
class Facility:
    id: int
    name: str
    sports: list[str]


@dataclass
class FacilityBlock:
    """A period in which a facility cannot be used (class, maintenance, ...)."""

    facility_id: int
    slot: TimeSlot
    reason: str


@dataclass
class Match:
    id: int
    organizer_id: int
    sport: str
    facility_id: int
    slot: TimeSlot
    capacity: int
    skill_level: SkillLevel
    participant_ids: list[int] = field(default_factory=list)
    status: MatchStatus = MatchStatus.OPEN


@dataclass
class BracketMatch:
    id: int
    round_number: int
    team_a: str | None
    team_b: str | None
    score_a: int | None = None
    score_b: int | None = None
    winner: str | None = None


@dataclass
class Tournament:
    id: int
    organizer_id: int
    name: str
    sport: str
    teams: list[str]
    bracket: list[BracketMatch] = field(default_factory=list)
    champion: str | None = None


@dataclass
class ActivityRecord:
    match_id: int
    sport: str
    slot: TimeSlot
    facility_id: int
