"""In-memory stand-ins for the application services, used to test the web UI before the real
services exist. They follow the planned service interface of the Software Design Report
(section 4.2) plus the three extra read methods the UI needs (see src/campusevent/web/README.md).
"""

from __future__ import annotations

from datetime import date, datetime

from campusevent import exceptions as exc
from campusevent.app import CampusEventApp
from campusevent.models import (
    ActivityRecord,
    Event,
    EventStatus,
    Facility,
    Profile,
    Role,
    TimeSlot,
    User,
)
from campusevent.notifications import InMemoryEmailSender

PASSWORD = "S3cure-pass!"


class FakeAuth:
    def __init__(self, domains, email_sender):
        self.domains = domains
        self.email_sender = email_sender
        self.users: dict[int, User] = {}
        self.passwords: dict[int, str] = {}
        self.tokens: dict[str, int] = {}

    def register(self, email, password, full_name, role=Role.STUDENT):
        if email.split("@")[-1].lower() not in self.domains:
            raise exc.InvalidEmailDomainError()
        if any(u.email.lower() == email.lower() for u in self.users.values()):
            raise exc.DuplicateEmailError()
        if not full_name.strip() or len(password) < 8:
            raise exc.ValidationError("Name and a password of at least 8 characters are required.")
        user = User(len(self.users) + 1, email, full_name, role)
        self.users[user.id] = user
        self.passwords[user.id] = password
        self.email_sender.send_verification_code(email, "123456")
        return user

    def _by_email(self, email):
        return next((u for u in self.users.values() if u.email.lower() == email.lower()), None)

    def verify_email(self, email, code):
        user = self._by_email(email)
        if user is None or code != self.email_sender.codes.get(email):
            raise exc.InvalidVerificationCodeError()
        user.is_verified = True
        return user

    def login(self, email, password):
        user = self._by_email(email)
        if user is None or self.passwords[user.id] != password:
            raise exc.AuthenticationError()
        if not user.is_verified:
            raise exc.EmailNotVerifiedError()
        token = f"token-{user.id}"
        self.tokens[token] = user.id
        return token

    def get_user_by_token(self, token):
        if token not in self.tokens:
            raise exc.AuthenticationError()
        return self.users[self.tokens[token]]

    def get_user(self, user_id):
        if user_id not in self.users:
            raise exc.NotFoundError()
        return self.users[user_id]

    def require_role(self, user_id, role):
        user = self.get_user(user_id)
        if user.role != role:
            raise exc.PermissionDeniedError()
        return user


class FakeProfiles:
    def __init__(self):
        self.profiles: dict[int, Profile] = {}

    def update_profile(self, user_id, interests, availability):
        cleaned = [i.strip().lower() for i in interests if i.strip()]
        if not cleaned:
            raise exc.ValidationError("Please add at least one interest.")
        self.profiles[user_id] = Profile(user_id, cleaned, list(availability))
        return self.profiles[user_id]

    def get_profile(self, user_id):
        return self.profiles.get(user_id, Profile(user_id))


class FakeFacilities:
    def __init__(self, auth, events_ref):
        self.auth = auth
        self.facilities: dict[int, Facility] = {}
        self.blocks: list[tuple[int, TimeSlot]] = []
        self._events = events_ref

    def add_facility(self, staff_id, name, capacity):
        self.auth.require_role(staff_id, Role.FACILITY_STAFF)
        facility = Facility(len(self.facilities) + 1, name, capacity)
        self.facilities[facility.id] = facility
        return facility

    def list_facilities(self):
        return list(self.facilities.values())

    def get_schedule(self, facility_id, day: date):
        busy = [s for f, s in self.blocks if f == facility_id and s.start.date() == day]
        for event in self._events().events.values():
            if (
                event.facility_id == facility_id
                and event.slot.start.date() == day
                and event.status in (EventStatus.OPEN, EventStatus.FULL)
            ):
                busy.append(event.slot)
        return busy

    def check_bookable(self, facility_id, slot, capacity):
        facility = self.facilities.get(facility_id)
        if facility is None:
            raise exc.NotFoundError()
        if capacity > facility.capacity:
            raise exc.ValidationError("The capacity is larger than the capacity of the facility.")
        if any(slot.overlaps(s) for s in self.get_schedule(facility_id, slot.start.date())):
            raise exc.FacilityConflictError()
        return facility


