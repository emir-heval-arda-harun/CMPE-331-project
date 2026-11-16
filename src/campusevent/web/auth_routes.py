"""UC-01 Register and verify e-mail, UC-02 Log in."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from campusevent import exceptions as exc
from campusevent.models import Role
from campusevent.web import common

bp = Blueprint("auth", __name__)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", step="register")

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    try:
        common.services().auth.register(email, request.form.get("password", ""), full_name, Role.STUDENT)
    except exc.CampusEventError as error:
        return render_template(
            "signup.html", step="register", error=common.message_for(error), full_name=full_name, email=email
        ), common.status_for(error)
    return render_template("signup.html", step="verify", email=email)


@bp.get("/verify")
def verify_form():
    """Lets a user who closed the page enter the code later."""
    return render_template("signup.html", step="verify", email="")  # no e-mail in the URL (it would reach server logs)


@bp.post("/verify")
def verify():
    email = request.form.get("email", "").strip()
    try:
        common.services().auth.verify_email(email, request.form.get("code", "").strip())
    except exc.CampusEventError as error:
        return render_template("signup.html", step="verify", email=email, error=common.message_for(error)), (
            common.status_for(error)
        )
    flash("Your e-mail address is verified. You can log in now.", "success")
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    try:
        token = common.services().auth.login(email, request.form.get("password", ""))
        user = common.services().auth.get_user_by_token(token)
    except exc.EmailNotVerifiedError as error:
        return render_template("login.html", error=common.message_for(error), unverified_email=email), 401
    except exc.CampusEventError as error:
        # The same message for every other failure: it never says which part was wrong.
        return render_template("login.html", error=common.message_for(error)), common.status_for(error)

    session.clear()  # new session after login, so an old session id cannot be reused
    session[common.TOKEN_KEY] = token
    if user.role == Role.FACILITY_STAFF:
        return redirect("/facilities")
    return redirect(url_for("events.find_events"))


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
