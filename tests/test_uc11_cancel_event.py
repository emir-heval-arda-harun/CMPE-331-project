"""UC-11 Cancel event."""

import pytest

from campusevent.exceptions import PermissionDeniedError
from campusevent.models import EventStatus
from tests.helpers import open_event, verified_user


def test_organizer_cancels_event(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=4)

    cancelled = app.events.cancel_event(event.id, organizer.id)

    assert cancelled.status is EventStatus.CANCELLED
    assert event.id not in [e.id for e in app.events.search_events()]


def test_only_the_organizer_can_cancel(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    guest = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=4)
    app.events.join_event(event.id, guest.id)

    with pytest.raises(PermissionDeniedError):
        app.events.cancel_event(event.id, guest.id)


def test_cancelled_event_frees_the_facility_slot(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=4)
    app.events.cancel_event(event.id, organizer.id)

    again = app.events.create_event(organizer.id, "Retry", event.category, event.facility_id, event.slot, 4)

    assert again.status is EventStatus.OPEN
