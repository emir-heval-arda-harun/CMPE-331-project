"""Wires all services together."""

from __future__ import annotations

from dataclasses import dataclass

from campusevent.auth import AuthService
from campusevent.facilities import FacilityService
from campusevent.matches import MatchService
from campusevent.matchmaking import MatchmakingService, SkillRatingClient
from campusevent.notifications import EmailSender, InMemoryEmailSender
from campusevent.profiles import ProfileService
from campusevent.tournaments import TournamentService

DEFAULT_EMAIL_DOMAINS = ("bilgiedu.net", "bilgi.edu.tr")


@dataclass
class CampusEventApp:
    auth: AuthService
    profiles: ProfileService
    facilities: FacilityService
    matches: MatchService
    matchmaking: MatchmakingService
    tournaments: TournamentService


def create_app(
    allowed_email_domains: tuple[str, ...] = DEFAULT_EMAIL_DOMAINS,
    email_sender: EmailSender | None = None,
    ai_client: SkillRatingClient | None = None,
) -> CampusEventApp:
    auth = AuthService(allowed_email_domains, email_sender or InMemoryEmailSender())
    profiles = ProfileService(auth)
    facilities = FacilityService(auth)
    matches = MatchService(auth, facilities)
    return CampusEventApp(
        auth=auth,
        profiles=profiles,
        facilities=facilities,
        matches=matches,
        matchmaking=MatchmakingService(matches, profiles, ai_client),
        tournaments=TournamentService(auth),
    )
