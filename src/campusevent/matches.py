"""UC-04 Create match, UC-05 Browse & filter, UC-06 Join match, UC-13 Activity history."""

from __future__ import annotations

from datetime import date

from campusevent.auth import AuthService
from campusevent.facilities import FacilityService
from campusevent.models import ActivityRecord, Match, SkillLevel, TimeSlot


class MatchService:
    def __init__(self, auth: AuthService, facilities: FacilityService) -> None:
        self.auth = auth
        self.facilities = facilities

    def create_match(
        self,
        organizer_id: int,
        sport: str,
        facility_id: int,
        slot: TimeSlot,
        capacity: int,
        skill_level: SkillLevel,
    ) -> Match:
        raise NotImplementedError

    def search_matches(
        self,
        sport: str | None = None,
        day: date | None = None,
        skill_level: SkillLevel | None = None,
        only_open: bool = True,
    ) -> list[Match]:
        raise NotImplementedError

    def join_match(self, match_id: int, user_id: int) -> Match:
        raise NotImplementedError

    def complete_match(self, match_id: int) -> Match:
        raise NotImplementedError

    def get_activity_history(self, user_id: int) -> list[ActivityRecord]:
        raise NotImplementedError
