"""UC-08 Create tournament, UC-09 Generate bracket, UC-10 Record score & advance."""

from __future__ import annotations

from campusevent.auth import AuthService
from campusevent.models import BracketMatch, Tournament


class TournamentService:
    def __init__(self, auth: AuthService) -> None:
        self.auth = auth

    def create_tournament(self, organizer_id: int, name: str, sport: str, teams: list[str]) -> Tournament:
        raise NotImplementedError

    def generate_bracket(self, tournament_id: int) -> list[BracketMatch]:
        """Create a single-elimination bracket; byes are added when needed."""
        raise NotImplementedError

    def record_score(self, organizer_id: int, bracket_match_id: int, score_a: int, score_b: int) -> BracketMatch:
        """Store the result and move the winner to the next round."""
        raise NotImplementedError

    def get_tournament(self, tournament_id: int) -> Tournament:
        raise NotImplementedError
