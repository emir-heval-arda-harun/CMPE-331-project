"""The whole wiring of create_app(database_url=...) against a real PostgreSQL database: UC-01, UC-02, UC-03.

Skipped without TEST_DATABASE_URL (see docs/database/README.md). The users created here have e-mails
starting with PREFIX and are deleted after the test (their codes and profile rows go with them).
"""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import delete

from campusevent.app import create_app
from campusevent.models import Profile, TimeSlot
from campusevent.notifications import InMemoryEmailSender
from campusevent.repositories.tables import UserRow

PREFIX = "wiring.test."
PASSWORD = "S3cure-pass!"


@pytest.fixture
def services(engine, test_database_url, fast_hasher):
    sender = InMemoryEmailSender()
    services = create_app(
        email_sender=sender, password_hasher=fast_hasher, secret_key="test", database_url=test_database_url
    )
    yield services
    services.end_request()
    services.db_session.get_bind().dispose()
    with engine.begin() as connection:
        connection.execute(delete(UserRow).where(UserRow.email.startswith(PREFIX)))


def test_sign_up_log_in_and_save_profile_across_requests(services):
    email = f"{PREFIX}deniz@bilgiedu.net"
    sender = services.auth.email_sender

    # every block below is one web request: the session is closed in between, like Flask does
    services.auth.register(email, PASSWORD, "Deniz")
    services.end_request()
    services.auth.verify_email(email, sender.codes[email])
    services.end_request()
    token = services.auth.login(email, PASSWORD)
    services.end_request()
    user = services.auth.get_user_by_token(token)
    slot = TimeSlot(datetime(2026, 11, 3, 14), datetime(2026, 11, 3, 16))
    services.profiles.update_profile(user.id, ["Football", "Board Games"], [slot])
    services.end_request()

    assert services.profiles.get_profile(user.id) == Profile(user.id, ["board games", "football"], [slot])
