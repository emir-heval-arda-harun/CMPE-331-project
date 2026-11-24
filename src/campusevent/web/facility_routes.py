"""UC-07 and UC-08: the Facility Management page of the facility staff (task 3.6).

One page, ``/facilities``: the facilities with their capacity, a form to add a facility, and the
schedule of one facility on one day with its blocks and bookings, a form to block a time and a
Remove button on each block (UC-08 alt. 2b, issue #19).

Times: the services keep naive UTC, staff see and type Istanbul time (``common.to_utc`` /
``common.slot_to_campus``). ``FacilityService`` works per UTC day, so the page asks for both UTC
days that an Istanbul day touches.
"""

from __future__ import annotations

from datetime import date
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for

from campusevent import exceptions as exc
from campusevent.models import EventStatus, Role, TimeSlot
from campusevent.web import common

bp = Blueprint("facilities", __name__)

NAME_MAX = 100  # same limits as FacilityService and the facility table
REASON_MAX = 200


def staff_required(view):
    """Logged in and facility staff; FacilityService checks the role again (NFR-04)."""

    @wraps(view)
    @common.login_required
    def wrapper(user, *args, **kwargs):
        if user.role != Role.FACILITY_STAFF:
            raise exc.PermissionDeniedError("Only facility staff can use this page.")
        return view(user, *args, **kwargs)

    return wrapper


def _day_schedule(facility_id: int, day: date) -> list[dict]:
    """Blocks (with reason) and event bookings of one Istanbul day, in Istanbul time, sorted."""
    facilities = common.services().facilities
    utc_start, utc_end = common.campus_day_in_utc(day)
    utc_days = (utc_start.date(), utc_end.date())
    whole_day = TimeSlot(utc_start, utc_end)

    # A block or event that crosses midnight UTC is returned for both UTC days: keep it once, by id.
    blocks = {b.id: b for d in utc_days for b in facilities.get_blocks(facility_id, d)}
    events = {e.id: e for d in utc_days for e in facilities.get_bookings(facility_id, d)}
    rows = []
    for block in blocks.values():
        if block.slot.overlaps(whole_day):
            local = common.slot_to_campus(block.slot)
            rows.append({"start": local.start, "end": local.end, "kind": "block", "id": block.id,
                         "label": block.reason, "note": ""})
    for event in events.values():
        if event.slot.overlaps(whole_day):
            local = common.slot_to_campus(event.slot)
            # Titles are public on Find Events; no organizer names or e-mail addresses here (NFR-05).
            note = "waiting for approval" if event.status == EventStatus.PENDING else ""
            rows.append({"start": local.start, "end": local.end, "kind": "event", "id": event.id,
                         "label": event.title, "note": note})
    return sorted(rows, key=lambda r: (r["start"], r["end"]))


def _render(user, facility_id: int | None = None, day: date | None = None, *, facility_form: dict | None = None,
            block_form: dict | None = None, facility_error: str | None = None, block_error: str | None = None,
            status: int = 200):
    facilities = common.services().facilities.list_facilities()
    selected = next((f for f in facilities if f.id == facility_id), None)
    if selected is None and facilities and facility_id is None:
        selected = facilities[0]
    day = day or common.campus_today()
    return render_template(
        "facilities.html",
        facilities=facilities,
        selected=selected,
        day=day,
        schedule=_day_schedule(selected.id, day) if selected else [],
        facility_form=facility_form or {},
        block_form=block_form or {"date": day.isoformat()},
        facility_error=facility_error,
        block_error=block_error,
        name_max=NAME_MAX,
        reason_max=REASON_MAX,
    ), status


@bp.get("/facilities")
@staff_required
def manage(user):
    facility_text = request.args.get("facility", "").strip()
    try:
        day = common.parse_date(request.args.get("date", ""))
        facility_id = common.parse_int(facility_text, "Facility") if facility_text else None
        if facility_id is not None:
            common.services().facilities.get_facility(facility_id)
    except exc.CampusEventError as error:
        return _render(user, block_error=common.message_for(error), status=common.status_for(error))
    return _render(user, facility_id, day)


@bp.post("/facilities")
@staff_required
def add_facility(user):
    form = {"name": request.form.get("name", ""), "capacity": request.form.get("capacity", "")}
    try:
        capacity = common.parse_int(form["capacity"], "Capacity")
        facility = common.services().facilities.add_facility(user.id, form["name"], capacity)
    except exc.CampusEventError as error:
        return _render(user, facility_form=form, facility_error=common.message_for(error),
                       status=common.status_for(error))
    flash(f'"{facility.name}" is added. Students can now book it.', "success")
    return redirect(url_for("facilities.manage", facility=facility.id))


@bp.post("/facilities/<int:facility_id>/blocks")
@staff_required
def add_block(user, facility_id: int):
    form = {key: request.form.get(key, "") for key in ("date", "start", "end", "reason")}
    day = None
    try:
        day = common.parse_date(form["date"])
        local = common.parse_slot(form["date"], form["start"], form["end"])
        common.services().facilities.add_block(user.id, facility_id, common.slot_to_utc(local), form["reason"])
    except exc.CampusEventError as error:
        if isinstance(error, exc.NotFoundError):
            raise
        # A conflict here means an event booking; the service's text says so, the generic one talks to students.
        message = str(error) if isinstance(error, exc.FacilityConflictError) else common.message_for(error)
        return _render(user, facility_id, day, block_form=form, block_error=message, status=common.status_for(error))
    flash(f"{local.start.strftime('%d %b %Y, %H:%M')} – {local.end.strftime('%H:%M')} is blocked. "
          "Students cannot book this time.", "success")
    return redirect(url_for("facilities.manage", facility=facility_id, date=form["date"].strip()))


@bp.post("/facilities/<int:facility_id>/blocks/<int:block_id>/remove")
@staff_required
def remove_block(user, facility_id: int, block_id: int):
    """UC-08 alt. 2b: remove a block that was added by mistake (issue #19)."""
    facilities = common.services().facilities
    if facilities.get_block(block_id).facility_id != facility_id:  # the address must match the block
        raise exc.NotFoundError()
    block = facilities.remove_block(user.id, block_id)
    local = common.slot_to_campus(block.slot)
    flash(f"The block {local.start.strftime('%d %b %Y, %H:%M')} – {local.end.strftime('%H:%M')} "
          f'("{block.reason}") is removed. Students can book this time again.', "success")
    return redirect(url_for("facilities.manage", facility=facility_id, date=local.start.date().isoformat()))
