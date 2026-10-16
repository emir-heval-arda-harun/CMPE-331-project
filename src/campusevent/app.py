"""Wires all services together."""

from __future__ import annotations

from dataclasses import dataclass

from campusevent.auth import AuthService
from campusevent.facilities import FacilityService
from campusevent.events import EventService
from campusevent.notifications import EmailSender, InMemoryEmailSender
from campusevent.profiles import ProfileService

DEFAULT_EMAIL_DOMAINS = ("bilgiedu.net", "bilgi.edu.tr")


@dataclass
class CampusEventApp:
    auth: AuthService
    profiles: ProfileService
    facilities: FacilityService
    events: EventService


def create_app(
    allowed_email_domains: tuple[str, ...] = DEFAULT_EMAIL_DOMAINS,
    email_sender: EmailSender | None = None,
) -> CampusEventApp:
    auth = AuthService(allowed_email_domains, email_sender or InMemoryEmailSender())
    profiles = ProfileService(auth)
    facilities = FacilityService(auth)
    events = EventService(auth, facilities)
    return CampusEventApp(
        auth=auth,
        profiles=profiles,
        facilities=facilities,
        events=events,
    )
