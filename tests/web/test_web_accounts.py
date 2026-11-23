"""Web UI tests for UC-01 register and verify, UC-02 log in, UC-03 profile."""

import re

from campusevent.facilities import FacilityService
from campusevent.models import Role
from campusevent.web import create_web_app
from tests.web.conftest import log_in, make_user
from tests.web.fakes import PASSWORD, make_fake_services, slot


def test_signup_shows_code_box_after_registration(client):
    response = client.post(
        "/signup", data={"full_name": "Test Student", "email": "student@bilgiedu.net", "password": PASSWORD}
    )
    assert response.status_code == 200
    assert b"Verify your e-mail" in response.data
    assert b'name="code"' in response.data


def test_login_and_signup_pages_have_a_show_password_button_and_no_main_navigation(client):
    for path in ("/login", "/signup"):
        page = client.get(path).data
        assert b'data-toggle-password="#password"' in page, path
        assert b'type="password"' in page, path  # the field is hidden until the user asks
        assert b"<nav" not in page, path  # these pages use the brand panel layout


def test_every_page_has_the_animated_background_that_stops_for_reduced_motion(client, student):
    for path in ("/login", "/signup", "/events", "/events/new", "/profile", "/activities"):
        page = client.get(path).data
        assert b'class="bg-orbs"' in page, path
        assert b"prefers-reduced-motion: reduce" in page, path  # no motion for people who ask for none
        assert page.count(b"<span></span>") >= 3, path


def test_pages_after_login_have_the_hero_band_and_auth_pages_do_not(client, student):
    for path in ("/events", "/events/new", "/profile", "/activities", "/events/999"):
        page = client.get(path).data
        assert b'<body class="app theme-glass"' in page, path  # every page after login uses the glass theme
        assert b'<div class="hero-bg"' in page, path
    for path in ("/login", "/signup"):
        page = client.get(path).data
        assert b'<body class="auth theme-glass"' in page, path
        assert b'<div class="hero-bg"' not in page, path
        assert b'class="hero-icons"' in page, path  # floating icons on the brand panel


def test_login_background_is_a_drawn_skyline_until_a_campus_photo_is_added(client):
    page = client.get("/login").data
    assert b'class="auth-skyline"' in page
    assert b"/static/img/campus" not in page


def test_login_background_uses_the_campus_photo_when_the_file_exists(web_app, tmp_path):
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "campus.jpg").write_bytes(b"\xff\xd8\xff fake jpeg for the test")
    web_app.static_folder = str(tmp_path)
    client = web_app.test_client()
    page = client.get("/login").data
    assert b"/static/img/campus.jpg" in page
    assert b'class="auth-skyline"' not in page  # the photo replaces the drawing
    assert client.get("/static/img/campus.jpg").status_code == 200


def test_signup_rejects_non_university_email(client):
    response = client.post(
        "/signup", data={"full_name": "Sample Name", "email": "student@gmail.com", "password": PASSWORD}
    )
    assert response.status_code == 400
    assert b"Please use your university e-mail address." in response.data
    assert b"Create your account" in response.data  # the form stays, the entered name stays
    assert b"Sample Name" in response.data


def test_signup_rejects_duplicate_email(client, services):
    make_user(services, "student@bilgiedu.net")
    response = client.post(
        "/signup", data={"full_name": "Test Student", "email": "student@bilgiedu.net", "password": PASSWORD}
    )
    assert b"already exists" in response.data


def test_verify_with_correct_code_goes_to_login(client, services):
    services.auth.register("student@bilgiedu.net", PASSWORD, "Test Student")
    response = client.post("/verify", data={"email": "student@bilgiedu.net", "code": "123456"}, follow_redirects=True)
    assert b"Your e-mail address is verified" in response.data
    assert b"Log in" in response.data


def test_verify_with_wrong_code_shows_error_and_keeps_form(client, services):
    services.auth.register("student@bilgiedu.net", PASSWORD, "Test Student")
    response = client.post("/verify", data={"email": "student@bilgiedu.net", "code": "000000"})
    assert response.status_code == 400
    assert b"wrong or has expired" in response.data
    assert b'name="code"' in response.data


def test_student_logs_in_and_lands_on_find_events(client, services):
    make_user(services, "student@bilgiedu.net")
    response = log_in(client, "student@bilgiedu.net")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/events")


