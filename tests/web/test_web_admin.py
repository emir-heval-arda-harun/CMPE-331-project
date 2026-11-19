"""Web UI for change request CR-01 / UC-12: the admin's Event Requests page, the organizer's view of pending
and rejected requests, and the follow-ups of the review of PR #7 (SECRET_KEY warning, favicon)."""

import logging

import pytest

from campusevent.models import EventStatus, Role
from campusevent.web import create_web_app
from tests.web.conftest import log_in, make_user
from tests.web.fakes import slot


@pytest.fixture
def reviewed(services):
    """From here on new events wait for an admin, as with the real service after CR-01."""
    services.events.auto_approve = False
    return services


@pytest.fixture
def admin(services):
    return make_user(services, "admin@bilgi.edu.tr", Role.ADMIN, "Demo Admin")


def request_by(services, hall, title="Chess club meetup", day=22, organizer=None):
    organizer = organizer or make_user(services, "organizer@bilgiedu.net", name="Demo Organizer")
    return services.events.create_event(organizer.id, title, "chess", hall.id, slot(day=day, hour=16), 12, "Beginners")


# admin: landing page, access -------------------------------------------------------------------------


def test_admin_lands_on_event_requests_after_login(client, admin):
    response = log_in(client, "admin@bilgi.edu.tr")
    assert response.status_code == 302 and response.headers["Location"].endswith("/admin/requests")
    assert client.get("/").headers["Location"].endswith("/admin/requests")
    page = client.get("/admin/requests").data
    assert b"Event Requests" in page and b"No requests are waiting." in page
    assert b'href="/events"' not in page  # admins do not get the student menu


