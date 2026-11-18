"""Helpers shared by all blueprints: current user, access decorators, input parsing, error messages."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from functools import wraps

from flask import current_app, redirect, session, url_for

from campusevent import exceptions as exc
from campusevent.app import CampusEventApp
from campusevent.models import Role, TimeSlot, User

TOKEN_KEY = "token"


def services() -> CampusEventApp:
    return current_app.extensions["campusevent"]


def current_user() -> User | None:
    """The logged-in user, or None. A token the service no longer accepts is dropped."""
    token = session.get(TOKEN_KEY)
    if not token:
        return None
    try:
        return services().auth.get_user_by_token(token)
    except exc.CampusEventError:
        session.pop(TOKEN_KEY, None)
        return None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return redirect(url_for("auth.login"))
        return view(user, *args, **kwargs)

    return wrapper


def student_required(view):
    """Logged in and a student; the service layer checks roles again (NFR-04)."""

    @wraps(view)
    @login_required
    def wrapper(user, *args, **kwargs):
        if user.role != Role.STUDENT:
            raise exc.PermissionDeniedError("Only students can use this page.")
        return view(user, *args, **kwargs)

    return wrapper


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise exc.ValidationError("Please enter a valid date.") from None


def parse_slot(day: str, start: str, end: str) -> TimeSlot:
    """Combine a date and two times (HH:MM) into a TimeSlot."""
    try:
        start_dt = datetime.strptime(f"{day.strip()} {start.strip()}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{day.strip()} {end.strip()}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise exc.ValidationError("Please enter a valid date and time.") from None
    if end_dt <= start_dt:
        raise exc.ValidationError("The end time must be after the start time.")
    return TimeSlot(start_dt, end_dt)


def parse_int(value: str, label: str) -> int:
    try:
        return int((value or "").strip())
    except ValueError:
        raise exc.ValidationError(f"{label} must be a whole number.") from None


# Suggestions for categories (Create Event, Find Events, My Profile). The category itself stays free text
# (charter, BR-14); "Other" lets a student type any category that is not in this list.
EVENT_CATEGORIES = [
    "Football", "Basketball", "Volleyball", "Billiards", "Tennis", "Table tennis", "Badminton",
    "Swimming", "Running", "Chess", "Board games", "Video games", "Study group", "Workshop", "Club meeting",
]

# Time window used to suggest free slots on the Create Event page (UC-04 4a). The requirements do not
# define opening hours, so this is an assumption of the UI; see web/README.md.
DAY_OPENS = time(8, 0)
DAY_CLOSES = time(22, 0)


def free_slots(busy: list[TimeSlot], day: date, min_minutes: int = 60) -> list[TimeSlot]:
    """The gaps of at least ``min_minutes`` between the busy slots of a facility on one day."""
    opens, closes = datetime.combine(day, DAY_OPENS), datetime.combine(day, DAY_CLOSES)
    shortest = timedelta(minutes=min_minutes)
    cursor, gaps = opens, []
    for slot in sorted(busy, key=lambda s: s.start):
        if slot.end <= cursor:
            continue
        gap_end = min(slot.start, closes)
        if gap_end - cursor >= shortest:
            gaps.append(TimeSlot(cursor, gap_end))
        cursor = max(cursor, slot.end)
        if cursor >= closes:
            return gaps
    if closes - cursor >= shortest:
        gaps.append(TimeSlot(cursor, closes))
    return gaps


def relative_day(value: datetime, today: date | None = None) -> str:
    """'Today', 'Tomorrow', 'In 3 days', '2 days ago' ... used as a small label next to dates."""
    days = (value.date() - (today or date.today())).days
    if days == 0:
        return "Today"
    if days == 1:
        return "Tomorrow"
    if days == -1:
        return "Yesterday"
    return f"In {days} days" if days > 1 else f"{-days} days ago"


def _ics_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n")


def ics_for(uid: int, title: str, location: str, start: datetime, end: datetime, description: str = "") -> str:
    """A one-event iCalendar file (RFC 5545) that Google Calendar, Outlook and Apple Calendar can import.
    Times are written as local times without a time zone, the same way the pages show them."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CampusEvent//CMPE 331//EN", "BEGIN:VEVENT",
        f"UID:event-{uid}@campusevent", f"DTSTAMP:{stamp}",
        f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}", f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{_ics_text(title)}", f"LOCATION:{_ics_text(location)}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{_ics_text(description)}")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines) + "\r\n"


_MESSAGES = {
    exc.InvalidEmailDomainError: "Please use your university e-mail address.",
    exc.DuplicateEmailError: "An account with this e-mail address already exists.",
    exc.InvalidVerificationCodeError: "The code is wrong or has expired. Please request a new one.",
    exc.AuthenticationError: "Invalid e-mail or password.",
    exc.EmailNotVerifiedError: "Please verify your e-mail address before logging in.",
    exc.PermissionDeniedError: "You are not allowed to do this.",
    exc.NotFoundError: "This item does not exist.",
    exc.FacilityConflictError: "This slot is busy. Please choose another time or facility.",
    exc.EventFullError: "This event is full.",
    exc.AlreadyJoinedError: "You have already joined this event.",
}

_STATUS = {
    exc.PermissionDeniedError: 403,
    exc.NotFoundError: 404,
    exc.FacilityConflictError: 409,
    exc.EventFullError: 409,
    exc.AlreadyJoinedError: 409,
}


def message_for(error: exc.CampusEventError) -> str:
    """User message for a domain error. Validation errors keep the service's own text."""
    for error_type, message in _MESSAGES.items():
        if type(error) is error_type:
            return message
    return str(error) or "The data you entered is not valid."


def status_for(error: exc.CampusEventError) -> int:
    for error_type, status in _STATUS.items():
        if type(error) is error_type:
            return status
    if isinstance(error, (exc.AuthenticationError, exc.EmailNotVerifiedError)):
        return 401
    return 400
