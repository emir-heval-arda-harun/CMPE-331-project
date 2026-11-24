"""UC-12 Review event requests (admin approves or rejects)."""

import pytest

from campusevent.exceptions import ValidationError
from campusevent.models import EventStatus
from tests.helpers import admin_user, campus_hall, slot, verified_user


def _request(app, email_sender, organizer, when=None):
    hall = campus_hall(app, email_sender)
    return app.events.create_event(organizer.id, "Game night", "board games", hall.id, when or slot(), 6)


def test_admin_sees_pending_requests(app, email_sender):
    organizer = verified_user(app, email_sender, "deniz@bilgiedu.net")
    admin = admin_user(app, email_sender)
    request = _request(app, email_sender, organizer)

    assert [e.id for e in app.events.list_pending_events(admin.id)] == [request.id]


def test_approved_request_becomes_open_and_listed(app, email_sender):
    organizer = verified_user(app, email_sender, "deniz@bilgiedu.net")
    admin = admin_user(app, email_sender)
    request = _request(app, email_sender, organizer)

    event = app.events.approve_event(request.id, admin.id)

    assert event.status is EventStatus.OPEN
    assert event.reviewed_by == admin.id
    assert [e.id for e in app.events.search_events(category="board games")] == [event.id]
    assert ("deniz@bilgiedu.net", "Game night", True, "") in email_sender.decisions


def test_rejected_request_frees_the_slot_and_tells_the_organizer_why(app, email_sender):
    organizer = verified_user(app, email_sender, "deniz@bilgiedu.net")
    admin = admin_user(app, email_sender)
    request = _request(app, email_sender, organizer)

    event = app.events.reject_event(request.id, admin.id, "Hall is reserved for exams that week")

    assert event.status is EventStatus.REJECTED
    assert event.rejection_reason == "Hall is reserved for exams that week"
    assert app.facilities.is_available(event.facility_id, event.slot) is True
    assert app.events.search_events() == []
    assert ("deniz@bilgiedu.net", "Game night", False, "Hall is reserved for exams that week") in email_sender.decisions


def test_rejection_needs_a_reason(app, email_sender):
    organizer = verified_user(app, email_sender, "deniz@bilgiedu.net")
    admin = admin_user(app, email_sender)
    request = _request(app, email_sender, organizer)

    with pytest.raises(ValidationError):
        app.events.reject_event(request.id, admin.id, "  ")


def test_only_pending_requests_can_be_reviewed(app, email_sender):
    organizer = verified_user(app, email_sender, "deniz@bilgiedu.net")
    admin = admin_user(app, email_sender)
    request = _request(app, email_sender, organizer)
    app.events.approve_event(request.id, admin.id)

    with pytest.raises(ValidationError):
        app.events.reject_event(request.id, admin.id, "Changed my mind")


def test_pending_request_holds_the_facility_slot(app, email_sender):
    organizer = verified_user(app, email_sender, "deniz@bilgiedu.net")
    request = _request(app, email_sender, organizer)

    assert app.facilities.is_available(request.facility_id, request.slot) is False


def test_pending_request_cannot_be_joined(app, email_sender):
    organizer = verified_user(app, email_sender, "deniz@bilgiedu.net")
    guest = verified_user(app, email_sender, "can@bilgiedu.net")
    request = _request(app, email_sender, organizer)

    with pytest.raises(ValidationError):
        app.events.join_event(request.id, guest.id)


def test_request_not_reviewed_before_start_expires(app, email_sender):
    organizer = verified_user(app, email_sender, "deniz@bilgiedu.net")
    request = _request(app, email_sender, organizer, when=slot(day=2, hour=18))

    expired = app.events.expire_pending_requests(now=request.slot.start)

    assert [e.id for e in expired] == [request.id]
    assert expired[0].status is EventStatus.REJECTED
    assert expired[0].reviewed_by is None
    assert app.facilities.is_available(request.facility_id, request.slot) is True


def test_organizer_follows_own_requests_in_every_status(app, email_sender):
    organizer = verified_user(app, email_sender, "deniz@bilgiedu.net")
    admin = admin_user(app, email_sender)
    hall = campus_hall(app, email_sender)
    first = app.events.create_event(organizer.id, "Chess", "chess", hall.id, slot(day=2), 4)
    second = app.events.create_event(organizer.id, "Poker", "card games", hall.id, slot(day=3), 4)
    app.events.reject_event(second.id, admin.id, "Gambling is not allowed on campus")

    statuses = {e.id: e.status for e in app.events.list_my_requests(organizer.id)}

    assert statuses == {first.id: EventStatus.PENDING, second.id: EventStatus.REJECTED}
