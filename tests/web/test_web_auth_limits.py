"""The pages with the real AuthService for the account limits of the penetration test (P1, P3, P6, P7)."""

from campusevent.app import create_app
from campusevent.auth import MAX_FAILED_LOGINS
from campusevent.notifications import InMemoryEmailSender
from campusevent.web import create_web_app

EMAIL = "student@bilgiedu.net"
PASSWORD = "Campus-2026!x"


def real_app():
    mail = InMemoryEmailSender()
    app = create_web_app(
        create_app(email_sender=mail, secret_key="k" * 32),
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "test"},
    )
    return app, mail


def signed_up_and_verified(app, mail):
    client = app.test_client()
    client.post("/signup", data={"full_name": "Test Student", "email": EMAIL, "password": PASSWORD})
    assert client.post("/verify", data={"email": EMAIL, "code": mail.codes[EMAIL]}).status_code == 302
    return client


def test_p3_a_copied_session_cookie_stops_working_after_log_out():
    app, mail = real_app()
    signed_up_and_verified(app, mail)
    browser = app.test_client()
    assert browser.post("/login", data={"email": EMAIL, "password": PASSWORD}).status_code == 302
    cookie = browser.get_cookie("session").value
    thief = app.test_client()
    thief.set_cookie("session", cookie)
    assert thief.get("/profile").status_code == 200  # the copy works while the user is logged in

    browser.post("/logout")
    assert thief.get("/profile").status_code == 302  # back to log in
    assert browser.post("/login", data={"email": EMAIL, "password": PASSWORD}).status_code == 302


def test_p1_the_log_in_page_says_to_wait_after_too_many_wrong_passwords():
    app, mail = real_app()
    signed_up_and_verified(app, mail)
    client = app.test_client()
    for _ in range(MAX_FAILED_LOGINS):
        response = client.post("/login", data={"email": EMAIL, "password": "wrong-password"})
        assert response.status_code == 401 and b"Invalid e-mail or password." in response.data

    response = client.post("/login", data={"email": EMAIL, "password": PASSWORD})
    unknown = client.post("/login", data={"email": "nobody@bilgiedu.net", "password": PASSWORD})
    assert response.status_code == unknown.status_code == 401
    assert b"logging in pauses for a few minutes" in response.data
    assert b"logging in pauses for a few minutes" in unknown.data  # the same answer as for an unknown address
    assert client.get("/profile").status_code == 302  # not logged in


def test_p6_the_verify_page_answers_the_same_for_a_verified_and_an_unknown_address():
    app, mail = real_app()
    client = signed_up_and_verified(app, mail)
    verified = client.post("/verify", data={"email": EMAIL, "code": "123456"})
    unknown = client.post("/verify", data={"email": "nobody@bilgiedu.net", "code": "123456"})
    assert verified.status_code == unknown.status_code == 400
    message = b"The code is wrong or has expired. Please request a new one. If your address is already verified"
    assert message in verified.data and message in unknown.data
    assert b"This e-mail address is already verified" not in verified.data  # the old, telling answer


def test_p7_the_sign_up_page_refuses_a_very_common_password():
    app, mail = real_app()
    response = app.test_client().post(
        "/signup", data={"full_name": "Test Student", "email": EMAIL, "password": "password123"}
    )
    assert response.status_code == 400
    assert b"too easy to guess" in response.data
    assert EMAIL not in mail.codes