def test_facility_staff_lands_on_facility_management(client, services):
    make_user(services, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    response = log_in(client, "staff@bilgi.edu.tr")
    assert response.headers["Location"].endswith("/facilities")


def test_wrong_credentials_do_not_say_which_part_is_wrong(client, services):
    make_user(services, "student@bilgiedu.net")
    wrong_password = client.post("/login", data={"email": "student@bilgiedu.net", "password": "nope"})
    unknown_email = client.post("/login", data={"email": "who@bilgiedu.net", "password": PASSWORD})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert b"Invalid e-mail or password." in wrong_password.data
    assert b"Invalid e-mail or password." in unknown_email.data


def test_unverified_account_cannot_log_in_and_is_offered_the_code_page(client, services):
    services.auth.register("student@bilgiedu.net", PASSWORD, "Test Student")
    response = log_in(client, "student@bilgiedu.net")
    assert response.status_code == 401
    assert b"verify your e-mail" in response.data
    assert b'href="/verify"' in response.data  # the e-mail address is not put into the URL


def test_head_requests_only_show_the_page_and_never_run_the_form(services):
    """Penetration test P8: HEAD ran the code of POST, and Flask-WTF does not check CSRF tokens on HEAD, so a HEAD
    with a form body logged in, signed up, saved a profile or created an event without a token."""
    app = create_web_app(services, {"SESSION_COOKIE_SECURE": False, "SECRET_KEY": "test"})  # CSRF on
    user = make_user(services, "student@bilgiedu.net")
    staff = make_user(services, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    hall = services.facilities.add_facility(staff.id, "Hall", 50)
    client = app.test_client()
    signup = {"email": "new@bilgiedu.net", "full_name": "New Student", "password": PASSWORD}
    assert client.open("/signup", method="HEAD", data=signup).status_code == 200
    assert services.auth._by_email("new@bilgiedu.net") is None  # nobody was signed up
    form = {"email": "student@bilgiedu.net", "password": PASSWORD}
    assert client.open("/login", method="HEAD", data=form).status_code == 200
    assert client.get("/profile").status_code == 302  # the HEAD did not log in

    page = client.get("/login").data.decode()
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page).group(1)
    assert client.post("/login", data={**form, "csrf_token": token}).status_code == 302  # a real log in, with token
    before = list(services.profiles.get_profile(user.id).interests)
    event_form = {"title": "No token", "category": "chess", "facility_id": str(hall.id), "date": "2026-11-21",
                  "start": "10:00", "end": "11:00", "capacity": "4", "interests": "Set without a token"}
    for path in ("/profile", "/events/new"):
        assert client.open(path, method="HEAD", data=event_form).status_code == 200, path
    assert services.profiles.get_profile(user.id).interests == before
    assert not services.events.events  # no event was created


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


# NFR-03: the live site sent none of these headers (checked on 23.11.2026).
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000",  # browsers use HTTPS only, also when typed without it
    "X-Frame-Options": "DENY",  # no other site can show our pages in a frame (clickjacking)
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",  # other sites never see which page of ours a visitor came from
}


def assert_security_headers(response, what):
    for name, value in SECURITY_HEADERS.items():
        assert response.headers.get(name) == value, (what, name, response.headers.get(name))
    # the same rule against framing for browsers that read CSP; the whole policy is checked below
    assert "frame-ancestors 'none'" in response.headers.get("Content-Security-Policy", ""), what


def test_every_kind_of_answer_has_the_security_headers(client, student):
    answers = {  # path: status, so that each kind of answer is really checked
        "/login": 200, "/signup": 200, "/events": 200, "/profile": 200,  # pages
        "/": 302,  # redirect
        "/no-such-page": 404,  # error page
        "/static/favicon.svg": 200,  # static file
    }
    for path, status in answers.items():
        response = client.get(path)
        assert response.status_code == status, path
        assert_security_headers(response, path)
    response = client.post("/logout")
    assert response.status_code == 302
    assert_security_headers(response, "POST /logout")


def test_the_error_page_of_an_unexpected_error_has_the_security_headers(services):
    app = create_web_app(services, {"WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "t"})
    make_user(services, "student@bilgiedu.net")
    client = app.test_client()
    log_in(client, "student@bilgiedu.net")

    def broken(*args, **kwargs):
        raise RuntimeError("database is down")

    services.events.search_events = broken
    response = client.get("/events")
    assert response.status_code == 500
    assert_security_headers(response, "500")


def csp_of(response):
    """The Content-Security-Policy header as {directive: [values]}."""
    policy = {}
    for part in response.headers.get("Content-Security-Policy", "").split(";"):
        if part.strip():
            name, *values = part.split()
            policy[name] = values
    return policy


def test_the_content_security_policy_allows_only_our_own_site_and_no_injected_script(client, student):
    """NFR-03: even if text typed by a user reached a page unescaped, the browser would not run it."""
    policy = csp_of(client.get("/events"))
    assert policy["default-src"] == ["'self'"]
    script = policy["script-src"]
    assert "'self'" in script and len([v for v in script if v.startswith("'nonce-")]) == 1
    assert "'unsafe-inline'" not in script and "'unsafe-eval'" not in script
    assert policy["object-src"] == ["'none'"] and policy["base-uri"] == ["'self'"]
    assert policy["form-action"] == ["'self'"] and policy["frame-ancestors"] == ["'none'"]
    values = [v for vs in policy.values() for v in vs]
    assert not any(v.startswith(("http", "*")) or v == "https:" for v in values)  # nothing from other sites


def test_every_script_on_every_page_carries_the_nonce_of_its_answer(web_app, services, hall):
    services.facilities = FacilityService(services.auth, events=services.events)  # the page needs the real one
    hall = services.facilities.add_facility(services.auth._by_email("staff@bilgi.edu.tr").id, "Hall", 50)
    organizer = make_user(services, "organizer@bilgiedu.net")
    make_user(services, "admin@bilgi.edu.tr", Role.ADMIN)
    event = services.events.create_event(organizer.id, "Game night", "board games", hall.id, slot(day=20), 6)
    pages = {
        None: ["/login", "/signup", "/verify", "/no-such-page"],
        "organizer@bilgiedu.net": ["/events", "/events/new", f"/events/{event.id}", "/activities", "/profile"],
        "admin@bilgi.edu.tr": ["/admin/requests"],
        "staff@bilgi.edu.tr": ["/facilities"],
    }
    nonces = set()
    for email, paths in pages.items():
        client = web_app.test_client()
        if email:
            log_in(client, email)
        for path in paths:
            response = client.get(path)
            nonce = [v for v in csp_of(response)["script-src"] if v.startswith("'nonce-")][0][7:-1]
            scripts = re.findall(r"<script\b[^>]*>", response.data.decode())
            assert scripts, path
            assert all(f'nonce="{nonce}"' in tag for tag in scripts), (path, scripts)
            nonces.add(nonce)
    assert len(nonces) == sum(len(paths) for paths in pages.values())  # a new nonce for every answer


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
    assert profile.availability[0].start.hour == 14  # typed 17:00 Istanbul time, kept as 14:00 UTC
    assert b'value="17:00"' in client.get("/profile").data  # and shown as 17:00 again
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
