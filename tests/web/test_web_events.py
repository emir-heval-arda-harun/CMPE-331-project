"""Web UI tests for UC-04 to UC-06 and UC-09 to UC-11."""

from campusevent.models import EventStatus
from tests.web.conftest import make_user
from tests.web.fakes import slot

CREATE_FORM = {
    "title": "Game night",
    "category": "Board Games",
    "description": "Bring your own games",
    "date": "2026-11-20",
    "start": "18:00",
    "end": "20:00",
    "capacity": "6",
}


def create(client, hall, **overrides):
    data = {**CREATE_FORM, "facility_id": str(hall.id), **overrides}
    return client.post("/events/new", data=data)


def organized_event(services, hall, organizer, **kwargs):
    return services.events.create_event(
        organizer.id, kwargs.get("title", "Game night"), kwargs.get("category", "board games"),
        hall.id, kwargs.get("slot", slot()), kwargs.get("capacity", 6),
    )


# UC-04 -------------------------------------------------------------------------------------------


def test_create_event_redirects_to_its_details_and_adds_the_organizer(client, student, hall, services):
    response = create(client, hall)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/events/1")
    event = services.events.get_event(1)
    assert event.participant_ids == [student.id]
    assert event.category == "board games"  # normalized by the service
    assert event.slot.start.hour == 15  # typed 18:00 Istanbul time, sent to the service as 15:00 UTC
    assert b"18:00" in client.get("/events/1").data  # and shown as 18:00 again


def test_create_form_lists_facilities_with_capacity(client, student, hall):
    response = client.get("/events/new")
    assert b"Santral Event Hall (capacity 50)" in response.data


def test_create_form_offers_ready_made_categories_and_an_other_option(client, student, hall):
    page = client.get("/events/new").data
    for name in (b"Football", b"Basketball", b"Volleyball", b"Billiards", b"Study group"):
        assert b'<option value="' + name + b'">' in page, name
    assert b'<option value="__other__">' in page
    assert b'name="category"' in page  # the text field is what the form sends, so a free text still works


def test_a_category_that_is_not_in_the_list_is_accepted(client, student, hall, services):
    create(client, hall, category="Frisbee")
    assert services.events.get_event(1).category == "frisbee"


def test_find_events_suggests_categories_in_the_filter(client, student):
    page = client.get("/events").data
    assert b'<datalist id="category-list">' in page
    assert b'<option value="Football">' in page


