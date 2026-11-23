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
        "start": common.to_campus(event.slot.start),  # services keep UTC, pages show Istanbul time
        "end": common.to_campus(event.slot.end),
        "facility": names.facility(event.facility_id),
        "organizer": names.user(event.organizer_id),
        "capacity": event.capacity,
    }


def _render_requests(
    user, page_text: str, errors: dict | None = None, reasons: dict | None = None, status: int = 200
):
    pending = sorted(common.services().events.list_pending_events(user.id), key=lambda e: e.slot.start)
    shown, page, pages = common.paginate(pending, page_text)  # 20 per page (NFR-02)
    names = _Names()
    errors = errors or {}
    listed = {e.id for e in shown}
    return render_template(
        "admin_requests.html",
        requests=[_request_view(e, names) for e in shown],
        total=len(pending),
        page=page,
        pages=pages,
        errors=errors,
        # an error about a request that is not on this page (reviewed meanwhile, withdrawn, expired, or moved
        # to another page because a request before it was decided)
        general_errors=[message for event_id, message in errors.items() if event_id not in listed],
        reasons=reasons or {},
        reason_max=REASON_MAX,
    ), status


def _back_to_page() -> str:
    """After a decision the admin comes back to the page the form was on (the hidden field ``page``)."""
    page = common.page_number(request.form.get("page", ""))
    if page > 1:
        return url_for("admin.event_requests", page=page)  # a page after the last shows the last one
    return url_for("admin.event_requests")


@bp.get("/admin/requests")
@common.admin_required
def event_requests(user):
    return _render_requests(user, request.args.get("page", "1"))


@bp.post("/admin/requests/<int:event_id>/approve")
@common.admin_required
def approve_request(user, event_id: int):
    try:
        event = common.services().events.approve_event(event_id, user.id)
    except exc.ValidationError as error:
        page_text = request.form.get("page", "1")
        return _render_requests(user, page_text, {event_id: common.message_for(error)}, status=409)
    flash(f'"{event.title}" is approved. It is now listed and students can join it.', "success")
    return redirect(_back_to_page())


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
        page_text = request.form.get("page", "1")
        return _render_requests(user, page_text, {event_id: common.message_for(error)}, {event_id: reason}, status)
    flash(f'"{event.title}" is rejected. The organizer gets the reason by e-mail.', "success")
    return redirect(_back_to_page())
