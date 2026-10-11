"""UC-07 AI skill-based team balancing (Gemini Pro)."""

from __future__ import annotations

from typing import Protocol

from campusevent.matches import MatchService
from campusevent.models import Profile
from campusevent.profiles import ProfileService


class SkillRatingClient(Protocol):
    """Wraps the AI model that turns profile data into a numeric skill rating."""

    def rate_players(self, sport: str, profiles: list[Profile]) -> dict[int, float]: ...


class MatchmakingService:
    def __init__(
        self,
        matches: MatchService,
        profiles: ProfileService,
        ai_client: SkillRatingClient | None,
    ) -> None:
        self.matches = matches
        self.profiles = profiles
        self.ai_client = ai_client

    def balance_teams(self, match_id: int, team_count: int = 2) -> list[list[int]]:
        """Split the match participants into teams with similar total skill."""
        raise NotImplementedError
