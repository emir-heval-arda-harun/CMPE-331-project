"""The composition root (app.py) and SmtpEmailSender.

No test here opens a database connection or a mail server: SQLAlchemy connects only at the first query,
and smtplib is replaced by a stand-in.
"""

import smtplib

import pytest

from campusevent import app as app_module
from campusevent import notifications
from campusevent.app import create_app, create_app_from_env
from campusevent.exceptions import EmailDeliveryError
from campusevent.notifications import InMemoryEmailSender, SmtpEmailSender
from campusevent.repositories.facility_repository import InMemoryFacilityRepository, SqlFacilityRepository
from campusevent.repositories.profile_repository import InMemoryProfileRepository, SqlProfileRepository
from campusevent.repositories.unit_of_work import InMemoryUnitOfWork, SqlUnitOfWork
from campusevent.repositories.user_repository import InMemoryUserRepository, SqlUserRepository

DB_URL = "postgresql://campusevent:secret@localhost:5432/campusevent_dev"
ENV_NAMES = ("DATABASE_URL", "SECRET_KEY", "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM")


@pytest.fixture
def clean_env(monkeypatch):
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


# --------------------------------------------------------------------------- #
# create_app
# --------------------------------------------------------------------------- #
def test_without_database_everything_is_in_memory():
    services = create_app()

    assert isinstance(services.auth.users, InMemoryUserRepository)
    assert isinstance(services.profiles.profiles, InMemoryProfileRepository)
    assert isinstance(services.facilities.facilities, InMemoryFacilityRepository)
    assert isinstance(services.auth.uow, InMemoryUnitOfWork)
    assert services.db_session is None
    services.end_request()  # nothing to close


def test_with_database_the_sql_classes_share_one_session_and_one_unit_of_work():
    services = create_app(database_url=DB_URL)

    assert isinstance(services.auth.users, SqlUserRepository)
    assert isinstance(services.profiles.profiles, SqlProfileRepository)
    assert isinstance(services.facilities.facilities, SqlFacilityRepository)
    assert isinstance(services.auth.uow, SqlUnitOfWork)
    session = services.db_session
    assert session is not None
    assert services.auth.users.session is session
    assert services.profiles.profiles.session is session
    assert services.facilities.facilities.session is session
    assert services.auth.uow is services.profiles.uow is services.facilities.uow
    assert services.auth.uow.session is session


def test_end_request_removes_the_session_of_the_request():
    class Registry:
        removed = 0

        def remove(self):
            self.removed += 1

    services = create_app()
    services.db_session = Registry()

    services.end_request()

    assert services.db_session.removed == 1


# --------------------------------------------------------------------------- #
# create_app_from_env
# --------------------------------------------------------------------------- #
def test_from_env_without_settings_keeps_data_and_mails_in_memory(clean_env):
    services = create_app_from_env()

    assert services.db_session is None
    assert isinstance(services.auth.email_sender, InMemoryEmailSender)


def test_from_env_uses_database_url_and_smtp_settings(clean_env):
    clean_env.setenv("DATABASE_URL", DB_URL)
    clean_env.setenv("SMTP_HOST", "smtp.example.com")
    clean_env.setenv("SMTP_PORT", "465")
    clean_env.setenv("SMTP_USERNAME", "campusevent@example.com")
    clean_env.setenv("SMTP_PASSWORD", "app-password")

    services = create_app_from_env()

    assert isinstance(services.auth.users, SqlUserRepository)
    sender = services.auth.email_sender
    assert isinstance(sender, SmtpEmailSender)
    assert (sender.host, sender.port, sender.username, sender.password, sender.sender) == (
        "smtp.example.com", 465, "campusevent@example.com", "app-password", "campusevent@example.com"
    )


