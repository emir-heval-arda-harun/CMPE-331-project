"""Layer 1 (presentation): Flask application factory for the CampusEvent web UI."""

from __future__ import annotations

import os
import secrets

from flask import Flask, redirect, render_template, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

from campusevent.app import CampusEventApp, create_app
from campusevent.exceptions import CampusEventError
from campusevent.web import admin_routes, auth_routes, common, event_routes, profile_routes

csrf = CSRFProtect()

# A photo placed in static/img/ with one of these names is used as the background of the sign up and
# log in pages. Without a photo a drawn campus skyline is shown instead.
CAMPUS_PHOTO_NAMES = ("campus.jpg", "campus.jpeg", "campus.png", "campus.webp")


def _campus_photo_url(flask_app: Flask) -> str | None:
    for name in CAMPUS_PHOTO_NAMES:
        if os.path.isfile(os.path.join(flask_app.static_folder or "", "img", name)):
            return url_for("static", filename=f"img/{name}")
    return None


def create_web_app(services: CampusEventApp | None = None, config: dict | None = None) -> Flask:
    """Build the Flask app.

    ``services`` is the composition root of the application layer. Tests pass in-memory
    services; production uses ``campusevent.app.create_app``.
    """
    flask_app = Flask(__name__)
    flask_app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "1") == "1",
    )
    flask_app.config.update(config or {})
    if not os.environ.get("SECRET_KEY") and "SECRET_KEY" not in (config or {}):
        # Each process then signs sessions with its own random key: users are logged out after a restart,
        # and with several gunicorn workers a session made by one worker is refused by the others.
        flask_app.logger.warning(
            "SECRET_KEY is not set: using a random key for this process only. Sessions will not survive a "
            "restart and break with more than one worker. Set SECRET_KEY in the environment (see .env.example)."
        )
    flask_app.extensions["campusevent"] = services or create_app()
    csrf.init_app(flask_app)
    flask_app.jinja_env.filters["when"] = common.relative_day

    flask_app.register_blueprint(auth_routes.bp)
    flask_app.register_blueprint(profile_routes.bp)
    flask_app.register_blueprint(event_routes.bp)
    flask_app.register_blueprint(admin_routes.bp)

    @flask_app.get("/")
    def index():
        user = common.current_user()
        if user is None:
            return redirect(url_for("auth.login"))
        return redirect(common.home_url(user))

    @flask_app.get("/favicon.ico")
    def favicon():
        # Browsers ask for /favicon.ico even when the page links the SVG icon.
        return redirect(url_for("static", filename="favicon.svg"), code=301)

    @flask_app.context_processor
    def inject_user():
        return {"current_user": common.current_user(), "campus_photo": _campus_photo_url(flask_app)}

    @flask_app.errorhandler(CampusEventError)
    def handle_domain_error(error: CampusEventError):
        status = common.status_for(error)
        return render_template("error.html", message=common.message_for(error), status=status), status

    @flask_app.errorhandler(CSRFError)
    def handle_csrf_error(error: CSRFError):
        return render_template("error.html", message="Your form has expired. Please try again.", status=400), 400

    @flask_app.errorhandler(404)
    def handle_not_found(error):
        return render_template("error.html", message="This page does not exist.", status=404), 404

    @flask_app.errorhandler(500)
    def handle_unexpected(error):
        flask_app.logger.exception("Unexpected error")
        return render_template("error.html", message="Something went wrong. Please try again later.", status=500), 500

    return flask_app
