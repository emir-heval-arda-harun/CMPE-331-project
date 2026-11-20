"""Composition root: chooses the implementations and wires the services (Software Design Report 4.3).

- ``create_app()`` without a database URL keeps everything in memory (requirement tests, development).
- ``create_app(database_url=...)`` uses PostgreSQL for the parts that have a SQL repository: users and
  verification codes, profiles, facilities. Events stay in memory until ``EventRepository`` exists.
- ``create_app_from_env()`` is used by the web app in production: it reads ``DATABASE_URL``,
  ``SECRET_KEY`` and ``SMTP_*`` (see .env.example). Only this function reads the environment, so the
  tests never touch a real database or mail server by accident.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from sqlalchemy.orm import Session, scoped_session

from campusevent.auth import AuthService
from campusevent.events import EventService
from campusevent.facilities import FacilityService
from campusevent.notifications import EmailSender, InMemoryEmailSender, SmtpEmailSender
from campusevent.profiles import ProfileService
from campusevent.repositories.db import create_db_engine, create_scoped_session
from campusevent.repositories.facility_repository import SqlFacilityRepository
from campusevent.repositories.profile_repository import SqlProfileRepository
from campusevent.repositories.unit_of_work import SqlUnitOfWork
from campusevent.repositories.user_repository import SqlUserRepository
from campusevent.security import PasswordHasher

DEFAULT_EMAIL_DOMAINS = ("bilgiedu.net", "bilgi.edu.tr")

log = logging.getLogger(__name__)


@dataclass
class CampusEventApp:
    auth: AuthService
    profiles: ProfileService
    facilities: FacilityService
    events: EventService
    # The database session registry shared by all Sql* classes; None when everything is in memory.
    db_session: scoped_session[Session] | None = None

    def end_request(self) -> None:
        """Close the database session of the current request (Flask calls this after every request).
        Anything not committed by a UnitOfWork is rolled back."""
        if self.db_session is not None:
            self.db_session.remove()


def create_app(
    allowed_email_domains: tuple[str, ...] = DEFAULT_EMAIL_DOMAINS,
    email_sender: EmailSender | None = None,
    password_hasher: PasswordHasher | None = None,
    secret_key: str | None = None,
    database_url: str | None = None,
) -> CampusEventApp:
    """``password_hasher`` defaults to argon2id with the recommended settings. ``secret_key`` signs the session
    tokens; without one a random key is made, so tokens do not survive a restart. ``database_url`` switches
    users, profiles and facilities to PostgreSQL; the engine does not connect before the first query."""
    session = users = profiles = facilities = uow = None
    if database_url:
        session = create_scoped_session(create_db_engine(database_url))  # one session per request
        uow = SqlUnitOfWork(session)  # shared by all services, so a request is one transaction
        users = SqlUserRepository(session)
        profiles = SqlProfileRepository(session)
        facilities = SqlFacilityRepository(session)

    auth = AuthService(
        allowed_email_domains,
        email_sender or InMemoryEmailSender(),
        users,
        uow=uow,
        hasher=password_hasher,
        secret_key=secret_key,
    )
    profile_service = ProfileService(auth, profiles, uow)
    # EventRepository (task 3.6) is not written yet: until it is passed here as ``events``, no event
    # occupies a facility slot and EventService keeps its own data.
    facility_service = FacilityService(auth, facilities, uow=uow)
    events = EventService(auth, facility_service)
    return CampusEventApp(
        auth=auth,
        profiles=profile_service,
        facilities=facility_service,
        events=events,
        db_session=session,
    )


def email_sender_from_env() -> EmailSender:
    """``SmtpEmailSender`` when SMTP_HOST is set. Otherwise the e-mails are only kept in memory: nobody
    receives a verification code, so only the verified demo users of scripts/seed_db.py can log in."""
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host:
        log.warning("SMTP_HOST is not set: verification e-mails are NOT sent (see .env.example).")
        return InMemoryEmailSender()
    return SmtpEmailSender(
        host=host,
        port=int(os.environ.get("SMTP_PORT") or 587),
        username=os.environ.get("SMTP_USERNAME", ""),
        password=os.environ.get("SMTP_PASSWORD", ""),
        sender=os.environ.get("SMTP_FROM", "") or os.environ.get("SMTP_USERNAME", ""),
    )


def create_app_from_env() -> CampusEventApp:
    """The production wiring (Render): DATABASE_URL, SECRET_KEY and SMTP_* from the environment.
    Without DATABASE_URL the data is kept in memory and lost at every restart."""
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        log.warning("DATABASE_URL is not set: all data is kept in memory and lost at every restart.")
    return create_app(
        email_sender=email_sender_from_env(),
        secret_key=os.environ.get("SECRET_KEY") or None,
        database_url=database_url or None,
    )
