"""UC-04 Create event, UC-05 Browse and filter, UC-06 Join, UC-09 Activity history,
UC-10 Leave, UC-11 Cancel.

The templates only get view models (plain dicts) with names, never e-mail addresses (NFR-05).
"""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from campusevent import exceptions as exc
from campusevent.models import Event, EventStatus
from campusevent.web import common

bp = Blueprint("events", __name__)

STATUS_LABELS = {
    EventStatus.OPEN: "Open",
    EventStatus.FULL: "Full",
    EventStatus.COMPLETED: "Completed",
    EventStatus.CANCELLED: "Cancelled",
}


# Suggestions for the category field. The category itself stays free text (charter, BR-14);
# "Other" lets a student type any category that is not in this list.
EVENT_CATEGORIES = [
    "Football", "Basketball", "Volleyball", "Billiards", "Tennis", "Table tennis", "Badminton",
    "Swimming", "Running", "Chess", "Board games", "Video games", "Study group", "Workshop", "Club meeting",
]


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
    return {
        "id": event.id,
        "title": event.title,
        "category": event.category,
        "description": event.description,
        "status": event.status.value,
        "status_label": STATUS_LABELS[event.status],
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
        "can_cancel": active and is_organizer,
        "joined": joined,
    }


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

    names = _Names()
    views = [_event_view(e, names, user.id) for e in sorted(events, key=lambda e: e.slot.start)]
    return render_template(
        "events.html",
        events=views,
        filters={"keyword": keyword, "category": category, "date": day_text},
        categories=EVENT_CATEGORIES,
        error=error,
    ), (400 if error else 200)


@bp.get("/events/<int:event_id>")
@common.student_required
def event_details(user, event_id: int):
    event = common.services().events.get_event(event_id)
    return render_template("event_details.html", event=_event_view(event, _Names(), user.id))


def _render_create_form(user, form: dict, error: str | None = None, status: int = 200):
    """The create form with the facility list and, once a facility and a date are chosen, its schedule."""
    names = _Names()
    schedule = None
    facility_id = form.get("facility_id", "")
    try:
        day = common.parse_date(form.get("date", ""))
        if facility_id and day:
            schedule = sorted(common.services().facilities.get_schedule(int(facility_id), day), key=lambda s: s.start)
    except (exc.CampusEventError, ValueError):
        schedule = None  # an invalid date or facility is reported when the form is submitted
    return (
        render_template(
            "event_new.html",
            facilities=list(names.facilities.values()),
            form=form,
            schedule=schedule,
            categories=EVENT_CATEGORIES,
            error=error,
        ),
        status,
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
    flash("Your event is created.", "success")
    return redirect(url_for("events.event_details", event_id=event.id))


@bp.post("/events/<int:event_id>/join")
@common.student_required
def join_event(user, event_id: int):
    common.services().events.join_event(event_id, user.id)
    flash("You joined the event.", "success")
    return redirect(url_for("events.event_details", event_id=event_id))


@bp.post("/events/<int:event_id>/leave")
@common.student_required
def leave_event(user, event_id: int):
    common.services().events.leave_event(event_id, user.id)
    flash("You left the event.", "success")
    return redirect(url_for("events.event_details", event_id=event_id))


@bp.post("/events/<int:event_id>/cancel")
@common.student_required
def cancel_event(user, event_id: int):
    common.services().events.cancel_event(event_id, user.id)
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
    return render_template("activities.html", rows=rows)
