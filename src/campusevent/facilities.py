"""UC-11 View facility schedule & conflict check, UC-12 Manage facility schedule."""

from __future__ import annotations

from datetime import date

from campusevent.auth import AuthService
from campusevent.models import Facility, FacilityBlock, TimeSlot


class FacilityService:
    def __init__(self, auth: AuthService) -> None:
        self.auth = auth

    def add_facility(self, staff_id: int, name: str, sports: list[str]) -> Facility:
        raise NotImplementedError

    def add_block(self, staff_id: int, facility_id: int, slot: TimeSlot, reason: str) -> FacilityBlock:
        """Mark a facility as unavailable (class hours, maintenance, ...)."""
        raise NotImplementedError

    def get_schedule(self, facility_id: int, day: date) -> list[TimeSlot]:
        """Return every busy slot (blocks and matches) of the facility on that day."""
        raise NotImplementedError

    def is_available(self, facility_id: int, slot: TimeSlot) -> bool:
        raise NotImplementedError
