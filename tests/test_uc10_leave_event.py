"""UC-10 Leave event."""

import pytest

from campusevent.exceptions import NotFoundError, ValidationError
from campusevent.models import EventStatus
from tests.helpers import open_event, verified_user


def test_participant_leaves_event_and_frees_a_place(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    guest = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=4)
    app.events.join_event(event.id, guest.id)

    left = app.events.leave_event(event.id, guest.id)

    assert guest.id not in left.participant_ids


def test_full_event_becomes_open_again_when_a_participant_leaves(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    guest = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=2)
    assert app.events.join_event(event.id, guest.id).status is EventStatus.FULL

    assert app.events.leave_event(event.id, guest.id).status is EventStatus.OPEN


def test_user_who_did_not_join_cannot_leave(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    stranger = verified_user(app, email_sender, "kerem@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=4)

    with pytest.raises((NotFoundError, ValidationError)):
        app.events.leave_event(event.id, stranger.id)
