"""Error and edge paths of the web UI that the feature tests did not reach, found while writing the
Software Testing Report (task 4.1): eight by the coverage measurement, and three alternative flows of the
use cases (UC-04 1a, UC-10 1a, UC-11 1b) by the traceability matrix."""

from datetime import date, datetime

from campusevent.models import EventStatus, Role, TimeSlot
from campusevent.web import common, create_web_app
from tests.web.conftest import log_in, make_user
from tests.web.fakes import slot


def test_start_page_sends_visitors_to_log_in_and_users_to_their_own_page(client, services):
    assert client.get("/").headers["Location"].endswith("/login")
    make_user(services, "student@bilgiedu.net")
    log_in(client, "student@bilgiedu.net")
    assert client.get("/").headers["Location"].endswith("/events")


def test_unknown_address_shows_the_error_page(client):
    response = client.get("/no-such-page")
    assert response.status_code == 404
    assert b"This page does not exist." in response.data


def test_unexpected_error_shows_a_friendly_page_and_is_logged(services, caplog):
    # TESTING would pass the exception on to the test; the deployed app uses the 500 handler.
    app = create_web_app(services, {"WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "test"})
    client = app.test_client()
    make_user(services, "student@bilgiedu.net")
    log_in(client, "student@bilgiedu.net")

    def broken(*args, **kwargs):
        raise RuntimeError("database is down")

    services.events.search_events = broken
    response = client.get("/events")
    assert response.status_code == 500
    assert b"Something went wrong. Please try again later." in response.data
    assert b"database is down" not in response.data  # no technical details on the page
    assert "Unexpected error" in caplog.text


def test_a_token_the_service_no_longer_accepts_logs_the_user_out(client):
    with client.session_transaction() as session:
        session[common.TOKEN_KEY] = "expired-or-made-up"
    response = client.get("/events")
    assert response.headers["Location"].endswith("/login")
    with client.session_transaction() as session:
        assert common.TOKEN_KEY not in session  # dropped, so it is not checked again on every page


def test_approving_a_request_that_is_no_longer_pending_is_refused(client, services, hall):
    services.events.auto_approve = False
    admin = make_user(services, "admin@bilgi.edu.tr", Role.ADMIN, "Demo Admin")
    organizer = make_user(services, "organizer@bilgiedu.net")
    event = services.events.create_event(organizer.id, "Chess club meetup", "chess", hall.id, slot(day=22), 12)
    services.events.reject_event(event.id, admin.id, "The hall is booked for exams.")
    log_in(client, "admin@bilgi.edu.tr")
    response = client.post(f"/admin/requests/{event.id}/approve")
    assert response.status_code == 409
    assert b"no longer pending" in response.data
    assert event.status == EventStatus.REJECTED


def test_free_slots_stop_at_a_busy_slot_that_lasts_until_closing_time():
    day = date(2026, 11, 20)
    busy = [TimeSlot(datetime(2026, 11, 20, 9), datetime(2026, 11, 20, 23)),
            TimeSlot(datetime(2026, 11, 20, 23), datetime(2026, 11, 21, 1))]
    assert common.free_slots(busy, day) == [TimeSlot(datetime(2026, 11, 20, 8), datetime(2026, 11, 20, 9))]


def test_an_empty_title_is_refused_and_the_form_is_kept(client, student, hall):
    """UC-04 alt. 1a."""
    response = client.post("/events/new", data={
        "title": "   ", "category": "Board Games", "date": "2026-11-20", "start": "18:00", "end": "19:00",
        "facility_id": str(hall.id), "capacity": "6", "description": "Bring your own games",
    })
    assert response.status_code == 400
    assert b"Title and category are required." in response.data
    assert b"Bring your own games" in response.data  # what was typed stays in the form


def test_leaving_an_event_you_have_not_joined_is_refused(client, student, hall, services):
    """UC-10 alt. 1a."""
    organizer = make_user(services, "organizer@bilgiedu.net")
    event = services.events.create_event(organizer.id, "Game night", "board games", hall.id, slot(day=22), 6)
    response = client.post(f"/events/{event.id}/leave")
    assert response.status_code == 400
    assert b"You are not a participant of this event." in response.data
    assert event.participant_ids == [organizer.id]


def test_cancelling_an_event_that_is_already_cancelled_is_refused(client, student, hall, services):
    """UC-11 alt. 1b."""
    event = services.events.create_event(student.id, "Game night", "board games", hall.id, slot(day=22), 6)
    services.events.cancel_event(event.id, student.id)
    response = client.post(f"/events/{event.id}/cancel")
    assert response.status_code == 400
    assert b"This event can no longer be cancelled." in response.data
    assert event.status == EventStatus.CANCELLED


def test_calendar_file_of_an_event_without_description_has_no_empty_description_line():
    body = common.ics_for(7, "Football friendly", "Main Court", datetime(2026, 11, 21, 14), datetime(2026, 11, 21, 15))
    assert "DESCRIPTION" not in body
    assert "DTSTART:20261121T140000Z" in body and body.endswith("END:VCALENDAR\r\n")


def test_a_participant_whose_account_is_gone_is_shown_as_unknown_user(client, student, services, hall):
    organizer = make_user(services, "organizer@bilgiedu.net", name="Gone Organizer")
    event = services.events.create_event(organizer.id, "Board game night", "board games", hall.id, slot(day=22), 8)
    del services.auth.users[organizer.id]
    page = client.get(f"/events/{event.id}").get_data(as_text=True)
    assert "Unknown user" in page and "Gone Organizer" not in page
