"""UC-05 Browse and filter matches by date, time, sport and skill level."""

from campusevent.models import SkillLevel
from tests.helpers import football_pitch, slot, verified_user


def _create_sample_matches(app, email_sender):
    organizer = verified_user(app, email_sender, "selin@bilgiedu.net")
    pitch = football_pitch(app, email_sender)
    beginner = app.matches.create_match(organizer.id, "football", pitch.id, slot(day=2), 10, SkillLevel.BEGINNER)
    advanced = app.matches.create_match(organizer.id, "football", pitch.id, slot(day=4), 10, SkillLevel.ADVANCED)
    return beginner, advanced


def test_filter_by_skill_level(app, email_sender):
    beginner, advanced = _create_sample_matches(app, email_sender)

    result = app.matches.search_matches(sport="football", skill_level=SkillLevel.BEGINNER)

    assert result == [beginner]


def test_filter_by_date(app, email_sender):
    beginner, advanced = _create_sample_matches(app, email_sender)

    result = app.matches.search_matches(day=advanced.slot.start.date())

    assert result == [advanced]


def test_no_result_returns_empty_list(app, email_sender):
    _create_sample_matches(app, email_sender)

    assert app.matches.search_matches(sport="basketball") == []
