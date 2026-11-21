"""Tests for the helper features of the web UI: free time suggestions (UC-04 4a), the facility schedule box,
'Add to calendar', pagination and category shortcuts on Find Events, interest tags, the password guide."""

import re
from datetime import date, datetime

import pytest

from campusevent.models import TimeSlot
from campusevent.web import common, create_web_app
from tests.web.conftest import make_user
from tests.web.fakes import PASSWORD, slot

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


def test_today_is_the_istanbul_date_even_when_the_server_runs_in_utc():
    from datetime import timezone

    late_night_utc = datetime(2026, 11, 19, 22, 30, tzinfo=timezone.utc)  # 01:30 on 20 Nov in Istanbul
    assert common.campus_today(late_night_utc) == date(2026, 11, 20)
    assert common.campus_today(datetime(2026, 11, 19, 20, 59, tzinfo=timezone.utc)) == date(2026, 11, 19)
    # a 10:00 event on 20 Nov is "Today" for a student looking at it at 01:30, not "Tomorrow"
    assert common.relative_day(datetime(2026, 11, 20, 10), common.campus_today(late_night_utc)) == "Today"


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
    # 18:00-19:00 Istanbul time, written in UTC form so every calendar shows the right moment
    assert "DTSTART:20261120T150000Z" in text and "DTEND:20261120T160000Z" in text
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


# time rule: services keep naive UTC, people see Istanbul time ---------------------------------------------


def test_time_conversion_helpers_round_trip():
    local = datetime(2026, 11, 21, 0, 30)
    assert common.to_utc(local) == datetime(2026, 11, 20, 21, 30)  # Istanbul is UTC+3
    assert common.to_campus(common.to_utc(local)) == local
    assert common.campus_day_in_utc(date(2026, 11, 21)) == (datetime(2026, 11, 20, 21, 0), datetime(2026, 11, 21, 21, 0))


def test_an_event_just_after_midnight_belongs_to_its_istanbul_day(client, student, hall, services):
    organizer = make_user(services, "organizer@bilgiedu.net")
    # 01:00 on 21 Nov in Istanbul is 22:00 on 20 Nov in UTC: the UTC date and the campus date differ
    event = services.events.create_event(organizer.id, "Night owls", "chess", hall.id, slot(day=21, hour=1), 4)
    assert event.slot.start == datetime(2026, 11, 20, 22, 0)

    assert b"Night owls" in client.get("/events?date=2026-11-21").data  # date filter uses the campus day
    assert b"Night owls" not in client.get("/events?date=2026-11-20").data
    assert b"Busy: 01:00" in client.get(f"/events/schedule?facility_id={hall.id}&date=2026-11-21").data
    assert b"Busy" not in client.get(f"/events/schedule?facility_id={hall.id}&date=2026-11-20").data
    assert b"Saturday, 21 Nov 2026" in client.get(f"/events/{event.id}").data  # the details page shows the campus date


# animated backgrounds ----------------------------------------------------------------------------------------


def test_every_page_has_the_campus_background_with_fireworks_by_default(client, student, services):
    page = client.get("/events").data
    assert b'class="bgfx-layer fx-campus"' in page and b'data-background="campus-festival"' in page
    assert b'id="bg-switcher"' not in page  # the comparison buttons of the demo are gone
    client.post("/logout")
    assert b'class="bgfx-layer fx-campus"' in client.get("/login").data  # the log in page too

    other = create_web_app(services, {"TESTING": True, "SECRET_KEY": "t", "BACKGROUND": "campus-dusk"})
    assert b'data-background="campus-dusk"' in other.test_client().get("/login").data  # another look by setting


# accessibility: labels -------------------------------------------------------------------------------------------


def _fields_without_a_label(html: str) -> list[str]:
    """Visible form fields (input, select, textarea) that have neither a <label for=...> nor an aria-label."""
    labelled = set(re.findall(r'<label[^>]*\bfor="([^"]+)"', html))
    missing = []
    for tag in re.findall(r"<(?:input|select|textarea)\b[^>]*>", html):
        if re.search(r'type="(hidden|submit|button)"', tag):
            continue
        field_id = re.search(r'\bid="([^"]+)"', tag)
        if "aria-label=" in tag or (field_id and field_id.group(1) in labelled):
            continue
        missing.append(tag[:80])
    return missing


def test_every_form_field_has_a_label(client, services, hall):
    """WCAG 1.3.1 and 3.3.2 (NFR-01): screen readers need a name for every field, also without JavaScript."""
    pages = {}
    for path in ("/login", "/signup", "/verify"):
        pages[path] = client.get(path).get_data(as_text=True)
    make_user(services, "student@bilgiedu.net")
    client.post("/login", data={"email": "student@bilgiedu.net", "password": PASSWORD})
    for path in ("/events", "/events/new", "/profile"):
        pages[path] = client.get(path).get_data(as_text=True)
    for path, html in pages.items():
        assert _fields_without_a_label(html) == [], path


def test_create_form_category_label_follows_the_visible_field(client, student, hall):
    page = client.get("/events/new").get_data(as_text=True)
    # without JavaScript only the text field is visible, so "Category" names it
    assert '<label class="form-label" for="category" id="category-label">Category</label>' in page
    # with JavaScript the list is shown: the script moves "Category" to it and shows the text field's own label
    assert 'id="category-other-label" hidden>Your own category</label>' in page
    assert "getElementById('category-label').htmlFor = 'category_choice'" in page
