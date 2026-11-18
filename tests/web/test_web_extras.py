"""Tests for the helper features of the web UI: free time suggestions (UC-04 4a), the facility schedule box,
'Add to calendar', pagination and category shortcuts on Find Events, interest tags, the password guide."""

from datetime import date, datetime

import pytest

from campusevent.models import TimeSlot
from campusevent.web import common
from tests.web.conftest import make_user
from tests.web.fakes import slot

DAY = date(2026, 11, 20)


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, 20, hour, minute)


# free_slots -------------------------------------------------------------------------------------


def test_free_slots_of_an_empty_day_is_the_whole_opening_time():
    assert common.free_slots([], DAY) == [TimeSlot(at(8), at(22))]


def test_free_slots_are_the_gaps_between_busy_slots():
    busy = [TimeSlot(at(10), at(12)), TimeSlot(at(18), at(19))]
    assert common.free_slots(busy, DAY) == [
        TimeSlot(at(8), at(10)), TimeSlot(at(12), at(18)), TimeSlot(at(19), at(22)),
    ]


def test_free_slots_skip_short_gaps_and_handle_overlapping_busy_slots():
    busy = [TimeSlot(at(8), at(11)), TimeSlot(at(10), at(13)), TimeSlot(at(13, 30), at(21, 30))]
    assert common.free_slots(busy, DAY) == []  # 13:00-13:30 and 21:30-22:00 are shorter than one hour


def test_relative_day_labels():
    today = date(2026, 11, 17)
    assert common.relative_day(datetime(2026, 11, 17, 9), today) == "Today"
    assert common.relative_day(datetime(2026, 11, 18, 9), today) == "Tomorrow"
    assert common.relative_day(datetime(2026, 11, 20, 9), today) == "In 3 days"
    assert common.relative_day(datetime(2026, 11, 16, 9), today) == "Yesterday"
    assert common.relative_day(datetime(2026, 11, 10, 9), today) == "7 days ago"


# schedule box and suggestions --------------------------------------------------------------------


def test_schedule_box_shows_busy_and_free_times(client, student, hall, services):
    organizer = make_user(services, "organizer@bilgiedu.net")
    services.events.create_event(organizer.id, "Game night", "board games", hall.id, slot(day=20, hour=18), 6)
    box = client.get(f"/events/schedule?facility_id={hall.id}&date=2026-11-20").data
    assert b"Busy: 18:00" in box
    assert b'data-start="08:00" data-end="18:00"' in box
    assert b'data-start="19:00" data-end="22:00"' in box
    assert b"<html" not in box  # only the box, not a whole page


def test_schedule_box_without_facility_asks_for_one(client, student):
    assert b"Choose a facility and a date" in client.get("/events/schedule").data


def test_schedule_box_needs_login(client):
    assert client.get("/events/schedule").status_code == 302


def test_busy_slot_error_suggests_free_times_of_the_day(client, student, hall, services):
    organizer = make_user(services, "organizer@bilgiedu.net")
    services.events.create_event(organizer.id, "Game night", "board games", hall.id, slot(day=20, hour=18), 6)
    response = client.post("/events/new", data={
        "title": "Chess", "category": "chess", "facility_id": str(hall.id), "date": "2026-11-20",
        "start": "18:30", "end": "19:30", "capacity": "4",
    })
    assert response.status_code == 409
    assert b"This slot is busy" in response.data
    assert b"Free times" in response.data
    assert b'data-start="19:00"' in response.data  # UC-04 4a: free slots of the same day


def test_create_form_tells_the_capacity_of_each_facility(client, student, hall):
    assert b'data-capacity="50"' in client.get("/events/new").data


# add to calendar ----------------------------------------------------------------------------------


def test_add_to_calendar_downloads_an_ics_file(client, student, hall, services):
    organizer = make_user(services, "organizer@bilgiedu.net")
    event = services.events.create_event(
        organizer.id, "Game night, round 2", "board games", hall.id, slot(day=20, hour=18), 6, "Bring snacks; and games"
    )
    response = client.get(f"/events/{event.id}/calendar.ics")
    assert response.status_code == 200
    assert response.mimetype == "text/calendar"
    assert "attachment" in response.headers["Content-Disposition"]
    text = response.data.decode()
    assert "BEGIN:VEVENT" in text and "END:VCALENDAR" in text
    assert "DTSTART;TZID=Europe/Istanbul:20261120T180000" in text and "DTEND;TZID=Europe/Istanbul:20261120T190000" in text
    # the time zone is defined in the file (RFC 5545 asks for a VTIMEZONE for every TZID used): UTC+3, no summer time
    assert "BEGIN:VTIMEZONE" in text and "TZID:Europe/Istanbul" in text and "TZOFFSETTO:+0300" in text
    assert text.index("END:VTIMEZONE") < text.index("BEGIN:VEVENT")
    assert all(line.endswith("\r") or not line for line in text.split("\n"))  # CRLF line ends
    assert "SUMMARY:Game night\\, round 2" in text  # commas are escaped as RFC 5545 asks
    assert "DESCRIPTION:Bring snacks\\; and games" in text
    assert "LOCATION:Santral Event Hall" in text
    assert "@bilgiedu.net" not in text  # no e-mail addresses (NFR-05)


def test_event_page_links_to_the_calendar_file(client, student, hall, services):
    organizer = make_user(services, "organizer@bilgiedu.net")
    event = services.events.create_event(organizer.id, "Game night", "board games", hall.id, slot(day=20), 6)
    assert f"/events/{event.id}/calendar.ics".encode() in client.get(f"/events/{event.id}").data


