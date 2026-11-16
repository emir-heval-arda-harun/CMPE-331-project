import pytest

from campusevent.models import Role
from campusevent.notifications import InMemoryEmailSender
from campusevent.web import create_web_app
from tests.web.fakes import PASSWORD, make_fake_services


@pytest.fixture
def services():
    return make_fake_services(InMemoryEmailSender())


@pytest.fixture
def web_app(services):
    return create_web_app(
        services,
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "test"},
    )


@pytest.fixture
def client(web_app):
    return web_app.test_client()


def make_user(services, email, role=Role.STUDENT, name=None):
    user = services.auth.register(email, PASSWORD, name or email.split("@")[0].title(), role)
    services.auth.verify_email(email, "123456")
    return user


def log_in(client, email):
    return client.post("/login", data={"email": email, "password": PASSWORD})


@pytest.fixture
def student(services, client):
    user = make_user(services, "deniz@bilgiedu.net", name="Deniz Kaya")
    log_in(client, "deniz@bilgiedu.net")
    return user


@pytest.fixture
def hall(services):
    staff = make_user(services, "staff@bilgi.edu.tr", Role.FACILITY_STAFF, "Facility Staff")
    return services.facilities.add_facility(staff.id, "Santral Event Hall", 50)
