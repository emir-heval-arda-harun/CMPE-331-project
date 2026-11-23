"""UC-03 Manage profile (interests and availability)."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from campusevent import exceptions as exc
from campusevent.web import common

bp = Blueprint("profile", __name__)

MAX_SLOT_ROWS = 50


def _interests_from_form() -> list[str]:
    # one interest per line; the service trims and normalizes (BR-14)
    return [line.strip() for line in request.form.get("interests", "").splitlines() if line.strip()]


def _slot_rows_from_form() -> list[dict]:
    days = request.form.getlist("slot_date")[:MAX_SLOT_ROWS]
    starts = request.form.getlist("slot_start")
    ends = request.form.getlist("slot_end")
    rows = []
    for index, day in enumerate(days):
        start = starts[index] if index < len(starts) else ""
        end = ends[index] if index < len(ends) else ""
        if day.strip() or start.strip() or end.strip():  # skip completely empty rows
            rows.append({"date": day, "start": start, "end": end})
    return rows


@bp.route("/profile", methods=["GET", "POST"])
@common.student_required
def my_profile(user):
    profiles = common.services().profiles
    if request.method != "POST":  # also HEAD: it must never run the form code (no CSRF check on HEAD)
        profile = profiles.get_profile(user.id)
        rows = [
            {"date": s.start.strftime("%Y-%m-%d"), "start": s.start.strftime("%H:%M"), "end": s.end.strftime("%H:%M")}
            for s in map(common.slot_to_campus, profile.availability)  # stored in UTC, shown in Istanbul time
        ]
        return render_template(
            "profile.html", interests="\n".join(profile.interests), rows=rows, categories=common.EVENT_CATEGORIES
        )

    interests = _interests_from_form()
    rows = _slot_rows_from_form()
    try:
        slots = [common.slot_to_utc(common.parse_slot(r["date"], r["start"], r["end"])) for r in rows]
        profiles.update_profile(user.id, interests, slots)
    except exc.CampusEventError as error:
        return render_template(
            "profile.html", interests="\n".join(interests), rows=rows, error=common.message_for(error),
            categories=common.EVENT_CATEGORIES,
        ), common.status_for(error)
    flash("Your profile is saved.", "success")
    return redirect(url_for("profile.my_profile"))
