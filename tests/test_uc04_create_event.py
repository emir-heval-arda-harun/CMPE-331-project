"""UC-04 Create event."""

import pytest

from campusevent.exceptions import ValidationError
from campusevent.models import EventStatus
from tests.helpers import campus_hall, slot, verified_user


def test_student_creates_event_and_joins_it_as_organizer(app, email_sender):
    organizer = verified_user(app, email_sender, "mert@bilgiedu.net")
    hall = campus_hall(app, email_sender)

    event = app.events.create_event(organizer.id, "Algorithms study group", "study group", hall.id, slot(), 8)

    assert event.status is EventStatus.OPEN
    assert event.participant_ids == [organizer.id]
    assert event in app.events.search_events(category="study group")


def test_any_free_text_category_is_accepted(app, email_sender):
    organizer = verified_user(app, email_sender, "mert@bilgiedu.net")
    hall = campus_hall(app, email_sender)

    for day, category in enumerate(["football", "photo walk", "chess club meeting"], start=2):
        event = app.events.create_event(organizer.id, f"{category} event", category, hall.id, slot(day=day), 6)
        assert event.category == category


def test_event_with_invalid_capacity_is_rejected(app, email_sender):
    organizer = verified_user(app, email_sender, "mert@bilgiedu.net")
    hall = campus_hall(app, email_sender)

    with pytest.raises(ValidationError):
        app.events.create_event(organizer.id, "Solo event", "other", hall.id, slot(), 1)


def test_capacity_cannot_exceed_the_facility_capacity(app, email_sender):
    organizer = verified_user(app, email_sender, "mert@bilgiedu.net")
    hall = campus_hall(app, email_sender, capacity=20)

    with pytest.raises(ValidationError):
        app.events.create_event(organizer.id, "Huge party", "social", hall.id, slot(), 21)