def test_create_event_on_busy_slot_shows_message_and_the_busy_times(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net")
    organized_event(services, hall, other)
    response = create(client, hall, start="18:30", end="19:30")
    assert response.status_code == 409
    assert b"This slot is busy" in response.data
    assert b"Busy: 18:00" in response.data  # the schedule helps to pick a free time
    assert b"Game night" in response.data  # the entered data is kept


def test_create_event_rejects_capacity_below_two_and_above_the_facility(client, student, hall):
    assert create(client, hall, capacity="1").status_code == 400
    too_big = create(client, hall, capacity="500")
    assert too_big.status_code == 400
    assert b"larger than the capacity of the facility" in too_big.data


def test_create_event_rejects_bad_times_and_numbers(client, student, hall):
    assert b"end time must be after" in create(client, hall, start="20:00", end="19:00").data
    assert b"valid date and time" in create(client, hall, date="not-a-date").data
    assert b"must be a whole number" in create(client, hall, capacity="many").data


def test_schedule_card_shows_free_facility(client, student, hall):
    response = client.get(f"/events/new?facility_id={hall.id}&date=2026-11-21")
    assert b"free all day" in response.data


# UC-05 -------------------------------------------------------------------------------------------


def test_find_events_lists_open_events_soonest_first(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net", name="Demo Organizer")
    organized_event(services, hall, other, title="Late one", slot=slot(day=22, hour=20))
    organized_event(services, hall, other, title="Early one", slot=slot(day=21, hour=9))
    page = client.get("/events").data.decode()
    assert page.index("Early one") < page.index("Late one")
    assert "organized by Demo Organizer" in page
    assert "Santral Event Hall" in page


def test_find_events_filters_by_keyword_category_and_date(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net")
    organized_event(services, hall, other, title="Football friendly", category="football", slot=slot(day=21))
    organized_event(services, hall, other, title="Chess club", category="chess", slot=slot(day=22))

    assert b"Chess club" not in client.get("/events?keyword=football").data
    assert b"Football friendly" not in client.get("/events?category=chess").data
    by_day = client.get("/events?date=2026-11-22").data
    assert b"Chess club" in by_day and b"Football friendly" not in by_day


def test_find_events_empty_result_offers_create_event(client, student):
    response = client.get("/events?keyword=nothing")
    assert b"No events match your search." in response.data
    assert b"Create an event" in response.data


def test_find_events_rejects_invalid_date(client, student):
    response = client.get("/events?date=31-31-2026")
    assert response.status_code == 400
    assert b"valid date" in response.data


def test_full_event_is_not_in_the_open_list(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net")
    event = organized_event(services, hall, other, capacity=2)
    services.events.join_event(event.id, make_user(services, "participant@bilgiedu.net").id)
    assert event.status == EventStatus.FULL
    assert b"Game night" not in client.get("/events").data


# UC-06 / UC-10 / UC-11 ----------------------------------------------------------------------------


def test_join_then_leave(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net")
    event = organized_event(services, hall, other)

    details = client.get(f"/events/{event.id}").data
    assert b"Join event" in details and b"Leave event" not in details and b"Cancel event" not in details

    joined = client.post(f"/events/{event.id}/join", follow_redirects=True)
    assert b"You joined the event." in joined.data
    assert student.id in event.participant_ids
    assert b"Leave event" in joined.data and b"Join event" not in joined.data

    left = client.post(f"/events/{event.id}/leave", follow_redirects=True)
    assert b"You left" in left.data and left.request.path == f"/events/{event.id}"  # from the details page
    assert student.id not in event.participant_ids


def test_join_twice_shows_clear_message(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net")
    event = organized_event(services, hall, other)
    client.post(f"/events/{event.id}/join")
    again = client.post(f"/events/{event.id}/join")
    assert again.status_code == 409
    assert b"already joined" in again.data


def test_join_full_event_shows_message(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net")
    event = organized_event(services, hall, other, capacity=2)
    services.events.join_event(event.id, make_user(services, "participant@bilgiedu.net").id)
    response = client.post(f"/events/{event.id}/join")
    assert response.status_code == 409
    assert b"This event is full." in response.data


def test_join_buttons_in_list_follow_the_rules(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net")
    event = organized_event(services, hall, other)
    assert f"/events/{event.id}/join".encode() in client.get("/events").data
    client.post(f"/events/{event.id}/join")
    assert b"You joined" in client.get("/events").data


def test_organizer_sees_cancel_but_not_leave_and_can_cancel(client, student, hall, services):
    create(client, hall)
    details = client.get("/events/1").data
    assert b"Cancel event" in details and b"Leave event" not in details
    assert b"cannot leave the event" in details

    cancelled = client.post("/events/1/cancel", follow_redirects=True)
    assert b"The event is cancelled" in cancelled.data
    assert services.events.get_event(1).status == EventStatus.CANCELLED
    after = client.get("/events/1").data
    assert b"Cancelled" in after and b"Join event" not in after


def test_only_the_organizer_can_cancel(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net")
    event = organized_event(services, hall, other)
    response = client.post(f"/events/{event.id}/cancel")
    assert response.status_code == 403
    assert event.status == EventStatus.OPEN


def test_event_details_never_show_email_addresses(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net", name="Demo Organizer")
    event = organized_event(services, hall, other)
    client.post(f"/events/{event.id}/join")
    page = client.get(f"/events/{event.id}").data
    assert b"Demo Organizer" in page and b"Test Student" in page
    assert b"@bilgiedu.net" not in page and b"@bilgi.edu.tr" not in page
    assert b"@bilgiedu.net" not in client.get("/events").data


def test_unknown_event_returns_404_page(client, student):
    response = client.get("/events/999")
    assert response.status_code == 404
    assert b"does not exist" in response.data


def test_text_in_events_is_escaped(client, student, hall):
    create(client, hall, title="<script>alert(1)</script>")
    page = client.get("/events/1").data
    assert b"<script>alert(1)</script>" not in page
    assert b"&lt;script&gt;" in page


# UC-09 -------------------------------------------------------------------------------------------


def test_activities_empty_state(client, student):
    assert b"No completed events yet." in client.get("/activities").data


def test_activities_list_completed_events_newest_first(client, student, hall, services):
    other = make_user(services, "organizer@bilgiedu.net")
    for day, title in ((10, "Older"), (12, "Newer")):
        event = organized_event(services, hall, other, title=title, slot=slot(day=day))
        services.events.join_event(event.id, student.id)
        services.events.complete_event(event.id)
    upcoming = organized_event(services, hall, other, title="Not done yet", slot=slot(day=25))
    services.events.join_event(upcoming.id, student.id)

    page = client.get("/activities").data.decode()
    assert page.index("Newer") < page.index("Older")
    assert "Not done yet" not in page
    assert "Santral Event Hall" in page


LONG_WORD = "Uzunisimliöğrencihesabı" * 4  # 92 letters without a space, within the 100 of a name


def test_long_words_without_spaces_break_instead_of_widening_the_page(client, student, hall, services):
    """NFR-01 (360 px): a name, title, category or link without spaces used to make the page wider than a phone
    (up to 4,267 px with a long rejection reason). The test client cannot measure a layout, so the widths were
    measured in the browser; this test keeps the two rules that fix it: long words may break anywhere, and the
    role next to a long name keeps its width instead of being squeezed letter by letter; buttons keep their
    labels whole."""
    organizer = make_user(services, "organizer@bilgiedu.net", name=LONG_WORD)
    event = organized_event(services, hall, organizer, title=LONG_WORD[:90])
    services.events.join_event(event.id, student.id)
    page = client.get(f"/events/{event.id}").data.decode()
    base_css = page.split("</style>")[0]  # the first style block of base.html
    assert "overflow-wrap: anywhere" in base_css and ".btn { overflow-wrap: normal; }" in base_css
    assert f'<span class="fw-medium" style="min-width: 0;">{LONG_WORD}</span>' in page
    assert '<span class="small text-muted ms-auto flex-shrink-0">Organizer</span>' in page
