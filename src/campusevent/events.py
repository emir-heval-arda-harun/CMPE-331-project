"""UC-04 Create event, UC-05 Browse & filter, UC-06 Join event, UC-09 Activity history,
UC-10 Leave event, UC-11 Cancel event, UC-12 Review event requests.

Business rules used here:
- BR-04: capacity is at least 2 and at most the capacity of the facility.
- BR-05: the organizer is the first participant.
- BR-07: a student joins an event only once and participants never exceed the capacity.
- BR-08: an event is FULL when the capacity is reached and OPEN again when someone leaves.
- BR-11/BR-13: the history shows only completed events, newest first; cancelled ones never.
- BR-12: an organizer cannot leave their own event, they cancel it.
- BR-14: categories are free text, trimmed and compared without regard to case.
- BR-15: every new event starts as PENDING and is listed only after approval (UC-12).
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Callable

from campusevent.auth import AuthService
from campusevent.exceptions import AlreadyJoinedError, EventFullError, PermissionDeniedError, ValidationError
from campusevent.facilities import FacilityService
from campusevent.models import ActivityRecord, Event, EventStatus, Role, TimeSlot
from campusevent.repositories.event_repository import EventRepository, InMemoryEventRepository
from campusevent.repositories.unit_of_work import InMemoryUnitOfWork, UnitOfWork

MIN_CAPACITY = 2  # BR-04
EXPIRED_REASON = "Not reviewed before the start time"  # BR-18
log = logging.getLogger(__name__)
TITLE_MAX = 120  # event.title is VARCHAR(120)
CATEGORY_MAX = 60  # event.category is VARCHAR(60), like an interest


def _utc_now() -> datetime:
    """Naive UTC, like the expiry time of the verification codes."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _fold(text: str) -> str:
    """Trim, join inner spaces and ignore case (BR-14). Turkish capital İ becomes a plain i, as in profiles.py."""
    return " ".join((text or "").split()).replace("İ", "i").lower()


