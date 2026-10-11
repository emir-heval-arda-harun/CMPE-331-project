"""UC-04 Create match."""

import pytest

from campusevent.exceptions import ValidationError
from campusevent.models import MatchStatus, SkillLevel
from tests.helpers import football_pitch, slot, verified_user


def test_student_creates_match_and_joins_it_as_organizer(app, email_sender):
    organizer = verified_user(app, email_sender, "mert@bilgiedu.net")
    pitch = football_pitch(app, email_sender)

    match = app.matches.create_match(organizer.id, "football", pitch.id, slot(), 10, SkillLevel.INTERMEDIATE)

    assert match.status is MatchStatus.OPEN
    assert match.participant_ids == [organizer.id]
    assert match in app.matches.search_matches(sport="football")


def test_match_with_invalid_capacity_is_rejected(app, email_sender):
    organizer = verified_user(app, email_sender, "mert@bilgiedu.net")
    pitch = football_pitch(app, email_sender)

    with pytest.raises(ValidationError):
        app.matches.create_match(organizer.id, "football", pitch.id, slot(), 1, SkillLevel.BEGINNER)


def test_facility_must_support_the_sport(app, email_sender):
    organizer = verified_user(app, email_sender, "mert@bilgiedu.net")
    pitch = football_pitch(app, email_sender)

    with pytest.raises(ValidationError):
        app.matches.create_match(organizer.id, "tennis", pitch.id, slot(), 4, SkillLevel.BEGINNER)
