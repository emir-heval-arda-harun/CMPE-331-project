"""UC-12 Review event requests: the admin's Event Requests page (change request CR-01).

Like the other pages, the template gets view models with names only, never e-mail addresses (NFR-05).
"""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from campusevent import exceptions as exc
from campusevent.web import common
from campusevent.web.event_routes import _Names

bp = Blueprint("admin", __name__)

REASON_MAX = 500  # characters; the organizer reads the reason on My Activities and in the e-mail


def _request_view(event, names: _Names) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "category": event.category,
        "description": event.description,
        "start": event.slot.start,
        "end": event.slot.end,
        "facility": names.facility(event.facility_id),
        "organizer": names.user(event.organizer_id),
        "capacity": event.capacity,
    }


def _render_requests(user, errors: dict | None = None, reasons: dict | None = None, status: int = 200):
    pending = common.services().events.list_pending_events(user.id)
    names = _Names()
    errors = errors or {}
    listed = {e.id for e in pending}
    return render_template(
        "admin_requests.html",
        requests=[_request_view(e, names) for e in sorted(pending, key=lambda e: e.slot.start)],
        errors=errors,
        # an error about a request that is no longer in the list (reviewed meanwhile, withdrawn, expired)
        general_errors=[message for event_id, message in errors.items() if event_id not in listed],
        reasons=reasons or {},
        reason_max=REASON_MAX,
    ), status


@bp.get("/admin/requests")
@common.admin_required
def event_requests(user):
    return _render_requests(user)


@bp.post("/admin/requests/<int:event_id>/approve")
@common.admin_required
def approve_request(user, event_id: int):
    try:
        event = common.services().events.approve_event(event_id, user.id)
    except exc.ValidationError as error:
        return _render_requests(user, {event_id: common.message_for(error)}, status=409)
    flash(f'"{event.title}" is approved. It is now listed and students can join it.', "success")
    return redirect(url_for("admin.event_requests"))


@bp.post("/admin/requests/<int:event_id>/reject")
@common.admin_required
def reject_request(user, event_id: int):
    reason = request.form.get("reason", "").strip()
    try:
        if len(reason) > REASON_MAX:
            raise exc.ValidationError(f"Please keep the reason under {REASON_MAX} characters.")
        event = common.services().events.reject_event(event_id, user.id, reason)
    except exc.ValidationError as error:
        status = 400 if not reason or len(reason) > REASON_MAX else 409
        return _render_requests(user, {event_id: common.message_for(error)}, {event_id: reason}, status)
    flash(f'"{event.title}" is rejected. The organizer gets the reason by e-mail.', "success")
    return redirect(url_for("admin.event_requests"))