class EventService:
    def __init__(
        self,
        auth: AuthService,
        facilities: FacilityService,
        events: EventRepository | None = None,
        uow: UnitOfWork | None = None,
        clock: Callable[[], datetime] = _utc_now,
        notify_decision: Callable[[Event, bool], None] | None = None,
    ) -> None:
        self.auth = auth
        self.facilities = facilities
        self.events = events if events is not None else InMemoryEventRepository()
        self.uow = uow if uow is not None else InMemoryUnitOfWork()
        self.clock = clock
        # UC-12: called after an admin approved (True) or rejected (False) a request, to e-mail the organizer.
        # app.py connects it to the notification service; without it no e-mail is sent.
        self.notify_decision = notify_decision
        # FacilityService finds busy slots through the event repository (UC-07). If it was built
        # without one, give it ours, so a pending/open event really blocks its slot.
        if getattr(facilities, "events", None) is None:
            facilities.events = self.events

    # ------------------------------------------------------------------ #
    # UC-04 Create event
    # ------------------------------------------------------------------ #
    def create_event(
        self,
        organizer_id: int,
        title: str,
        category: str,
        facility_id: int,
        slot: TimeSlot,
        capacity: int,
        description: str = "",
    ) -> Event:
        """Create an event request with status PENDING. It holds the facility slot but is
        not listed until an admin approves it (UC-12)."""
        self.auth.require_role(organizer_id, Role.STUDENT)
        title = (title or "").strip()
        category = _fold(category)  # BR-14: stored trimmed and lower case (DB check ck_event_category_normalized)
        if not title or not category:  # UC-04 1a
            raise ValidationError("Please enter a title and a category.")
        if len(title) > TITLE_MAX:
            raise ValidationError(f"The title can be at most {TITLE_MAX} characters long.")
        if len(category) > CATEGORY_MAX:
            raise ValidationError(f"The category can be at most {CATEGORY_MAX} characters long.")
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < MIN_CAPACITY:
            raise ValidationError(f"The capacity must be a whole number of at least {MIN_CAPACITY}.")  # 3a, BR-04
        if slot.start <= self.clock():  # UC-04: an event request is for a future time
            raise ValidationError("The event must start in the future.")

        self.uow.begin()
        try:
            # Locks the facility, then checks the slot (4a), the facility capacity (3b) and conflicts (BR-06).
            self.facilities.check_bookable(facility_id, slot, capacity)
            event = self.events.add(
                Event(
                    id=0,
                    organizer_id=organizer_id,
                    title=title,
                    category=category,
                    facility_id=facility_id,
                    slot=slot,
                    capacity=capacity,
                    description=(description or "").strip(),
                    participant_ids=[organizer_id],  # BR-05
                    status=EventStatus.PENDING,  # BR-15
                )
            )
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return event

    # ------------------------------------------------------------------ #
    # UC-05 Browse and filter events
    # ------------------------------------------------------------------ #
    def search_events(
        self,
        category: str | None = None,
        day: date | None = None,
        keyword: str | None = None,
        only_open: bool = True,
    ) -> list[Event]:
        """Listed events ordered by start time. Pending, rejected, cancelled and completed events are
        never listed (BR-15). ``only_open=True`` shows OPEN events only; ``False`` also shows FULL ones.
        All given filters must match."""
        self._settle()
        statuses = (EventStatus.OPEN,) if only_open else (EventStatus.OPEN, EventStatus.FULL)
        now = self.clock()
        events = [e for e in self.events.list_by_status(statuses) if e.slot.start > now]  # UC-05: upcoming events
        if category is not None and _fold(category):
            wanted = _fold(category)
            events = [e for e in events if _fold(e.category) == wanted]  # BR-14
        if day is not None:
            events = [e for e in events if e.slot.start.date() == day]
        if keyword is not None and _fold(keyword):
            needle = _fold(keyword)
            events = [e for e in events if needle in _fold(e.title)]
        return sorted(events, key=lambda e: (e.slot.start, e.slot.end, e.id))

    # ------------------------------------------------------------------ #
    # UC-12 Review event requests (CR-01)
    # ------------------------------------------------------------------ #
    def list_pending_events(self, admin_id: int) -> list[Event]:
        """UC-12: all PENDING requests, oldest start time first. Admins only."""
        self.auth.require_role(admin_id, Role.ADMIN)
        self._settle()  # requests whose start time has passed are expired first (BR-18)
        events = self.events.list_by_status((EventStatus.PENDING,))
        return sorted(events, key=lambda e: (e.slot.start, e.slot.end, e.id))

    def approve_event(self, event_id: int, admin_id: int) -> Event:
        """UC-12: PENDING -> OPEN, the event becomes visible; the organizer is e-mailed."""
        self.auth.require_role(admin_id, Role.ADMIN)  # BR-17
        self.uow.begin()
        try:
            event = self.events.get_for_update(event_id)
            self._require_pending(event)  # 2b
            if event.slot.start <= self.clock():  # BR-18: a request not reviewed before its start expires
                raise ValidationError("This request has expired: its start time has passed.")
            event.status = EventStatus.OPEN
            event.reviewed_by = admin_id
            event.reviewed_at = self.clock()
            event.rejection_reason = ""
            self.events.save(event)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        self._notify(event, approved=True)
        return event

    def reject_event(self, event_id: int, admin_id: int, reason: str) -> Event:
        """UC-12: PENDING -> REJECTED with a reason; the facility slot is freed and the
        organizer is e-mailed. The organizer may submit a corrected request (UC-04)."""
        self.auth.require_role(admin_id, Role.ADMIN)  # BR-17
        reason = (reason or "").strip()
        if not reason:  # 2a1
            raise ValidationError("Please enter a reason for the rejection.")
        self.uow.begin()
        try:
            event = self.events.get_for_update(event_id)
            self._require_pending(event)  # 2b
            # REJECTED is not an active status, so the facility slot is free again (BR-16).
            event.status = EventStatus.REJECTED
            event.rejection_reason = reason
            event.reviewed_by = admin_id
            event.reviewed_at = self.clock()
            self.events.save(event)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        self._notify(event, approved=False)
        return event

    def expire_pending_requests(self, now: datetime) -> list[Event]:
        """UC-12: requests still PENDING at their start time become REJECTED automatically (BR-18)."""
        expired: list[Event] = []
        self.uow.begin()
        try:
            for candidate in self.events.list_by_status((EventStatus.PENDING,)):
                if candidate.slot.start > now:
                    continue
                event = self.events.get_for_update(candidate.id)
                if event.status != EventStatus.PENDING:
                    continue
                event.status = EventStatus.REJECTED
                event.rejection_reason = EXPIRED_REASON  # the database requires a reason (BR-17)
                event.reviewed_by = None  # no reviewer
                event.reviewed_at = now
                self.events.save(event)
                expired.append(event)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return expired

    def list_my_requests(self, organizer_id: int) -> list[Event]:
        """UC-12: every event the user organized, in any status, so the organizer can follow
        pending, approved and rejected requests. Newest start time first."""
        self.auth.get_user(organizer_id)
        self._settle()
        events = self.events.list_by_organizer(organizer_id)
        return sorted(events, key=lambda e: (e.slot.start, e.slot.end, e.id), reverse=True)

    @staticmethod
    def _require_pending(event: Event) -> None:
        if event.status != EventStatus.PENDING:
            raise ValidationError("This request is no longer pending.")

    def _notify(self, event: Event, approved: bool) -> None:
        """E-mail the decision after the commit. A mail error must not undo the decision."""
        if self.notify_decision is None:
            return
        try:
            self.notify_decision(event, approved)
        except Exception:
            log.exception("Could not send the decision e-mail for event %s", event.id)

    # ------------------------------------------------------------------ #
    # UC-06 Join event
    # ------------------------------------------------------------------ #
    def join_event(self, event_id: int, user_id: int) -> Event:
        self.auth.require_role(user_id, Role.STUDENT)
        self.uow.begin()
        try:
            event = self.events.get_for_update(event_id)  # lock: two students cannot take the last place
            if event.status not in (EventStatus.OPEN, EventStatus.FULL):  # 1a
                raise ValidationError("This event is not open for joining.")
            if event.slot.start <= self.clock():  # UC-06: only upcoming events can be joined
                raise ValidationError("This event has already started.")
            if user_id in event.participant_ids:  # 2a, BR-07
                raise AlreadyJoinedError("You have already joined this event.")
            if len(event.participant_ids) >= event.capacity:  # 1b
                raise EventFullError("This event is full.")
            event.participant_ids.append(user_id)
            if len(event.participant_ids) >= event.capacity:  # BR-08
                event.status = EventStatus.FULL
            self.events.save(event)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return event

    # ------------------------------------------------------------------ #
    # UC-10 Leave event
    # ------------------------------------------------------------------ #
    def leave_event(self, event_id: int, user_id: int) -> Event:
        self.auth.require_role(user_id, Role.STUDENT)
        self.uow.begin()
        try:
            event = self.events.get_for_update(event_id)
            if user_id not in event.participant_ids:  # 1a
                raise ValidationError("You are not a participant of this event.")
            if user_id == event.organizer_id:  # 1b, BR-12
                raise ValidationError("The organizer cannot leave the event. Cancel the event instead.")
            if event.status not in (EventStatus.OPEN, EventStatus.FULL) or event.slot.start <= self.clock():
                raise ValidationError("You can only leave an open event that has not started.")
            event.participant_ids.remove(user_id)
            if event.status == EventStatus.FULL:  # BR-08
                event.status = EventStatus.OPEN
            self.events.save(event)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return event

    # ------------------------------------------------------------------ #
    # UC-11 Cancel event
    # ------------------------------------------------------------------ #
    def cancel_event(self, event_id: int, user_id: int) -> Event:
        """UC-11: the organizer cancels an OPEN/FULL event or withdraws a PENDING request."""
        self.uow.begin()
        try:
            event = self.events.get_for_update(event_id)
            if event.organizer_id != user_id:  # 1a
                raise PermissionDeniedError("Only the organizer can cancel this event.")
            active = (EventStatus.PENDING, EventStatus.OPEN, EventStatus.FULL)
            if event.status not in active or event.slot.start <= self.clock():  # 1b
                raise ValidationError("This event can no longer be cancelled.")
            # CANCELLED is not an ACTIVE status, so the facility slot is free again (BR-16, UC-07).
            event.status = EventStatus.CANCELLED
            self.events.save(event)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return event

    def complete_event(self, event_id: int) -> Event:
        """OPEN/FULL -> COMPLETED once the event took place (called by the system, not by a user)."""
        self.uow.begin()
        try:
            event = self.events.get_for_update(event_id)
            if event.status not in (EventStatus.OPEN, EventStatus.FULL):
                raise ValidationError("Only an open or full event can be completed.")
            event.status = EventStatus.COMPLETED
            self.events.save(event)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return event

    def get_event(self, event_id: int) -> Event:
        """One event by id, in any status (Event Details and the join, leave and cancel pages).
        ``NotFoundError`` for an unknown id."""
        return self.events.get(event_id)

    def _settle(self) -> None:
        """Bring the statuses up to date with the clock before a list is read: requests still pending at their
        start time are rejected (BR-18), and open or full events that have ended become COMPLETED, so they
        appear in the activity history (UC-09, BR-11). There is no background job on the free hosting plan,
        so this runs when the lists are opened."""
        now = self.clock()
        self.expire_pending_requests(now)
        for event in self.events.list_by_status((EventStatus.OPEN, EventStatus.FULL)):
            if event.slot.end <= now:
                try:
                    self.complete_event(event.id)
                except ValidationError:  # completed or cancelled by another request in the meantime
                    pass

    # ------------------------------------------------------------------ #
    # UC-09 Track activity history
    # ------------------------------------------------------------------ #
    def get_activity_history(self, user_id: int) -> list[ActivityRecord]:
        """Completed events the user took part in, newest first (BR-11). Cancelled ones never appear (BR-13)."""
        self.auth.get_user(user_id)  # NotFoundError for an unknown user
        self._settle()
        events = [
            e for e in self.events.list_by_participant(user_id) if e.status == EventStatus.COMPLETED
        ]
        events.sort(key=lambda e: (e.slot.start, e.slot.end, e.id), reverse=True)
        return [
            ActivityRecord(event_id=e.id, title=e.title, category=e.category, slot=e.slot, facility_id=e.facility_id)
            for e in events
        ]