def test_only_admins_can_open_the_requests_page(client, services, student):
    assert client.get("/admin/requests").status_code == 403  # a logged-in student
    client.post("/logout")
    assert client.get("/admin/requests").status_code == 302  # logged out: to the login page
    make_user(services, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    log_in(client, "staff@bilgi.edu.tr")
    assert client.get("/admin/requests").status_code == 403


def test_a_student_cannot_approve_or_reject(client, reviewed, hall, student):
    event = request_by(reviewed, hall)
    assert client.post(f"/admin/requests/{event.id}/approve").status_code == 403
    assert client.post(f"/admin/requests/{event.id}/reject", data={"reason": "no"}).status_code == 403
    assert event.status == EventStatus.PENDING


# admin: list, approve, reject ---------------------------------------------------------------------------


def test_requests_page_lists_pending_requests_soonest_first_without_e_mails(client, reviewed, hall, admin):
    later = request_by(reviewed, hall, "Later request", day=25)
    request_by(reviewed, hall, "Sooner request", day=21, organizer=reviewed.auth.get_user(later.organizer_id))
    log_in(client, "admin@bilgi.edu.tr")
    page = client.get("/admin/requests").data
    assert b"2 requests waiting" in page
    assert page.index(b"Sooner request") < page.index(b"Later request")
    assert b"Demo Organizer" in page and b"Santral Event Hall" in page and b"up to 12 people" in page
    assert b"@bilgiedu.net" not in page  # names only (NFR-05)


def test_admin_approves_a_request_and_it_is_listed(client, reviewed, hall, admin, services):
    event = request_by(reviewed, hall)
    log_in(client, "admin@bilgi.edu.tr")
    response = client.post(f"/admin/requests/{event.id}/approve", follow_redirects=True)
    assert b"is approved" in response.data and b"No requests are waiting." in response.data
    assert event.status == EventStatus.OPEN and event.reviewed_by == admin.id
    assert ("organizer@bilgiedu.net", "Chess club meetup", True, "") in services.auth.email_sender.decisions
    assert event in services.events.search_events()


def test_admin_rejects_a_request_with_a_reason(client, reviewed, hall, admin, services):
    event = request_by(reviewed, hall)
    log_in(client, "admin@bilgi.edu.tr")
    response = client.post(f"/admin/requests/{event.id}/reject", data={"reason": " Hall is closed for exams "},
                           follow_redirects=True)
    assert b"is rejected" in response.data
    assert event.status == EventStatus.REJECTED and event.rejection_reason == "Hall is closed for exams"
    decision = ("organizer@bilgiedu.net", "Chess club meetup", False, "Hall is closed for exams")
    assert decision in services.auth.email_sender.decisions
    assert services.facilities.get_schedule(hall.id, event.slot.start.date()) == []  # the slot is free again


def test_rejection_without_a_reason_keeps_the_request_and_says_why(client, reviewed, hall, admin):
    event = request_by(reviewed, hall)
    log_in(client, "admin@bilgi.edu.tr")
    response = client.post(f"/admin/requests/{event.id}/reject", data={"reason": "   "})
    assert response.status_code == 400
    assert b"Please give a reason" in response.data
    assert b"<details class=\"flex-grow-1\" open" in response.data  # the reason box stays open
    assert event.status == EventStatus.PENDING


def test_a_too_long_reason_is_refused_and_kept_in_the_box(client, reviewed, hall, admin):
    event = request_by(reviewed, hall)
    log_in(client, "admin@bilgi.edu.tr")
    response = client.post(f"/admin/requests/{event.id}/reject", data={"reason": "x" * 501})
    assert response.status_code == 400 and b"under 500 characters" in response.data
    assert event.status == EventStatus.PENDING


def test_a_request_that_is_no_longer_pending_cannot_be_reviewed_again(client, reviewed, hall, admin, services):
    event = request_by(reviewed, hall)
    other = request_by(reviewed, hall, "Still waiting", day=24, organizer=services.auth.get_user(event.organizer_id))
    services.events.approve_event(event.id, admin.id)
    log_in(client, "admin@bilgi.edu.tr")
    response = client.post(f"/admin/requests/{event.id}/reject", data={"reason": "Too late"})
    assert response.status_code == 409 and b"no longer pending" in response.data and b"alert-warning" in response.data
    assert b"Still waiting" in response.data and other.status == EventStatus.PENDING
    assert event.status == EventStatus.OPEN


def test_the_reason_is_escaped_on_every_page(client, reviewed, hall, admin, services):
    event = request_by(reviewed, hall, organizer=make_user(services, "student@bilgiedu.net"))
    services.events.reject_event(event.id, admin.id, "<script>alert(1)</script>")
    log_in(client, "student@bilgiedu.net")
    for url in (f"/events/{event.id}", "/activities"):
        page = client.get(url).data
        assert b"<script>alert(1)</script>" not in page and b"&lt;script&gt;" in page


# organizer: pending and rejected requests ---------------------------------------------------------------


def test_a_new_event_is_sent_for_review_and_not_listed(client, reviewed, hall, student):
    response = client.post("/events/new", data={
        "title": "Secret chess round", "category": "chess", "facility_id": str(hall.id), "date": "2026-11-21",
        "start": "10:00", "end": "11:00", "capacity": "4",
    }, follow_redirects=True)
    assert b"Your request is sent" in response.data
    assert b"Waiting for approval" in response.data and b"Withdraw request" in response.data
    assert b"Join event" not in response.data and b"Add to calendar" not in response.data
    assert b"Secret chess round" not in client.get("/events").data  # pending events are not listed


def test_other_students_cannot_open_a_pending_or_rejected_request(client, reviewed, hall, admin, student):
    pending = request_by(reviewed, hall)
    rejected = request_by(reviewed, hall, "Refused", day=23, organizer=reviewed.auth.get_user(pending.organizer_id))
    reviewed.events.reject_event(rejected.id, admin.id, "No")
    for event in (pending, rejected):
        assert client.get(f"/events/{event.id}").status_code == 404
        assert client.get(f"/events/{event.id}/calendar.ics").status_code == 404
        assert client.post(f"/events/{event.id}/join").status_code == 404


def test_organizer_sees_the_rejection_reason_and_can_submit_a_corrected_request(client, reviewed, hall, admin, student):
    event = request_by(reviewed, hall, "Late karaoke", organizer=student)
    reviewed.events.reject_event(event.id, admin.id, "The hall closes at 22:00")
    page = client.get(f"/events/{event.id}").data
    assert b"Your request was rejected." in page and b"Reason: The hall closes at 22:00" in page
    assert b"Back to My Activities" in page and b"Withdraw request" not in page
    link = f"/events/new?title=Late+karaoke&amp;category=chess&amp;facility_id={hall.id}".encode()
    assert link in page
    form = client.get(f"/events/new?title=Late+karaoke&category=chess&facility_id={hall.id}&capacity=12").data
    assert b'value="Late karaoke"' in form and b'value="12"' in form and b"selected" in form


def test_organizer_withdraws_a_pending_request(client, reviewed, hall, student):
    event = request_by(reviewed, hall, organizer=student)
    response = client.post(f"/events/{event.id}/cancel", follow_redirects=True)
    assert b"Your request is withdrawn" in response.data
    assert event.status == EventStatus.CANCELLED
    assert reviewed.facilities.get_schedule(hall.id, event.slot.start.date()) == []


def test_my_activities_lists_my_requests_in_every_status(client, reviewed, hall, admin, student):
    waiting = request_by(reviewed, hall, "Waiting one", day=24, organizer=student)
    refused = request_by(reviewed, hall, "Refused one", day=25, organizer=student)
    approved = request_by(reviewed, hall, "Approved one", day=21, organizer=student)
    reviewed.events.reject_event(refused.id, admin.id, "Exams that week")
    reviewed.events.approve_event(approved.id, admin.id)
    request_by(reviewed, hall, "Someone else's", day=26)

    page = client.get("/activities").data
    assert b"My requests and events" in page
    assert page.index(b"Waiting one") < page.index(b"Refused one") < page.index(b"Approved one")
    assert b"Waiting for approval" in page and b"Rejected" in page and b"Open" in page
    assert b"Reason: Exams that week" in page and b"Submit a corrected request" in page
    assert b"Someone else" not in page
    assert waiting.status == EventStatus.PENDING


def test_my_activities_has_no_request_section_without_own_events(client, student):
    page = client.get("/activities").data
    assert b"My requests and events" not in page and b"No completed events yet." in page


# follow-ups of the review of PR #7 ------------------------------------------------------------------------


def test_missing_secret_key_is_logged_as_a_warning(services, monkeypatch, caplog):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with caplog.at_level(logging.WARNING):
        create_web_app(services, {"TESTING": True})
    assert "SECRET_KEY is not set" in caplog.text

    caplog.clear()
    monkeypatch.setenv("SECRET_KEY", "from-the-environment")
    with caplog.at_level(logging.WARNING):
        create_web_app(services, {"TESTING": True})
    assert "SECRET_KEY" not in caplog.text


def test_pages_have_a_favicon(client):
    assert b'rel="icon" href="/static/favicon.svg"' in client.get("/login").data
    old_path = client.get("/favicon.ico")
    assert old_path.status_code == 301 and old_path.headers["Location"].endswith("/static/favicon.svg")
    icon = client.get("/static/favicon.svg")
    assert icon.status_code == 200 and b"<svg" in icon.data
    icon.close()


def test_schedule_box_waits_for_a_complete_date(client, student):
    page = client.get("/events/new").data
    assert b"completeDate(date.value)" in page and b"addEventListener('change', scheduleSoon)" in page
