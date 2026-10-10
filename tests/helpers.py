"""Shared setup steps. They are called inside test bodies (not fixtures) so that
a missing feature makes the test FAIL instead of ERROR."""

from datetime import datetime, timedelta

from campusevent.models import Role, SkillLevel, TimeSlot

PASSWORD = "S3cure-pass!"


def slot(day: int = 2, hour: int = 18, hours: int = 1) -> TimeSlot:
    start = datetime(2026, 11, day, hour, 0)
    return TimeSlot(start, start + timedelta(hours=hours))


def verified_user(app, email_sender, email: str, role: Role = Role.STUDENT):
    app.auth.register(email, PASSWORD, email.split("@")[0].title(), role)
    return app.auth.verify_email(email, email_sender.codes[email])


def football_pitch(app, email_sender):
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    return app.facilities.add_facility(staff.id, "Santral Football Pitch", ["football"])


def open_match(app, email_sender, organizer, capacity=10, skill=SkillLevel.INTERMEDIATE, when=None):
    pitch = football_pitch(app, email_sender)
    return app.matches.create_match(organizer.id, "football", pitch.id, when or slot(), capacity, skill)
