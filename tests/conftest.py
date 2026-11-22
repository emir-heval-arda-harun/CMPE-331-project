from datetime import datetime

import pytest

from campusevent import create_app
from campusevent.notifications import InMemoryEmailSender
from campusevent.security import Argon2PasswordHasher


@pytest.fixture
def email_sender():
    return InMemoryEmailSender()


@pytest.fixture
def fast_hasher():
    """Still salted argon2id hashes (NFR-03), but with small cost settings: the tests register hundreds of
    users, and the production settings take about 50 ms per hash."""
    return Argon2PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


# The requirement tests use fixed event dates (tests/helpers.slot(): 2 Nov 2026 and later), so EventService
# gets a fixed "now" before them. With the real time, "has not started" (UC-10, UC-11) fails once the date passed.
NOW = datetime(2026, 11, 1, 12, 0)  # naive UTC, like the services


@pytest.fixture
def app(email_sender, fast_hasher):
    return create_app(email_sender=email_sender, password_hasher=fast_hasher, clock=lambda: NOW)
