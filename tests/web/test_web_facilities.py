"""Web UI for UC-07 and UC-08: the Facility Management page of the facility staff (task 3.6).

These tests use the real FacilityService (task 3.3) with the fake AuthService and fake events of
tests/web/fakes.py. Services keep naive UTC; the page shows and takes Istanbul time (UTC+3).
"""

from datetime import date, datetime

import pytest

from campusevent.facilities import FacilityService
from campusevent.models import Role, TimeSlot
from tests.web.conftest import log_in, make_user
from tests.web.fakes import slot


@pytest.fixture
def facilities(services):
    real = FacilityService(services.auth, events=services.events)  # FakeEvents.active_on
    services.facilities = real
    services.events.facilities = real  # create_event books through check_bookable
    return real


@pytest.fixture
def staff(services, client, facilities):
    user = make_user(services, "staff@bilgi.edu.tr", Role.FACILITY_STAFF, "Facility Staff")
    log_in(client, "staff@bilgi.edu.tr")
    return user


@pytest.fixture
def court(facilities, staff):
    return facilities.add_facility(staff.id, "Dorm Basketball Court", 20)


def block(client, facility, **overrides):
    data = {"date": "2026-11-20", "start": "09:00", "end": "12:00", "reason": "Physical education class", **overrides}
    return client.post(f"/facilities/{facility.id}/blocks", data=data)


# access ------------------------------------------------------------------------------------------


def test_staff_lands_on_facility_management_after_login(client, services, facilities):
    make_user(services, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    response = log_in(client, "staff@bilgi.edu.tr")
    assert response.status_code == 302 and response.headers["Location"].endswith("/facilities")
    page = client.get("/facilities").data
    assert b"Facility Management" in page and b"No facility yet." in page
    assert b'class="nav-link active" href="/facilities"' in page
    assert b'href="/events"' not in page  # staff do not get the student menu


def test_only_staff_can_open_the_page(client, services, student, facilities):
    assert client.get("/facilities").status_code == 403
    assert client.post("/facilities", data={"name": "Fake Court", "capacity": "10"}).status_code == 403
    assert facilities.list_facilities() == []
    client.post("/logout")
    assert client.get("/facilities").status_code == 302  # logged out: to the login page
    make_user(services, "admin@bilgi.edu.tr", Role.ADMIN)
    log_in(client, "admin@bilgi.edu.tr")
    assert client.get("/facilities").status_code == 403


# UC-08 add a facility ----------------------------------------------------------------------------


def test_staff_adds_a_facility(client, staff, facilities):
    response = client.post("/facilities", data={"name": "  Santral Event Hall ", "capacity": "50"})
    assert response.status_code == 302
    hall = facilities.list_facilities()[0]
    assert (hall.name, hall.capacity) == ("Santral Event Hall", 50)
    assert response.headers["Location"].endswith(f"/facilities?facility={hall.id}")
    page = client.get(response.headers["Location"]).data
    assert b"&#34;Santral Event Hall&#34; is added." in page
    assert b"Capacity 50" in page


@pytest.mark.parametrize(
    "capacity, message",
    [("1", b"at least 2"), ("", b"Capacity must be a whole number."), ("ten", b"Capacity must be a whole number.")],
)
def test_wrong_capacity_is_explained_and_the_name_is_kept(client, staff, facilities, capacity, message):
    response = client.post("/facilities", data={"name": "Tennis Court", "capacity": capacity})
    assert response.status_code == 400
    assert message in response.data
    assert b'value="Tennis Court"' in response.data
    assert facilities.list_facilities() == []


def test_duplicate_facility_name_is_refused(client, staff, court):
    response = client.post("/facilities", data={"name": "dorm basketball COURT", "capacity": "10"})
    assert response.status_code == 400
    assert b"already exists" in response.data


def test_facilities_are_listed_with_capacity_and_the_first_is_selected(client, staff, facilities):
    facilities.add_facility(staff.id, "Tennis Court", 4)
    facilities.add_facility(staff.id, "Room B-204", 30)
    page = client.get("/facilities").data.decode()
    assert page.index("Room B-204") < page.index("Tennis Court")  # sorted by name
    assert 'aria-current="true">\n          <span class="text-truncate">Room B-204' in page


# UC-08 block a time ------------------------------------------------------------------------------


def test_staff_blocks_a_time_in_istanbul_time(client, staff, court, facilities):
    response = block(client, court)
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/facilities?facility={court.id}&date=2026-11-20")
    # 09:00-12:00 in Istanbul is 06:00-09:00 UTC in the service
    assert facilities.get_blocks(court.id, date(2026, 11, 20))[0].slot == TimeSlot(
        datetime(2026, 11, 20, 6), datetime(2026, 11, 20, 9)
    )
    page = client.get(response.headers["Location"]).data
    assert b"is blocked. Students cannot book this time." in page
    assert b"09:00 \xe2\x80\x93 12:00" in page and b"Blocked: Physical education class" in page


def test_a_blocked_time_cannot_be_booked(client, staff, court, facilities):
    block(client, court)
    assert facilities.is_available(court.id, TimeSlot(datetime(2026, 11, 20, 7), datetime(2026, 11, 20, 8))) is False


def test_overlapping_block_is_refused_and_the_form_is_kept(client, staff, court):
    block(client, court)
    response = block(client, court, start="11:00", end="13:00", reason="Maintenance")
    assert response.status_code == 400
    assert b"overlaps another block" in response.data
    assert b'value="Maintenance"' in response.data and b'value="11:00"' in response.data


def test_block_over_an_event_booking_is_refused(client, services, staff, court):
    organizer = make_user(services, "organizer@bilgiedu.net")
    services.events.create_event(organizer.id, "Pickup game", "basketball", court.id, slot(day=20, hour=9), 6)
    response = block(client, court, start="09:30", end="10:30")
    assert response.status_code == 409
    assert b"An event is booked in this time, so it cannot be blocked." in response.data


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"reason": "  "}, b"Please enter a reason"),
        ({"end": "08:00"}, b"The end time must be after the start time."),
        ({"date": "20.11.2026"}, b"Please enter a valid date"),
    ],
)
def test_wrong_block_input_is_explained(client, staff, court, facilities, overrides, message):
    response = block(client, court, **overrides)
    assert response.status_code == 400
    assert message in response.data
    assert facilities.get_blocks(court.id, date(2026, 11, 20)) == []


