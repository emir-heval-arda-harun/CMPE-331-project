"""Wires all services together."""

from __future__ import annotations

import os
from dataclasses import dataclass

from campusevent.auth import AuthService
from campusevent.facilities import FacilityService
from campusevent.events import EventService
from campusevent.notifications import EmailSender, InMemoryEmailSender
from campusevent.profiles import ProfileService
from campusevent.security import PasswordHasher

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
    password_hasher: PasswordHasher | None = None,
    secret_key: str | None = None,
) -> CampusEventApp:
    """``password_hasher`` defaults to argon2id with the recommended settings. ``secret_key`` signs the session
    tokens; it defaults to the SECRET_KEY environment variable (the same one the web app uses), and without
    one a random key is made, so tokens do not survive a restart."""
    auth = AuthService(
        allowed_email_domains,
        email_sender or InMemoryEmailSender(),
        hasher=password_hasher,
        secret_key=secret_key or os.environ.get("SECRET_KEY"),
    )
    profiles = ProfileService(auth)
    facilities = FacilityService(auth)
    events = EventService(auth, facilities)
    return CampusEventApp(
        auth=auth,
        profiles=profiles,
        facilities=facilities,
        events=events,
    )
