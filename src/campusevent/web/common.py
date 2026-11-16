"""Helpers shared by all blueprints: current user, access decorators, input parsing, error messages."""

from __future__ import annotations

from datetime import date, datetime
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
