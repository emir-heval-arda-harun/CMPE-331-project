"""UC-04 Create event, UC-05 Browse & filter, UC-06 Join event, UC-09 Activity history,
UC-10 Leave event, UC-11 Cancel event."""

from __future__ import annotations

from datetime import date

from campusevent.auth import AuthService
from campusevent.facilities import FacilityService
from campusevent.models import ActivityRecord, Event, TimeSlot


class EventService:
    def __init__(self, auth: AuthService, facilities: FacilityService) -> None:
        self.auth = auth
        self.facilities = facilities

    def create_event(
        self,
        organizer_id: int,
        title: str,
        category: str,
        facility_id: int,
        slot: TimeSlot,
        capacity: int,
        description: str = "",
    ) -> Event:
        raise NotImplementedError

    def search_events(
        self,
        category: str | None = None,
        day: date | None = None,
        keyword: str | None = None,
        only_open: bool = True,
    ) -> list[Event]:
        raise NotImplementedError

    def join_event(self, event_id: int, user_id: int) -> Event:
        raise NotImplementedError

    def leave_event(self, event_id: int, user_id: int) -> Event:
        raise NotImplementedError

    def cancel_event(self, event_id: int, user_id: int) -> Event:
        raise NotImplementedError

    def complete_event(self, event_id: int) -> Event:
        raise NotImplementedError

    def get_activity_history(self, user_id: int) -> list[ActivityRecord]:
        raise NotImplementedError