def test_block_for_an_unknown_facility(client, staff):
    response = client.post("/facilities/99/blocks", data={"date": "2026-11-20", "start": "09:00", "end": "10:00", "reason": "x"})
    assert response.status_code == 404


# UC-07 schedule of one day -----------------------------------------------------------------------


def test_schedule_shows_blocks_and_bookings_of_the_istanbul_day(client, services, staff, court):
    organizer = make_user(services, "organizer@bilgiedu.net")
    # slot() takes Istanbul time. The 01:00 block is 22:00 UTC on 19 Nov: the page must ask for both UTC days.
    services.events.create_event(organizer.id, "Pickup game", "basketball", court.id, slot(day=20, hour=18), 6)
    block(client, court, date="2026-11-20", start="01:00", end="02:00", reason="Cleaning")
    page = client.get(f"/facilities?facility={court.id}&date=2026-11-20").data.decode()
    assert "01:00 – 02:00" in page and "Blocked: Cleaning" in page
    assert "18:00 – 19:00" in page and "Event: Pickup game" in page
    assert page.index("Cleaning") < page.index("Pickup game")  # sorted by time
    other_day = client.get(f"/facilities?facility={court.id}&date=2026-11-19").data
    assert b"Nothing is blocked or booked on this day." in other_day


def test_cancelled_events_do_not_show_in_the_schedule(client, services, staff, court):
    organizer = make_user(services, "organizer@bilgiedu.net")
    event = services.events.create_event(organizer.id, "Pickup game", "basketball", court.id, slot(day=20, hour=18), 6)
    services.events.cancel_event(event.id, organizer.id)
    page = client.get(f"/facilities?facility={court.id}&date=2026-11-20").data
    assert b"Pickup game" not in page


def test_wrong_facility_or_date_in_the_address(client, staff, court):
    assert client.get("/facilities?facility=99").status_code == 404
    assert client.get("/facilities?facility=abc").status_code == 400
    assert client.get(f"/facilities?facility={court.id}&date=yesterday").status_code == 400


# UC-08 alt. 2b: remove a block (issue #19) ---------------------------------------------------------


def test_each_block_has_a_remove_button_with_a_confirmation(client, staff, court, facilities):
    block(client, court)
    added = facilities.get_blocks(court.id, date(2026, 11, 20))[0]
    page = client.get(f"/facilities?facility={court.id}&date=2026-11-20").data.decode()
    assert f'action="/facilities/{court.id}/blocks/{added.id}/remove"' in page
    assert 'data-block="09:00 – 12:00 (Physical education class)"' in page
    assert "Remove this block?" in page and "Yes, remove it" in page


def test_staff_removes_a_block(client, staff, court, facilities):
    block(client, court)
    added = facilities.get_blocks(court.id, date(2026, 11, 20))[0]
    response = client.post(f"/facilities/{court.id}/blocks/{added.id}/remove")
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/facilities?facility={court.id}&date=2026-11-20")
    assert facilities.get_blocks(court.id, date(2026, 11, 20)) == []
    page = client.get(response.headers["Location"]).data.decode()
    assert "The block 20 Nov 2026, 09:00 – 12:00 (&#34;Physical education class&#34;) is removed." in page
    assert "Nothing is blocked or booked on this day." in page


def test_only_staff_can_remove_a_block(client, services, court, facilities):
    block(client, court)
    added = facilities.get_blocks(court.id, date(2026, 11, 20))[0]
    client.post("/logout")
    for email, role in (("student@bilgiedu.net", Role.STUDENT), ("admin@bilgi.edu.tr", Role.ADMIN)):
        make_user(services, email, role)
        log_in(client, email)
        assert client.post(f"/facilities/{court.id}/blocks/{added.id}/remove").status_code == 403
        client.post("/logout")
    assert facilities.get_blocks(court.id, date(2026, 11, 20)) == [added]


def test_removing_an_unknown_block_or_one_of_another_facility(client, staff, court, facilities):
    other = facilities.add_facility(staff.id, "Tennis Court", 4)
    block(client, court)
    added = facilities.get_blocks(court.id, date(2026, 11, 20))[0]
    assert client.post(f"/facilities/{court.id}/blocks/99/remove").status_code == 404
    assert client.post(f"/facilities/{other.id}/blocks/{added.id}/remove").status_code == 404
    assert facilities.get_blocks(court.id, date(2026, 11, 20)) == [added]


def test_schedule_shows_event_titles_and_pending_requests(client, services, staff, court):
    organizer = make_user(services, "organizer@bilgiedu.net")
    services.events.create_event(organizer.id, "Pickup game", "basketball", court.id, slot(day=20, hour=18), 6)
    services.events.auto_approve = False
    services.events.create_event(organizer.id, "Chess club", "chess", court.id, slot(day=20, hour=20), 6)
    page = client.get(f"/facilities?facility={court.id}&date=2026-11-20").data.decode()
    assert "Event: Pickup game" in page
    assert "Event: Chess club" in page and "(waiting for approval)" in page
    assert "organizer@bilgiedu.net" not in page  # names of events only, never e-mail addresses (NFR-05)
