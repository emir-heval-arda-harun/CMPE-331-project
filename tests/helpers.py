"""Shared setup steps. They are called inside test bodies (not fixtures) so that
a missing feature makes the test FAIL instead of ERROR."""

from datetime import datetime, timedelta

from campusevent.models import Role, TimeSlot

PASSWORD = "S3cure-pass!"


def slot(day: int = 2, hour: int = 18, hours: int = 1) -> TimeSlot:
    start = datetime(2026, 11, day, hour, 0)
    return TimeSlot(start, start + timedelta(hours=hours))


def verified_user(app, email_sender, email: str, role: Role = Role.STUDENT):
    app.auth.register(email, PASSWORD, email.split("@")[0].title(), role)
    return app.auth.verify_email(email, email_sender.codes[email])


def campus_hall(app, email_sender, capacity: int = 50):
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    return app.facilities.add_facility(staff.id, "Santral Event Hall", capacity)


def open_event(app, email_sender, organizer, capacity=10, when=None, category="board games", title="Game night"):
    hall = campus_hall(app, email_sender)
    return app.events.create_event(organizer.id, title, category, hall.id, when or slot(), capacity)
