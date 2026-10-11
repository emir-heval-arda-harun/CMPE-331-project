"""UC-03 Manage profile."""

from __future__ import annotations

from campusevent.auth import AuthService
from campusevent.models import Profile, SkillLevel, TimeSlot


class ProfileService:
    def __init__(self, auth: AuthService) -> None:
        self.auth = auth

    def update_profile(
        self,
        user_id: int,
        sports: dict[str, SkillLevel],
        availability: list[TimeSlot],
    ) -> Profile:
        raise NotImplementedError

    def get_profile(self, user_id: int) -> Profile:
        raise NotImplementedError
