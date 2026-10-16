"""UC-07 View facility schedule and prevent booking conflicts."""

import pytest

from campusevent.exceptions import FacilityConflictError
from tests.helpers import campus_hall, slot, verified_user


def test_schedule_shows_existing_events(app, email_sender):
    organizer = verified_user(app, email_sender, "ece@bilgiedu.net")
    hall = campus_hall(app, email_sender)
    event = app.events.create_event(organizer.id, "Movie night", "social", hall.id, slot(hour=18), 10)

    assert event.slot in app.facilities.get_schedule(hall.id, event.slot.start.date())
    assert app.facilities.is_available(hall.id, slot(hour=18)) is False
    assert app.facilities.is_available(hall.id, slot(hour=20)) is True


def test_overlapping_event_in_same_facility_is_rejected(app, email_sender):
    organizer = verified_user(app, email_sender, "ece@bilgiedu.net")
    hall = campus_hall(app, email_sender)
    app.events.create_event(organizer.id, "Movie night", "social", hall.id, slot(hour=18, hours=2), 10)

    with pytest.raises(FacilityConflictError):
        app.events.create_event(organizer.id, "Quiz night", "social", hall.id, slot(hour=19), 10)