def test_only_the_organizer_gets_the_cancel_confirmation_window(client, student, hall, services):
    client.post("/events/new", data={
        "title": "Mine", "category": "chess", "facility_id": str(hall.id), "date": "2026-11-21",
        "start": "10:00", "end": "11:00", "capacity": "4",
    })
    assert b'id="cancel-modal"' in client.get("/events/1").data
    organizer = make_user(services, "organizer@bilgiedu.net")
    other = services.events.create_event(organizer.id, "Theirs", "chess", hall.id, slot(day=22), 4)
    assert b'id="cancel-modal"' not in client.get(f"/events/{other.id}").data


# a status the UI does not know (a later change request could add one) -----------------------------


def test_event_with_a_status_the_page_does_not_know_still_opens(client, student, hall, services):
    from enum import Enum

    class FutureStatus(str, Enum):  # stands in for a status a later change request might add
        ARCHIVED = "archived"

    organizer = make_user(services, "organizer@bilgiedu.net")
    event = services.events.create_event(organizer.id, "Old event", "chess", hall.id, slot(day=20), 4)
    event.status = FutureStatus.ARCHIVED

    page = client.get(f"/events/{event.id}")
    assert page.status_code == 200
    assert b"Archived" in page.data and b"text-bg-secondary" in page.data
    assert b"Join event" not in page.data  # only open events can be joined


# find events ---------------------------------------------------------------------------------------


def test_find_events_shows_twenty_events_per_page(client, student, hall, services):
    organizer = make_user(services, "organizer@bilgiedu.net")
    for day in range(1, 26):
        services.events.create_event(organizer.id, f"Event {day:02d}", "chess", hall.id, slot(day=day), 4)
    first = client.get("/events").data
    assert b"Event 20" in first and b"Event 21" not in first
    assert b"25 events" in first and b"page 1 of 2" in first
    second = client.get("/events?page=2").data
    assert b"Event 21" in second and b"Event 25" in second and b"Event 20" not in second
    assert client.get("/events?page=99").status_code == 200  # a page after the last shows the last page
    assert client.get("/events?page=abc").status_code == 200


def test_pagination_links_keep_the_filters(client, student, hall, services):
    organizer = make_user(services, "organizer@bilgiedu.net")
    for day in range(1, 23):
        services.events.create_event(organizer.id, f"Match {day:02d}", "chess", hall.id, slot(day=day), 4)
    page = client.get("/events?category=chess").data
    assert b"/events?page=2&amp;category=chess" in page or b"/events?category=chess&amp;page=2" in page


def test_category_shortcuts_filter_with_one_click(client, student):
    page = client.get("/events?keyword=night").data
    assert b'href="/events?keyword=night"' in page  # "All" keeps the keyword
    assert b"category=Football" in page
    assert b"Clear all filters" in page
    assert b"Clear all filters" not in client.get("/events").data


def test_joined_event_card_has_a_leave_button_that_returns_to_the_same_list(client, student, hall, services):
    organizer = make_user(services, "organizer@bilgiedu.net")
    event = services.events.create_event(organizer.id, "Game night", "board games", hall.id, slot(day=20), 6)
    client.post(f"/events/{event.id}/join")
    page = client.get("/events?category=board+games").data
    assert b"You joined" in page and f'action="/events/{event.id}/leave"'.encode() in page
    assert b'name="next" value="/events?category=board+games"' in page

    left = client.post(f"/events/{event.id}/leave", data={"next": "/events?category=board+games"})
    assert left.status_code == 302 and left.headers["Location"] == "/events?category=board+games"
    assert student.id not in event.participant_ids
    assert b"Join" in client.get("/events?category=board+games").data


def test_organizer_card_has_no_leave_button(client, student, hall, services):
    client.post("/events/new", data={
        "title": "Mine", "category": "chess", "facility_id": str(hall.id), "date": "2026-11-21",
        "start": "10:00", "end": "11:00", "capacity": "4",
    })
    page = client.get("/events").data
    assert b"You joined" in page and b"/events/1/leave" not in page  # the organizer cancels instead


@pytest.mark.parametrize("target", ["https://evil.example/", "//evil.example/events", "/profile", r"/events?x=\evil", ""])
def test_leave_never_redirects_outside_find_events(client, student, hall, services, target):
    organizer = make_user(services, "organizer@bilgiedu.net")
    event = services.events.create_event(organizer.id, "Game night", "board games", hall.id, slot(day=20), 6)
    client.post(f"/events/{event.id}/join")
    left = client.post(f"/events/{event.id}/leave", data={"next": target})
    assert left.headers["Location"] == f"/events/{event.id}"  # unsafe or missing: the event page


def test_event_cards_show_how_far_away_the_event_is(client, student, hall, services):
    organizer = make_user(services, "organizer@bilgiedu.net")
    services.events.create_event(organizer.id, "Game night", "board games", hall.id, slot(day=20), 6)
    page = client.get("/events").data
    assert b'class="when-label' in page


# profile, sign up, layout --------------------------------------------------------------------------


def test_profile_offers_interest_suggestions_and_still_sends_the_text_field(client, student):
    page = client.get("/profile").data
    assert b'data-value="Basketball"' in page
    assert b'name="interests"' in page


def test_signup_has_a_password_strength_guide(client):
    assert b'id="pw-meter"' in client.get("/signup").data


def test_footer_is_on_the_pages_after_login_only(client, student):
    assert b"<footer" in client.get("/events").data
    assert b"<footer" not in client.get("/login").data
