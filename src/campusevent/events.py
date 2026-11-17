"""UC-04 Create event, UC-05 Browse & filter, UC-06 Join event, UC-09 Activity history,
UC-10 Leave event, UC-11 Cancel event, UC-12 Review event requests."""

from __future__ import annotations

from datetime import date, datetime

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
        """Create an event request with status PENDING. It holds the facility slot but is
        not listed until an admin approves it (UC-12)."""
        raise NotImplementedError

    def search_events(
        self,
        category: str | None = None,
        day: date | None = None,
        keyword: str | None = None,
        only_open: bool = True,
    ) -> list[Event]:
        raise NotImplementedError

    def list_pending_events(self, admin_id: int) -> list[Event]:
        """UC-12: all PENDING requests, oldest start time first. Admins only."""
        raise NotImplementedError

    def approve_event(self, event_id: int, admin_id: int) -> Event:
        """UC-12: PENDING -> OPEN, the event becomes visible; the organizer is e-mailed."""
        raise NotImplementedError

    def reject_event(self, event_id: int, admin_id: int, reason: str) -> Event:
        """UC-12: PENDING -> REJECTED with a reason; the facility slot is freed and the
        organizer is e-mailed. The organizer may submit a corrected request (UC-04)."""
        raise NotImplementedError

    def expire_pending_requests(self, now: datetime) -> list[Event]:
        """UC-12: requests still PENDING at their start time become REJECTED automatically."""
        raise NotImplementedError

    def list_my_requests(self, organizer_id: int) -> list[Event]:
        """UC-12: every event the user organized, in any status, so the organizer can follow
        pending, approved and rejected requests."""
        raise NotImplementedError

    def join_event(self, event_id: int, user_id: int) -> Event:
        raise NotImplementedError

    def leave_event(self, event_id: int, user_id: int) -> Event:
        raise NotImplementedError

    def cancel_event(self, event_id: int, user_id: int) -> Event:
        """UC-11: the organizer cancels an OPEN/FULL event or withdraws a PENDING request."""
        raise NotImplementedError

    def complete_event(self, event_id: int) -> Event:
        raise NotImplementedError

    def get_activity_history(self, user_id: int) -> list[ActivityRecord]:
        raise NotImplementedError
