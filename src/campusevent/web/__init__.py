"""Layer 1 (presentation): Flask application factory for the CampusEvent web UI."""

from __future__ import annotations

import mimetypes
import os
import secrets

from flask import Flask, g, redirect, render_template, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

from campusevent.app import CampusEventApp, create_app_from_env
from campusevent.exceptions import CampusEventError
from campusevent.web import admin_routes, auth_routes, common, event_routes, facility_routes, profile_routes

csrf = CSRFProtect()

# A photo placed in static/img/ with one of these names is used as the background of the sign up and
# log in pages. Without a photo a drawn campus skyline is shown instead.
CAMPUS_PHOTO_NAMES = ("campus.jpg", "campus.jpeg", "campus.png", "campus.webp")

# Sent with every answer (NFR-03). A route that sets one of them itself keeps its own value.
SECURITY_HEADERS = {
    # After one visit over HTTPS the browser uses HTTPS only for a year, even if http:// is typed.
    # Browsers ignore it on plain HTTP, so the local demo is not affected.
    "Strict-Transport-Security": "max-age=31536000",
    # No other site may show our pages in a frame (clickjacking); frame-ancestors in CONTENT_SECURITY_POLICY is the
    # newer form of the same rule.
    "X-Frame-Options": "DENY",
    # The browser must not guess another type than the one the server sends.
    "X-Content-Type-Options": "nosniff",
    # Links to other sites do not tell them which of our pages the visitor came from (NFR-05).
    "Referrer-Policy": "same-origin",
}

# Content-Security-Policy (NFR-03): everything comes from our own site (Bootstrap and Inter too, since #44), and a
# script runs only if it is a file of ours or carries the nonce of this answer. Text a user typed can therefore never
# run as script, even if it reached a page unescaped. Styles may stay inline: the templates use style attributes,
# and CSS cannot run code. data: is for the small SVG pictures inside the CSS.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'self'; frame-ancestors 'none'"
)


def _campus_photo_url(flask_app: Flask) -> str | None:
    for name in CAMPUS_PHOTO_NAMES:
        if os.path.isfile(os.path.join(flask_app.static_folder or "", "img", name)):
            return url_for("static", filename=f"img/{name}")
    return None


def create_web_app(services: CampusEventApp | None = None, config: dict | None = None) -> Flask:
    """Build the Flask app.

    ``services`` is the composition root of the application layer. Tests pass in-memory
    services; production (``services`` left out) uses ``campusevent.app.create_app_from_env``, which
    reads DATABASE_URL, SECRET_KEY and SMTP_* from the environment.
    """
    # The Inter font in static/vendor: Flask takes the type of a static file from the system's list of file
    # types, and not every list has .woff2. Registering it sends the font as font/woff2 on every server.
    mimetypes.add_type("font/woff2", ".woff2")
    flask_app = Flask(__name__)
    flask_app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "1") == "1",
        # The largest form is Create Event; 1 MB is far more than any real text and stops huge posts (pentest P5).
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    flask_app.config.update(config or {})
    if not os.environ.get("SECRET_KEY") and "SECRET_KEY" not in (config or {}):
        # Each process then signs sessions with its own random key: users are logged out after a restart,
        # and with several gunicorn workers a session made by one worker is refused by the others.
        flask_app.logger.warning(
            "SECRET_KEY is not set: using a random key for this process only. Sessions will not survive a "
            "restart and break with more than one worker. Set SECRET_KEY in the environment (see .env.example)."
        )
    services = services or create_app_from_env()
    flask_app.extensions["campusevent"] = services

    @flask_app.teardown_appcontext
    def end_request(error):
        # One database session per request (Software Design Report 7.1): close it after every request.
        end = getattr(services, "end_request", None)  # the fakes of the web tests may not have it
        if end is not None:
            end()

    @flask_app.before_request
    def new_csp_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)  # a new one for every answer, so it cannot be guessed

    @flask_app.after_request
    def add_security_headers(response):
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        nonce = g.get("csp_nonce") or secrets.token_urlsafe(16)
        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY.format(nonce=nonce))
        return response

    csrf.init_app(flask_app)
    flask_app.jinja_env.filters["when"] = common.relative_day
    flask_app.jinja_env.filters["accent"] = common.accent

    flask_app.register_blueprint(auth_routes.bp)
    flask_app.register_blueprint(profile_routes.bp)
    flask_app.register_blueprint(event_routes.bp)
    flask_app.register_blueprint(admin_routes.bp)
    flask_app.register_blueprint(facility_routes.bp)

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
        return {
            "current_user": common.current_user(),
            "campus_photo": _campus_photo_url(flask_app),
            "csp_nonce": g.get("csp_nonce", ""),
        }

    @flask_app.errorhandler(CampusEventError)
    def handle_domain_error(error: CampusEventError):
        status = common.status_for(error)
        return render_template("error.html", message=common.message_for(error), status=status), status

    @flask_app.errorhandler(CSRFError)
    def handle_csrf_error(error: CSRFError):
        return render_template("error.html", message="Your form has expired. Please try again.", status=400), 400

    @flask_app.errorhandler(413)
    def handle_too_large(error):
        message = "This form is too large. Please shorten the text and try again."
        return render_template("error.html", message=message, status=413), 413

    @flask_app.errorhandler(404)
    def handle_not_found(error):
        return render_template("error.html", message="This page does not exist.", status=404), 404

    @flask_app.errorhandler(500)
    def handle_unexpected(error):
        flask_app.logger.exception("Unexpected error")
        return render_template("error.html", message="Something went wrong. Please try again later.", status=500), 500

    return flask_app
