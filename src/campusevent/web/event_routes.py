"""UC-04 Create event, UC-05 Browse and filter, UC-06 Join, UC-09 Activity history,
UC-10 Leave, UC-11 Cancel, and the organizer's view of UC-12 (pending and rejected requests).

The templates only get view models (plain dicts) with names, never e-mail addresses (NFR-05).
"""

from __future__ import annotations

import math

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from campusevent import exceptions as exc
from campusevent.models import Event, EventStatus
from campusevent.web import common

bp = Blueprint("events", __name__)

STATUS_LABELS = {
    EventStatus.PENDING: "Waiting for approval",
    EventStatus.REJECTED: "Rejected",
    EventStatus.OPEN: "Open",
    EventStatus.FULL: "Full",
    EventStatus.COMPLETED: "Completed",
    EventStatus.CANCELLED: "Cancelled",
}


def _status_label(status) -> str:
    """Label of an event status. A status this page does not know yet is shown with its own name
    instead of breaking the page."""
    return STATUS_LABELS.get(status) or str(getattr(status, "value", status)).replace("_", " ").capitalize()


EVENT_CATEGORIES = common.EVENT_CATEGORIES
CATEGORY_SHORTCUTS = 8  # how many categories are shown as one-click filters on Find Events
PAGE_SIZE = 20  # events per page on Find Events (design report, NFR-02)


class _Names:
    """Looks up facility and user names once per request."""

    def __init__(self) -> None:
        services = common.services()
        self._users = services.auth
        self.facilities = {f.id: f for f in services.facilities.list_facilities()}
        self._user_names: dict[int, str] = {}

    def facility(self, facility_id: int) -> str:
        facility = self.facilities.get(facility_id)
        return facility.name if facility else "Unknown facility"

    def user(self, user_id: int) -> str:
        if user_id not in self._user_names:
            try:
                self._user_names[user_id] = self._users.get_user(user_id).full_name
            except exc.NotFoundError:
                self._user_names[user_id] = "Unknown user"
        return self._user_names[user_id]


def _event_view(event: Event, names: _Names, viewer_id: int) -> dict:
    joined = viewer_id in event.participant_ids
    is_organizer = viewer_id == event.organizer_id
    active = event.status in (EventStatus.OPEN, EventStatus.FULL)
    pending = event.status == EventStatus.PENDING
    return {
        "id": event.id,
        "title": event.title,
        "category": event.category,
        "description": event.description,
        "status": str(getattr(event.status, "value", event.status)),
        "status_label": _status_label(event.status),
        "start": event.slot.start,
        "end": event.slot.end,
        "facility": names.facility(event.facility_id),
        "organizer": names.user(event.organizer_id),
        "count": len(event.participant_ids),
        "capacity": event.capacity,
        "participants": [
            {"name": names.user(uid), "role": "Organizer" if uid == event.organizer_id else "Participant"}
            for uid in event.participant_ids
        ],
        "can_join": event.status == EventStatus.OPEN and not joined,
        "can_leave": active and joined and not is_organizer,
        "can_cancel": (active or pending) and is_organizer,  # a pending request is withdrawn (UC-11)
        "active": active,
        "pending": pending,
        "rejected": event.status == EventStatus.REJECTED,
        "rejection_reason": event.rejection_reason,
        "is_organizer": is_organizer,
        "joined": joined,
        "facility_id": event.facility_id,
    }


def _visible_event(event_id: int, viewer_id: int) -> Event:
    """An event the viewer may open. Pending and rejected requests are not public (BR-15): only their
    organizer sees them; for everyone else they do not exist."""
    event = common.services().events.get_event(event_id)
    if event.status in (EventStatus.PENDING, EventStatus.REJECTED) and event.organizer_id != viewer_id:
        raise exc.NotFoundError()
    return event


def resubmit_args(view: dict) -> dict:
    """Form values for 'Submit a corrected request' after a rejection (UC-12 2a.4); date and time are
    left out on purpose, so the organizer picks a slot again."""
    return {
        "title": view["title"], "category": view["category"], "facility_id": view["facility_id"],
        "capacity": view["capacity"], "description": view["description"],
    }


def _page_number(text: str) -> int:
    return int(text) if text.isdigit() and int(text) > 0 else 1


@bp.get("/events")
@common.student_required
def find_events(user):
    category = request.args.get("category", "")
    keyword = request.args.get("keyword", "")
    day_text = request.args.get("date", "")
    error = None
    events: list[Event] = []
    try:
        day = common.parse_date(day_text)
        events = common.services().events.search_events(
            category=category.strip() or None, day=day, keyword=keyword.strip() or None, only_open=True
        )
    except exc.ValidationError as error_:
        error = common.message_for(error_)

    events = sorted(events, key=lambda e: e.slot.start)
    pages = max(1, math.ceil(len(events) / PAGE_SIZE))
    page = min(_page_number(request.args.get("page", "1")), pages)
    names = _Names()
    views = [_event_view(e, names, user.id) for e in events[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]]
    filters = {"keyword": keyword, "category": category, "date": day_text}
    return render_template(
        "events.html",
        events=views,
        total=len(events),
        page=page,
        pages=pages,
        filters=filters,
        active_filters={key: value for key, value in filters.items() if value},
        categories=EVENT_CATEGORIES,
        shortcuts=EVENT_CATEGORIES[:CATEGORY_SHORTCUTS],
        error=error,
    ), (400 if error else 200)


