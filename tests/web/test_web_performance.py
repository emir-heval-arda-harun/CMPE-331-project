"""NFR-02 through the web UI: with 1,000 open events the pages answer in under 2 seconds.

`tests/test_nfr.py` measures `EventService.search_events` alone. These tests measure a whole request through
Flask: routing, the service calls, the names of facilities and people, Istanbul time and the template.
- With the stand-ins of `fakes.py`: the cost of the web layer itself. They run everywhere, also in CI.
- With the real services (`create_app`, data in memory): the whole application without a database. They need
  `EventService` (task 3.4) and are skipped until it is on the branch.
Each page is opened three times and the slowest time is checked, so a single fast run cannot hide a slow one.
"""

import time
from datetime import datetime, timedelta

import pytest

from campusevent.models import EventStatus, Role, TimeSlot
from campusevent.web import create_web_app
from tests.helpers import PASSWORD as REAL_PASSWORD
from tests.helpers import verified_user
from tests.web.conftest import log_in, make_user

LIMIT = 2.0  # seconds, NFR-02
EVENTS = 1000
FIRST_START = datetime(2026, 11, 2, 6, 0)  # naive UTC; 09:00 in Istanbul
NOW = datetime(2026, 10, 31, 12, 0)  # before every event, like tests/conftest.py


def hourly_slot(i: int) -> TimeSlot:
    """Event number i, one hour each, one after the other (1,000 hours: 2 Nov to 14 Dec 2026)."""
    start = FIRST_START + timedelta(hours=i)
    return TimeSlot(start, start + timedelta(hours=1))


def slowest(client, url: str, runs: int = 3) -> float:
    times = []
    for _ in range(runs):
        started = time.perf_counter()
        response = client.get(url)
        times.append(time.perf_counter() - started)
        assert response.status_code == 200, (url, response.status_code)
    print(f"NFR-02 {url}: slowest of {runs} {max(times) * 1000:.0f} ms")  # shown with pytest -s
    return max(times)


# --------------------------------------------------------------------------- the web layer (stand-ins)
@pytest.fixture
def busy(services, client, hall):
    """1,000 open events of one organizer; 'student' joined 300 of them, so cards show *You joined*."""
    organizer = make_user(services, "organizer@bilgiedu.net", name="Demo Organizer")
    student = make_user(services, "student@bilgiedu.net", name="Test Student")
    for i in range(EVENTS):
        event = services.events.create_event(
            organizer.id, f"Event {i}", ("music", "football", "board games")[i % 3], hall.id, hourly_slot(i), 10
        )
        if i % 10 < 3:
            services.events.join_event(event.id, student.id)
    assert len(services.events.search_events()) == EVENTS  # really 1,000 open events to search
    log_in(client, "student@bilgiedu.net")
    return organizer


FIND_EVENTS = [
    "/events",  # first page: 20 of 1,000
    "/events?page=50",  # last page
    "/events?category=music",
    "/events?keyword=Event+99",
    "/events?date=2026-11-20",
]


@pytest.mark.parametrize("url", FIND_EVENTS)
def test_find_events_is_fast_with_1000_open_events(client, busy, url):
    assert slowest(client, url) < LIMIT


def test_my_activities_is_fast_with_1000_requests_and_a_long_history(client, services, busy):
    log_in(client, "organizer@bilgiedu.net")
    for event in list(services.events.events.values())[:500]:
        event.status = EventStatus.COMPLETED  # half of them are over: 500 rows in the history
    assert slowest(client, "/activities") < LIMIT


def test_event_requests_is_fast_with_1000_pending_requests(client, services, hall):
    services.events.auto_approve = False
    organizer = make_user(services, "organizer@bilgiedu.net")
    for i in range(EVENTS):
        services.events.create_event(organizer.id, f"Request {i}", "music", hall.id, hourly_slot(i), 10)
    make_user(services, "admin@bilgi.edu.tr", Role.ADMIN)
    log_in(client, "admin@bilgi.edu.tr")
    assert slowest(client, "/admin/requests") < LIMIT


def test_event_details_is_fast_with_50_participants(client, services, hall):
    organizer = make_user(services, "organizer@bilgiedu.net")
    event = services.events.create_event(organizer.id, "Big night", "music", hall.id, hourly_slot(0), 50)
    for i in range(49):
        services.events.join_event(event.id, make_user(services, f"p{i}@bilgiedu.net").id)
    log_in(client, "organizer@bilgiedu.net")
    assert slowest(client, f"/events/{event.id}") < LIMIT


# --------------------------------------------------------------------------- the real services (in memory)
@pytest.fixture
def real(app, email_sender):
    """The real services of create_app with 1,000 approved events in 10 halls, and a web client of a student.
    Skipped while EventService is still a skeleton (main before task 3.4 / #33)."""
    app.events.clock = lambda: NOW
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    admin = verified_user(app, email_sender, "admin@bilgi.edu.tr", Role.ADMIN)
    halls = [app.facilities.add_facility(staff.id, f"Hall {h}", 500) for h in range(10)]
    organizers = [verified_user(app, email_sender, f"organizer{h}@bilgiedu.net") for h in range(10)]
    try:
        for i in range(EVENTS):
            event = app.events.create_event(
                organizers[i % 10].id, f"Event {i}", ("music", "football", "board games")[i % 3],
                halls[i % 10].id, hourly_slot(i // 10), 10,
            )
            app.events.approve_event(event.id, admin.id)
    except NotImplementedError:
        pytest.skip("EventService is not implemented on this branch yet (task 3.4, #33)")
    assert len(app.events.search_events()) == EVENTS  # really 1,000 open events to search
    verified_user(app, email_sender, "student@bilgiedu.net")
    web = create_web_app(
        app, {"TESTING": True, "WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "test"}
    )
    client = web.test_client()
    client.post("/login", data={"email": "student@bilgiedu.net", "password": REAL_PASSWORD})
    return app, client


@pytest.mark.parametrize("url", FIND_EVENTS)
def test_find_events_with_the_real_services_is_fast(real, url):
    _, client = real
    assert slowest(client, url) < LIMIT


def test_find_events_with_the_real_services_shows_every_page(real):
    _, client = real
    assert b"Event 0" in client.get("/events").data  # soonest first
    last = client.get("/events?page=50").data
    assert b"Event 980" in last and b"Event 999" in last and b"Event 979" not in last  # page 50 = events 980-999


def test_my_activities_with_the_real_services_after_1000_events_ended(real):
    """The worst case of the history: the first visit after all 1,000 events ended. EventService completes
    them when a list is read (BR-11), so this one request also changes the status of 1,000 events."""
    app, client = real
    client.post("/events/1/join")
    app.events.clock = lambda: datetime(2027, 1, 1)
    assert slowest(client, "/activities") < LIMIT
    assert b"Event 0" in client.get("/activities").data  # the joined event is in the history
