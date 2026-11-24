"""UC-06 Join event."""

import pytest

from campusevent.exceptions import AlreadyJoinedError, EventFullError
from campusevent.models import EventStatus
from tests.helpers import open_event, verified_user


def test_student_joins_open_event(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    guest = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=4)

    joined = app.events.join_event(event.id, guest.id)

    assert guest.id in joined.participant_ids


def test_event_becomes_full_and_rejects_new_participants(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    guest = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    late = verified_user(app, email_sender, "kerem@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=2)

    assert app.events.join_event(event.id, guest.id).status is EventStatus.FULL
    with pytest.raises(EventFullError):
        app.events.join_event(event.id, late.id)


def test_student_cannot_join_twice(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    guest = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=4)
    app.events.join_event(event.id, guest.id)

    with pytest.raises(AlreadyJoinedError):
        app.events.join_event(event.id, guest.id)
