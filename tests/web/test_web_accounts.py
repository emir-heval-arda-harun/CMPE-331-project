"""Web UI tests for UC-01 register and verify, UC-02 log in, UC-03 profile."""

from campusevent.models import Role
from campusevent.web import create_web_app
from tests.web.conftest import log_in, make_user
from tests.web.fakes import PASSWORD, make_fake_services


def test_signup_shows_code_box_after_registration(client):
    response = client.post(
        "/signup", data={"full_name": "Deniz Kaya", "email": "deniz@bilgiedu.net", "password": PASSWORD}
    )
    assert response.status_code == 200
    assert b"Verify your e-mail" in response.data
    assert b'name="code"' in response.data


def test_signup_rejects_non_university_email(client):
    response = client.post(
        "/signup", data={"full_name": "Deniz", "email": "deniz@gmail.com", "password": PASSWORD}
    )
    assert response.status_code == 400
    assert b"Please use your university e-mail address." in response.data
    assert b"Create your account" in response.data  # the form stays, the entered name stays
    assert b"Deniz" in response.data


def test_signup_rejects_duplicate_email(client, services):
    make_user(services, "deniz@bilgiedu.net")
    response = client.post(
        "/signup", data={"full_name": "Deniz", "email": "deniz@bilgiedu.net", "password": PASSWORD}
    )
    assert b"already exists" in response.data


def test_verify_with_correct_code_goes_to_login(client, services):
    services.auth.register("deniz@bilgiedu.net", PASSWORD, "Deniz")
    response = client.post("/verify", data={"email": "deniz@bilgiedu.net", "code": "123456"}, follow_redirects=True)
    assert b"Your e-mail address is verified" in response.data
    assert b"Log in" in response.data


def test_verify_with_wrong_code_shows_error_and_keeps_form(client, services):
    services.auth.register("deniz@bilgiedu.net", PASSWORD, "Deniz")
    response = client.post("/verify", data={"email": "deniz@bilgiedu.net", "code": "000000"})
    assert response.status_code == 400
    assert b"wrong or has expired" in response.data
    assert b'name="code"' in response.data


def test_student_logs_in_and_lands_on_find_events(client, services):
    make_user(services, "deniz@bilgiedu.net")
    response = log_in(client, "deniz@bilgiedu.net")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/events")


def test_facility_staff_lands_on_facility_management(client, services):
    make_user(services, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    response = log_in(client, "staff@bilgi.edu.tr")
    assert response.headers["Location"].endswith("/facilities")


def test_wrong_credentials_do_not_say_which_part_is_wrong(client, services):
    make_user(services, "deniz@bilgiedu.net")
    wrong_password = client.post("/login", data={"email": "deniz@bilgiedu.net", "password": "nope"})
    unknown_email = client.post("/login", data={"email": "who@bilgiedu.net", "password": PASSWORD})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert b"Invalid e-mail or password." in wrong_password.data
    assert b"Invalid e-mail or password." in unknown_email.data


def test_unverified_account_cannot_log_in_and_is_offered_the_code_page(client, services):
    services.auth.register("deniz@bilgiedu.net", PASSWORD, "Deniz")
    response = log_in(client, "deniz@bilgiedu.net")
    assert response.status_code == 401
    assert b"verify your e-mail" in response.data
    assert b'href="/verify"' in response.data  # the e-mail address is not put into the URL


def test_pages_redirect_to_login_when_logged_out(client):
    for path in ("/events", "/events/new", "/profile", "/activities"):
        response = client.get(path)
        assert response.status_code == 302, path
        assert response.headers["Location"].endswith("/login"), path


def test_staff_cannot_open_student_pages(client, services):
    make_user(services, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    log_in(client, "staff@bilgi.edu.tr")
    assert client.get("/events").status_code == 403


def test_logout_ends_the_session(client, student):
    assert client.get("/events").status_code == 200
    client.post("/logout")
    assert client.get("/events").status_code == 302


def test_forms_are_protected_by_csrf_tokens(services):
    app = create_web_app(services, {"TESTING": True, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "test"})
    response = app.test_client().post("/login", data={"email": "a@bilgiedu.net", "password": "x"})
    assert response.status_code == 400
    assert b"form has expired" in response.data


def test_session_cookie_is_secure_by_default(services):
    app = create_web_app(services, {"SECRET_KEY": "test"})
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


# UC-03 -------------------------------------------------------------------------------------------


def test_profile_saves_interests_and_availability(client, student, services):
    response = client.post(
        "/profile",
        data={
            "interests": "Football\nboard games\n",
            "slot_date": ["2026-11-20", ""],
            "slot_start": ["17:00", ""],
            "slot_end": ["19:00", ""],
        },
        follow_redirects=True,
    )
    assert b"Your profile is saved." in response.data
    profile = services.profiles.get_profile(student.id)
    assert profile.interests == ["football", "board games"]
    assert len(profile.availability) == 1
    assert profile.availability[0].start.hour == 17
    assert b"football" in response.data  # shown again after saving


def test_profile_requires_one_interest(client, student):
    response = client.post("/profile", data={"interests": "  \n"})
    assert response.status_code == 400
    assert b"at least one interest" in response.data


def test_profile_rejects_slot_that_ends_before_it_starts(client, student):
    response = client.post(
        "/profile",
        data={"interests": "chess", "slot_date": ["2026-11-20"], "slot_start": ["19:00"], "slot_end": ["17:00"]},
    )
    assert response.status_code == 400
    assert b"end time must be after the start time" in response.data
    assert b"chess" in response.data  # the input is kept


def test_new_accounts_get_their_own_empty_services():
    # guards against shared state between two apps created in one process
    first, second = make_fake_services(), make_fake_services()
    first.auth.register("a@bilgiedu.net", PASSWORD, "A")
    assert second.auth.users == {}
