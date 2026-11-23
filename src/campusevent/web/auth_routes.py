"""UC-01 Register and verify e-mail, UC-02 Log in."""

from __future__ import annotations

import time

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from campusevent import exceptions as exc
from campusevent.models import Role
from campusevent.web import common

bp = Blueprint("auth", __name__)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method != "POST":  # also HEAD: it must never run the form code (no CSRF check on HEAD)
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


RESEND_WAIT = 60  # seconds between two "Send a new code" requests from one browser (against e-mail flooding)
RESEND_KEY = "resend_at"
RESEND_SENT = (
    "If this address belongs to an account that is not verified yet, a new code is on its way. "
    "Codes sent before no longer work."
)


@bp.post("/verify/resend")
def resend_code():
    """UC-01 5a, UC-02 3a: send a new verification code.

    The answer is the same for unknown, verified and unverified addresses (the service tells nothing either),
    so the page cannot be used to find out who has an account."""
    email = request.form.get("email", "").strip()
    if not email:
        return render_template(
            "signup.html", step="verify", email="", error="Please enter your university e-mail address."
        ), 400
    now = time.time()
    waited = now - float(session.get(RESEND_KEY, 0))
    if 0 <= waited < RESEND_WAIT:
        seconds = int(RESEND_WAIT - waited) + 1
        return render_template(
            "signup.html", step="verify", email=email,
            error=f"A code was sent a moment ago. You can ask for another one in {seconds} seconds.",
        ), 429
    try:
        common.services().auth.resend_code(email)
    except exc.CampusEventError as error:  # for example the mail server cannot be reached
        return render_template("signup.html", step="verify", email=email, error=common.message_for(error)), (
            common.status_for(error)
        )
    session[RESEND_KEY] = now
    return render_template("signup.html", step="verify", email=email, notice=RESEND_SENT)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method != "POST":  # also HEAD: it must never run the form code (no CSRF check on HEAD)
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
    return redirect(common.home_url(user))


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