@bp.get("/events/<int:event_id>")
@common.student_required
def event_details(user, event_id: int):
    view = _event_view(_visible_event(event_id, user.id), _Names(), user.id)
    return render_template("event_details.html", event=view, resubmit=resubmit_args(view))


@bp.get("/events/<int:event_id>/calendar.ics")
@common.student_required
def event_calendar(user, event_id: int):
    """'Add to calendar': the event as an iCalendar file for Google Calendar, Outlook or Apple Calendar."""
    event = _visible_event(event_id, user.id)
    body = common.ics_for(
        event.id, event.title, _Names().facility(event.facility_id), event.slot.start, event.slot.end, event.description
    )
    return Response(
        body,
        mimetype="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="campusevent-{event.id}.ics"'},
    )


def _schedule_context(facility_text: str, date_text: str) -> dict:
    """Busy slots of a facility on a day and the free gaps between them (UC-07, UC-04 4a)."""
    try:
        day = common.parse_date(date_text)
        if facility_text and day:
            busy = sorted(common.services().facilities.get_schedule(int(facility_text), day), key=lambda s: s.start)
            return {"schedule": busy, "free": common.free_slots(busy, day)}
    except (exc.CampusEventError, ValueError):
        pass  # an invalid date or facility is reported when the form is submitted
    return {"schedule": None, "free": []}


def _render_create_form(user, form: dict, error: str | None = None, status: int = 200):
    """The create form with the facility list and, once a facility and a date are chosen, its schedule."""
    names = _Names()
    return (
        render_template(
            "event_new.html",
            facilities=list(names.facilities.values()),
            form=form,
            categories=EVENT_CATEGORIES,
            error=error,
            opens=common.DAY_OPENS,
            closes=common.DAY_CLOSES,
            **_schedule_context(form.get("facility_id", ""), form.get("date", "")),
        ),
        status,
    )


@bp.get("/events/schedule")
@common.student_required
def facility_schedule(user):
    """Only the schedule box of the Create Event page; the page reloads it when the facility or date changes."""
    return render_template(
        "_schedule.html",
        opens=common.DAY_OPENS,
        closes=common.DAY_CLOSES,
        **_schedule_context(request.args.get("facility_id", ""), request.args.get("date", "")),
    )


@bp.route("/events/new", methods=["GET", "POST"])
@common.student_required
def create_event(user):
    if request.method == "GET":
        return _render_create_form(user, request.args.to_dict())

    form = request.form.to_dict()
    try:
        slot = common.parse_slot(form.get("date", ""), form.get("start", ""), form.get("end", ""))
        event = common.services().events.create_event(
            organizer_id=user.id,
            title=form.get("title", ""),
            category=form.get("category", ""),
            facility_id=common.parse_int(form.get("facility_id", ""), "Facility"),
            slot=slot,
            capacity=common.parse_int(form.get("capacity", ""), "Participants"),
            description=form.get("description", ""),
        )
    except exc.CampusEventError as error:
        return _render_create_form(user, form, common.message_for(error), common.status_for(error))
    if event.status == EventStatus.PENDING:
        flash("Your request is sent. An admin reviews it before the event is listed; you get an e-mail "
              "with the decision.", "success")
    else:
        flash("Your event is created.", "success")
    return redirect(url_for("events.event_details", event_id=event.id))


@bp.post("/events/<int:event_id>/join")
@common.student_required
def join_event(user, event_id: int):
    _visible_event(event_id, user.id)  # someone else's pending request does not exist for this user
    common.services().events.join_event(event_id, user.id)
    flash("You joined the event.", "success")
    return redirect(url_for("events.event_details", event_id=event_id))


@bp.post("/events/<int:event_id>/leave")
@common.student_required
def leave_event(user, event_id: int):
    _visible_event(event_id, user.id)
    common.services().events.leave_event(event_id, user.id)
    flash("You left the event.", "success")
    return redirect(url_for("events.event_details", event_id=event_id))


@bp.post("/events/<int:event_id>/cancel")
@common.student_required
def cancel_event(user, event_id: int):
    was_pending = _visible_event(event_id, user.id).status == EventStatus.PENDING
    common.services().events.cancel_event(event_id, user.id)
    if was_pending:
        flash("Your request is withdrawn and the facility slot is free again.", "success")
    else:
        flash("The event is cancelled and the facility slot is free again.", "success")
    return redirect(url_for("events.my_activities"))


@bp.get("/activities")
@common.student_required
def my_activities(user):
    records = common.services().events.get_activity_history(user.id)
    names = _Names()
    rows = [
        {"event_id": r.event_id, "title": r.title, "category": r.category, "start": r.slot.start,
         "end": r.slot.end, "facility": names.facility(r.facility_id)}
        for r in sorted(records, key=lambda r: r.slot.start, reverse=True)
    ]
    # UC-12 organizer view: every own event in any status. Completed ones are already in the history above.
    own = [e for e in common.services().events.list_my_requests(user.id) if e.status != EventStatus.COMPLETED]
    order = {EventStatus.PENDING: 0, EventStatus.REJECTED: 1, EventStatus.OPEN: 2, EventStatus.FULL: 2}
    requests = [
        _event_view(e, names, user.id) for e in sorted(own, key=lambda e: (order.get(e.status, 3), e.slot.start))
    ]
    for view in requests:
        view["resubmit"] = resubmit_args(view)
    return render_template("activities.html", rows=rows, requests=requests)
