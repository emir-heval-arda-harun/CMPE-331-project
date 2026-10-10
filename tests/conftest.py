import pytest

from campusevent import create_app
from campusevent.notifications import InMemoryEmailSender


@pytest.fixture
def email_sender():
    return InMemoryEmailSender()


@pytest.fixture
def app(email_sender):
    return create_app(email_sender=email_sender)
