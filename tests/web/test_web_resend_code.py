"""UC-01 5a and UC-02 3a: "Send a new code" on the verify page and on the log in page."""

import re
from datetime import timedelta

from campusevent.app import create_app
from campusevent.auth import RESEND_INTERVAL, utc_now
from campusevent.notifications import InMemoryEmailSender
from campusevent.web import auth_routes, create_web_app
from tests.web.fakes import PASSWORD

EMAIL = "student@bilgiedu.net"
SENT = b"a new code is on its way"


def resend(client, email=EMAIL):
    return client.post("/verify/resend", data={"email": email})


def test_verify_page_offers_a_new_code_in_the_same_form(client):
    page = client.get("/verify").get_data(as_text=True)
    form = page[page.index('action="/verify"') :]
    form = form[: form.index("</form>")]
    assert 'formaction="/verify/resend"' in form  # the e-mail typed above is sent along, no JavaScript needed
    assert "Send a new code" in form


def test_new_code_replaces_the_old_one(client, services):
    services.auth.register(EMAIL, PASSWORD, "Test Student")
    old = services.auth.email_sender.codes[EMAIL]
    response = resend(client)
    assert response.status_code == 200
    assert SENT in response.data
    assert f'value="{EMAIL}"'.encode() in response.data  # the address stays in the form
    new = services.auth.email_sender.codes[EMAIL]
    assert new != old
    assert client.post("/verify", data={"email": EMAIL, "code": old}).status_code == 400
    response = client.post("/verify", data={"email": EMAIL, "code": new}, follow_redirects=True)
    assert b"Your e-mail address is verified" in response.data


def test_answer_is_the_same_for_unknown_and_verified_addresses(web_app, services):
    services.auth.register("done@bilgiedu.net", PASSWORD, "Done")
    services.auth.verify_email("done@bilgiedu.net", "123456")
    services.auth.register(EMAIL, PASSWORD, "Test Student")
    pages = []
    for email in ("nobody@bilgiedu.net", "done@bilgiedu.net", EMAIL):
        response = resend(web_app.test_client(), email)  # a new browser each time, so the wait does not apply
        assert response.status_code == 200
        page = response.get_data(as_text=True).replace(email, "ADDRESS")
        page = re.sub(r'name="csrf_token"[^>]*', "", page)  # the form token differs per browser
        pages.append(re.sub(r'nonce="[^"]*"', "", page))  # and the script nonce per answer
    assert pages[0] == pages[1] == pages[2]  # nothing tells which addresses have accounts
    assert "nobody@bilgiedu.net" not in services.auth.email_sender.codes


def test_empty_address_is_refused(client):
    response = resend(client, "  ")
    assert response.status_code == 400
    assert b"Please enter your university e-mail address." in response.data


def test_one_browser_waits_a_minute_between_two_codes(client, services, monkeypatch):
    services.auth.register(EMAIL, PASSWORD, "Test Student")
    clock = [1_000_000.0]
    monkeypatch.setattr(auth_routes.time, "time", lambda: clock[0])
    assert resend(client).status_code == 200
    first = services.auth.email_sender.codes[EMAIL]

    clock[0] += 20
    response = resend(client)
    assert response.status_code == 429
    assert b"another one in 41 seconds" in response.data
    assert services.auth.email_sender.codes[EMAIL] == first  # no second e-mail

    clock[0] += auth_routes.RESEND_WAIT
    assert resend(client).status_code == 200
    assert services.auth.email_sender.codes[EMAIL] != first


def test_unverified_log_in_offers_a_new_code_without_the_address_in_a_link(client, services):
    services.auth.register(EMAIL, PASSWORD, "Test Student")
    page = client.post("/login", data={"email": EMAIL, "password": PASSWORD}).get_data(as_text=True)
    assert 'action="/verify/resend"' in page
    assert f'type="hidden" name="email" value="{EMAIL}"' in page  # in the form body, not in a URL
    assert "send a new code" in page
    response = resend(client)
    assert SENT in response.data


def test_works_with_the_real_auth_service():
    """The route against AuthService (task 3.2): the old code stops working, the new one verifies."""
    mail = InMemoryEmailSender()
    services = create_app(email_sender=mail, secret_key="k" * 32)
    app = create_web_app(
        services,
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "test"},
    )
    client = app.test_client()
    client.post("/signup", data={"full_name": "Test Student", "email": EMAIL, "password": "Campus-2026!x"})
    old = mail.codes[EMAIL]
    later = utc_now() + RESEND_INTERVAL + timedelta(seconds=1)  # the service sends one code per minute (#30)
    services.auth.clock = lambda: later
    assert SENT in resend(client).data
    new = mail.codes[EMAIL]
    assert re.fullmatch(r"\d{6}", new) and new != old
    assert client.post("/verify", data={"email": EMAIL, "code": old}).status_code == 400
    assert client.post("/verify", data={"email": EMAIL, "code": new}).status_code == 302
