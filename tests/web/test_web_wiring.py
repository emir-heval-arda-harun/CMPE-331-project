"""The web app and the composition root: one database session per request, production wiring, e-mail errors."""

from campusevent.exceptions import EmailDeliveryError
from campusevent.notifications import InMemoryEmailSender
from campusevent.web import create_web_app
from tests.web.fakes import PASSWORD, make_fake_services

CONFIG = {"TESTING": True, "WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "test"}


class FakeSessionRegistry:
    def __init__(self):
        self.removed = 0

    def remove(self):
        self.removed += 1


def test_database_session_is_closed_after_every_request():
    services = make_fake_services(InMemoryEmailSender())
    services.db_session = FakeSessionRegistry()
    client = create_web_app(services, CONFIG).test_client()

    client.get("/login")
    client.get("/signup")

    assert services.db_session.removed == 2


def test_without_services_the_app_is_built_from_the_environment(monkeypatch):
    for name in ("DATABASE_URL", "SMTP_HOST"):
        monkeypatch.delenv(name, raising=False)

    web_app = create_web_app(config=CONFIG)

    assert web_app.extensions["campusevent"].db_session is None
    assert web_app.test_client().get("/login").status_code == 200


def test_mail_server_problem_is_shown_on_the_sign_up_page():
    services = make_fake_services(InMemoryEmailSender())

    def register(*args, **kwargs):
        raise EmailDeliveryError("We could not send the e-mail. Please try again in a few minutes.")

    services.auth.register = register
    client = create_web_app(services, CONFIG).test_client()

    response = client.post(
        "/signup", data={"full_name": "Ayse", "email": "ayse@bilgiedu.net", "password": PASSWORD}
    )

    assert response.status_code == 503
    assert b"We could not send the e-mail" in response.data
