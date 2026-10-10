"""UC-11 View facility schedule and prevent booking conflicts."""

import pytest

from campusevent.exceptions import FacilityConflictError
from campusevent.models import SkillLevel
from tests.helpers import football_pitch, slot, verified_user


def test_schedule_shows_existing_matches(app, email_sender):
    organizer = verified_user(app, email_sender, "ece@bilgiedu.net")
    pitch = football_pitch(app, email_sender)
    match = app.matches.create_match(organizer.id, "football", pitch.id, slot(hour=18), 10, SkillLevel.BEGINNER)

    assert match.slot in app.facilities.get_schedule(pitch.id, match.slot.start.date())
    assert app.facilities.is_available(pitch.id, slot(hour=18)) is False
    assert app.facilities.is_available(pitch.id, slot(hour=20)) is True


def test_overlapping_match_on_same_facility_is_rejected(app, email_sender):
    organizer = verified_user(app, email_sender, "ece@bilgiedu.net")
    pitch = football_pitch(app, email_sender)
    app.matches.create_match(organizer.id, "football", pitch.id, slot(hour=18, hours=2), 10, SkillLevel.BEGINNER)

    with pytest.raises(FacilityConflictError):
        app.matches.create_match(organizer.id, "football", pitch.id, slot(hour=19), 10, SkillLevel.BEGINNER)
