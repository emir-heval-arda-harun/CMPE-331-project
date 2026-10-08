"""UC-12 Manage facility schedule (facility staff)."""

import pytest

from campusevent.exceptions import FacilityConflictError, PermissionDeniedError
from campusevent.models import Role, SkillLevel
from tests.helpers import slot, verified_user


def test_staff_blocks_facility_and_matches_cannot_use_it(app, email_sender):
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    student = verified_user(app, email_sender, "baris@bilgiedu.net")
    court = app.facilities.add_facility(staff.id, "Dorm Basketball Court", ["basketball"])

    app.facilities.add_block(staff.id, court.id, slot(hour=9, hours=3), "Physical education class")

    assert app.facilities.is_available(court.id, slot(hour=10)) is False
    with pytest.raises(FacilityConflictError):
        app.matches.create_match(student.id, "basketball", court.id, slot(hour=10), 6, SkillLevel.BEGINNER)


def test_student_cannot_manage_facilities(app, email_sender):
    student = verified_user(app, email_sender, "baris@bilgiedu.net")

    with pytest.raises(PermissionDeniedError):
        app.facilities.add_facility(student.id, "Fake Court", ["basketball"])