def test_from_env_signs_tokens_with_secret_key_so_they_survive_a_restart(clean_env, monkeypatch, fast_hasher):
    clean_env.setenv("SECRET_KEY", "the-same-key-on-every-worker")
    monkeypatch.setattr(app_module, "create_app", _with_hasher(create_app, fast_hasher))
    first = app_module.create_app_from_env()
    user = first.auth.register("ayse@bilgiedu.net", "S3cure-pass!", "Ayse")
    first.auth.verify_email("ayse@bilgiedu.net", first.auth.email_sender.codes["ayse@bilgiedu.net"])
    token = first.auth.login("ayse@bilgiedu.net", "S3cure-pass!")

    restarted = app_module.create_app_from_env()
    restarted.auth.users = first.auth.users  # in production both read the same database

    assert restarted.auth.get_user_by_token(token).id == user.id


def _with_hasher(factory, hasher):
    def wrapped(**kwargs):
        return factory(password_hasher=hasher, **kwargs)

    return wrapped


# --------------------------------------------------------------------------- #
# SmtpEmailSender
# --------------------------------------------------------------------------- #
class FakeSmtp:
    """Stand-in for smtplib.SMTP / SMTP_SSL that records what happens."""

    instances: list["FakeSmtp"] = []
    fail_on: str | None = None

    def __init__(self, host, port, timeout=None, context=None):
        if FakeSmtp.fail_on == "connect":
            raise ConnectionRefusedError("no server")
        self.host, self.port, self.timeout, self.ssl_context = host, port, timeout, context
        self.calls: list[str] = []
        self.messages = []
        FakeSmtp.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.calls.append("quit")

    def starttls(self, context=None):
        self.calls.append("starttls")

    def login(self, username, password):
        if FakeSmtp.fail_on == "login":
            raise smtplib.SMTPAuthenticationError(535, b"bad credentials")
        self.calls.append(f"login {username} {password}")

    def send_message(self, message):
        self.calls.append("send")
        self.messages.append(message)


@pytest.fixture
def fake_smtp(monkeypatch):
    FakeSmtp.instances, FakeSmtp.fail_on = [], None
    monkeypatch.setattr(notifications.smtplib, "SMTP", FakeSmtp)
    monkeypatch.setattr(notifications.smtplib, "SMTP_SSL", FakeSmtp)
    return FakeSmtp


def test_verification_code_is_sent_with_starttls_and_login(fake_smtp):
    sender = SmtpEmailSender("smtp.example.com", 587, "bot@example.com", "app-password", "CampusEvent <bot@example.com>")

    sender.send_verification_code("ayse@bilgiedu.net", "042917")

    smtp = fake_smtp.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.example.com", 587)
    assert smtp.calls == ["starttls", "login bot@example.com app-password", "send", "quit"]
    message = smtp.messages[0]
    assert (message["To"], message["From"]) == ("ayse@bilgiedu.net", "CampusEvent <bot@example.com>")
    assert "042917" in message["Subject"] and "042917" in message.get_content()
    assert "15 minutes" in message.get_content()


def test_port_465_uses_tls_from_the_start(fake_smtp):
    SmtpEmailSender("smtp.example.com", 465, "bot@example.com", "pw").send_verification_code("a@bilgiedu.net", "1")

    smtp = fake_smtp.instances[0]
    assert smtp.ssl_context is not None
    assert "starttls" not in smtp.calls


def test_event_decision_mail_has_the_reason(fake_smtp):
    sender = SmtpEmailSender("smtp.example.com", 587)

    sender.send_event_decision("can@bilgiedu.net", "Chess night", False, "The hall is closed for exams.")

    smtp = fake_smtp.instances[0]
    assert "login" not in " ".join(smtp.calls)  # no username: the server needs no login
    assert "rejected" in smtp.messages[0]["Subject"]
    assert "The hall is closed for exams." in smtp.messages[0].get_content()


@pytest.mark.parametrize("fail_on", ["connect", "login"])
def test_mail_server_problems_become_email_delivery_error(fake_smtp, fail_on):
    fake_smtp.fail_on = fail_on

    with pytest.raises(EmailDeliveryError, match="could not send the e-mail"):
        SmtpEmailSender("smtp.example.com", 587, "bot@example.com", "wrong").send_verification_code("a@b.c", "1")