class FakeEvents:
    def __init__(self, auth, facilities):
        self.auth = auth
        self.facilities = facilities
        self.events: dict[int, Event] = {}

    def create_event(self, organizer_id, title, category, facility_id, slot, capacity, description=""):
        if not title.strip() or not category.strip():
            raise exc.ValidationError("Title and category are required.")
        if capacity < 2:
            raise exc.ValidationError("The capacity must be at least 2.")
        self.facilities.check_bookable(facility_id, slot, capacity)
        event = Event(
            len(self.events) + 1, organizer_id, title, category.strip().lower(), facility_id, slot,
            capacity, description, [organizer_id],
        )
        self.events[event.id] = event
        return event

    def get_event(self, event_id):
        if event_id not in self.events:
            raise exc.NotFoundError()
        return self.events[event_id]

    def search_events(self, category=None, day=None, keyword=None, only_open=True):
        result = []
        for event in self.events.values():
            if only_open and event.status != EventStatus.OPEN:
                continue
            if category and event.category != category.strip().lower():
                continue
            if day and event.slot.start.date() != day:
                continue
            if keyword and keyword.lower() not in (event.title + " " + event.description).lower():
                continue
            result.append(event)
        return result

    def _set_status(self, event):
        if event.status in (EventStatus.OPEN, EventStatus.FULL):
            event.status = EventStatus.FULL if len(event.participant_ids) >= event.capacity else EventStatus.OPEN

    def join_event(self, event_id, user_id):
        event = self.get_event(event_id)
        if user_id in event.participant_ids:
            raise exc.AlreadyJoinedError()
        if event.status == EventStatus.FULL:
            raise exc.EventFullError()
        if event.status != EventStatus.OPEN:
            raise exc.ValidationError("This event is not open.")
        event.participant_ids.append(user_id)
        self._set_status(event)
        return event

    def leave_event(self, event_id, user_id):
        event = self.get_event(event_id)
        if user_id == event.organizer_id:
            raise exc.ValidationError("The organizer cannot leave the event; cancel it instead.")
        if user_id not in event.participant_ids:
            raise exc.ValidationError("You are not a participant of this event.")
        event.participant_ids.remove(user_id)
        self._set_status(event)
        return event

    def cancel_event(self, event_id, user_id):
        event = self.get_event(event_id)
        if user_id != event.organizer_id:
            raise exc.PermissionDeniedError()
        event.status = EventStatus.CANCELLED
        return event

    def complete_event(self, event_id):
        event = self.get_event(event_id)
        event.status = EventStatus.COMPLETED
        return event

    def get_activity_history(self, user_id):
        return [
            ActivityRecord(e.id, e.title, e.category, e.slot, e.facility_id)
            for e in self.events.values()
            if e.status == EventStatus.COMPLETED and user_id in e.participant_ids
        ]


def make_fake_services(email_sender: InMemoryEmailSender | None = None) -> CampusEventApp:
    sender = email_sender or InMemoryEmailSender()
    auth = FakeAuth(("bilgiedu.net", "bilgi.edu.tr"), sender)
    holder: dict = {}
    facilities = FakeFacilities(auth, lambda: holder["events"])
    events = FakeEvents(auth, facilities)
    holder["events"] = events
    return CampusEventApp(auth=auth, profiles=FakeProfiles(), facilities=facilities, events=events)


def slot(day: int = 20, hour: int = 18, hours: int = 1) -> TimeSlot:
    from datetime import timedelta

    start = datetime(2026, 11, day, hour, 0)
    return TimeSlot(start, start + timedelta(hours=hours))
