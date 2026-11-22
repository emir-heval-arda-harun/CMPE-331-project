"""Unit tests of the EventService rules (task 3.4): UC-04, 05, 06, 09, 10, 11 and UC-12.

EventService is tested on its own: the user service and the facility service are small fakes, and the
events are kept in ``InMemoryEventRepository``. The clock is fixed, so the tests do not depend on today's date.
Rules: BR-04, BR-05, BR-07, BR-08, BR-11, BR-12, BR-13, BR-14, BR-15, BR-16, BR-17, BR-18.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from campusevent.events import EXPIRED_REASON, EventService
from campusevent.exceptions import (
    AlreadyJoinedError,
    EventFullError,
    FacilityConflictError,
    PermissionDeniedError,
    ValidationError,
)
from campusevent.models import EventStatus, Role

NOW = datetime(2026, 11, 1, 12, 0)  # fixed "current time"
ADMIN = 100
FACILITY_CAPACITY = 10


class FakeAuth:
    def __init__(self) -> None:
        self.roles = {i: Role.STUDENT for i in range(1, 8)}
        self.roles[ADMIN] = Role.ADMIN

    def require_role(self, user_id, role):
        if self.roles.get(user_id) != role:
            raise PermissionDeniedError("This action is not allowed for your role.")

    def get_user(self, user_id):
        return self.roles[user_id]


class FakeFacilities:
    """Same contract as FacilityService.check_bookable: capacity and slot checks against active events."""

    def __init__(self) -> None:
        self.events = None

    def check_bookable(self, facility_id, slot, capacity):
        if capacity > FACILITY_CAPACITY:
            raise ValidationError("The capacity is larger than the capacity of the facility.")
        if any(e.slot.overlaps(slot) for e in self.events.active_on(facility_id, slot.start.date())):
            raise FacilityConflictError("The facility is not available in this time slot.")


def slot(hour: int, day: int = 1):
    from campusevent.models import TimeSlot

    return TimeSlot(datetime(2026, 12, day, hour), datetime(2026, 12, day, hour + 1))


def make_service(**kwargs) -> EventService:
    return EventService(FakeAuth(), FakeFacilities(), clock=lambda: NOW, **kwargs)


def create(svc, organizer=1, title="Football", category="sports", hour=10, capacity=3, **kw):
    return svc.create_event(organizer, title, category, 1, slot(hour), capacity, **kw)


def open_event(svc, **kw):
    event = create(svc, **kw)
    return svc.approve_event(event.id, ADMIN)


# --------------------------------------------------------------------------- UC-04
def test_new_event_is_pending_and_organizer_is_first_participant():
    event = create(make_service())
    assert event.status == EventStatus.PENDING  # BR-15
    assert event.participant_ids == [1]  # BR-05


def test_capacity_below_two_is_rejected():
    for capacity in (1, 0, -3):
        with pytest.raises(ValidationError):
            create(make_service(), capacity=capacity)  # BR-04


def test_capacity_above_the_facility_capacity_is_rejected():
    with pytest.raises(ValidationError):
        create(make_service(), capacity=FACILITY_CAPACITY + 1)  # BR-04


def test_title_and_category_are_required_and_limited():
    svc = make_service()
    for bad in ({"title": "  "}, {"category": ""}, {"title": "x" * 121}, {"category": "y" * 61}):
        with pytest.raises(ValidationError):
            create(svc, **bad)


def test_category_is_stored_trimmed_and_lower_case():
    assert create(make_service(), category="  Board   GAMES ").category == "board games"  # BR-14
    assert create(make_service(), category="İlk Yardım", hour=12).category == "ilk yardım"  # Turkish İ


def test_pending_request_holds_the_slot_and_cancel_frees_it():
    svc = make_service()
    first = create(svc)
    with pytest.raises(FacilityConflictError):
        create(svc, organizer=2)  # BR-16
    svc.cancel_event(first.id, 1)
    assert create(svc, organizer=2).status == EventStatus.PENDING


# --------------------------------------------------------------------------- UC-05
def test_search_lists_only_open_events_and_filters_combine():
    svc = make_service()
    create(svc, title="Hidden pending", hour=9)  # pending: never listed (BR-15)
    a = open_event(svc, title="Football match", category="Sports", hour=10)
    b = open_event(svc, title="Chess night", category="board games", hour=12)
    assert [e.id for e in svc.search_events()] == [a.id, b.id]  # ordered by start time
    assert [e.id for e in svc.search_events(category=" SPORTS ")] == [a.id]  # BR-14
    assert [e.id for e in svc.search_events(keyword="CHESS")] == [b.id]
    assert [e.id for e in svc.search_events(day=date(2026, 12, 1), category="sports", keyword="foot")] == [a.id]
    assert svc.search_events(day=date(2026, 12, 2)) == []


def test_full_events_are_listed_only_when_asked():
    svc = make_service()
    event = open_event(svc, capacity=2)
    svc.join_event(event.id, 2)
    assert svc.search_events() == []
    assert [e.id for e in svc.search_events(only_open=False)] == [event.id]


# --------------------------------------------------------------------------- UC-06 / UC-10
def test_pending_event_cannot_be_joined():
    svc = make_service()
    with pytest.raises(ValidationError):
        svc.join_event(create(svc).id, 2)


def test_join_twice_is_rejected_and_capacity_is_never_exceeded():
    svc = make_service()
    event = open_event(svc, capacity=3)
    svc.join_event(event.id, 2)
    with pytest.raises(AlreadyJoinedError):
        svc.join_event(event.id, 2)  # UC-06 2a, BR-07
    svc.join_event(event.id, 3)
    with pytest.raises(EventFullError):
        svc.join_event(event.id, 4)  # UC-06 1b
    assert len(svc.events.get(event.id).participant_ids) == 3


def test_event_becomes_full_and_open_again_when_someone_leaves():
    svc = make_service()
    event = open_event(svc, capacity=2)
    assert svc.join_event(event.id, 2).status == EventStatus.FULL  # BR-08
    assert svc.leave_event(event.id, 2).status == EventStatus.OPEN  # BR-08
    assert svc.events.get(event.id).participant_ids == [1]


def test_organizer_cannot_leave_and_non_participant_cannot_leave():
    svc = make_service()
    event = open_event(svc)
    with pytest.raises(ValidationError):
        svc.leave_event(event.id, 1)  # BR-12
    with pytest.raises(ValidationError):
        svc.leave_event(event.id, 5)


def test_cannot_leave_or_cancel_after_the_start_time():
    svc = EventService(FakeAuth(), FakeFacilities(), clock=lambda: datetime(2026, 12, 1, 10, 30))
    event = svc.create_event(1, "Started", "x", 1, slot(10), 3)
    svc.approve_event(event.id, ADMIN)
    svc.join_event(event.id, 2)
    with pytest.raises(ValidationError):
        svc.leave_event(event.id, 2)
    with pytest.raises(ValidationError):
        svc.cancel_event(event.id, 1)


# --------------------------------------------------------------------------- UC-11
def test_only_the_organizer_can_cancel():
    svc = make_service()
    event = open_event(svc)
    with pytest.raises(PermissionDeniedError):
        svc.cancel_event(event.id, 2)  # BR-13, NFR-04
    assert svc.cancel_event(event.id, 1).status == EventStatus.CANCELLED


def test_cancelled_event_cannot_be_cancelled_again_and_frees_its_slot():
    svc = make_service()
    event = open_event(svc)
    svc.cancel_event(event.id, 1)
    with pytest.raises(ValidationError):
        svc.cancel_event(event.id, 1)
    assert open_event(svc, organizer=2).status == EventStatus.OPEN  # same slot is free again


# --------------------------------------------------------------------------- UC-09
def test_history_shows_completed_events_newest_first_and_never_cancelled_ones():
    svc = make_service()
    older = open_event(svc, hour=9, title="Older")
    newer = open_event(svc, hour=15, title="Newer")
    cancelled = open_event(svc, hour=18, title="Cancelled")
    upcoming = open_event(svc, hour=20, title="Still upcoming")
    svc.cancel_event(cancelled.id, 1)
    svc.complete_event(older.id)
    svc.complete_event(newer.id)
    history = svc.get_activity_history(1)
    assert [r.title for r in history] == ["Newer", "Older"]  # BR-11, BR-13
    assert upcoming.id not in [r.event_id for r in history]
    assert svc.get_activity_history(2) == []


# --------------------------------------------------------------------------- UC-12
def test_admin_approves_and_the_event_becomes_listed():
    svc = make_service()
    event = create(svc)
    assert [e.id for e in svc.list_pending_events(ADMIN)] == [event.id]
    approved = svc.approve_event(event.id, ADMIN)
    assert approved.status == EventStatus.OPEN and approved.reviewed_by == ADMIN and approved.reviewed_at == NOW
    assert [e.id for e in svc.search_events()] == [event.id]
    assert svc.list_pending_events(ADMIN) == []


def test_reject_needs_a_reason_frees_the_slot_and_keeps_the_reason():
    svc = make_service()
    event = create(svc)
    with pytest.raises(ValidationError):
        svc.reject_event(event.id, ADMIN, "   ")
    rejected = svc.reject_event(event.id, ADMIN, " Not suitable ")
    assert rejected.status == EventStatus.REJECTED and rejected.rejection_reason == "Not suitable"
    assert create(svc, organizer=2).status == EventStatus.PENDING  # slot is free again


def test_only_admins_review_and_only_pending_requests():
    svc = make_service()
    event = create(svc)
    with pytest.raises(PermissionDeniedError):
        svc.approve_event(event.id, 2)
    with pytest.raises(PermissionDeniedError):
        svc.list_pending_events(2)
    svc.approve_event(event.id, ADMIN)
    with pytest.raises(ValidationError):
        svc.reject_event(event.id, ADMIN, "too late")  # BR-17


def test_unreviewed_requests_are_rejected_at_their_start_time():
    svc = make_service()
    early = create(svc, hour=9)
    late = create(svc, hour=15)
    expired = svc.expire_pending_requests(datetime(2026, 12, 1, 10, 0))
    assert [e.id for e in expired] == [early.id]
    stored = svc.events.get(early.id)
    assert stored.status == EventStatus.REJECTED and stored.rejection_reason == EXPIRED_REASON  # BR-18
    assert stored.reviewed_by is None
    assert svc.events.get(late.id).status == EventStatus.PENDING


def test_organizer_sees_all_own_requests_in_any_status():
    svc = make_service()
    a = create(svc, hour=9)
    b = create(svc, hour=12)
    svc.reject_event(b.id, ADMIN, "no")
    create(svc, organizer=2, hour=15)
    assert [e.id for e in svc.list_my_requests(1)] == [b.id, a.id]


def test_decision_notification_is_sent_and_a_mail_error_does_not_undo_it():
    sent = []
    svc = make_service(notify_decision=lambda event, approved: sent.append((event.id, approved)))
    svc.approve_event(create(svc, hour=9).id, ADMIN)
    svc.reject_event(create(svc, hour=12).id, ADMIN, "no")
    assert sent == [(1, True), (2, False)]

    def broken(event, approved):
        raise RuntimeError("SMTP down")

    svc2 = make_service(notify_decision=broken)
    event = create(svc2)
    assert svc2.approve_event(event.id, ADMIN).status == EventStatus.OPEN
