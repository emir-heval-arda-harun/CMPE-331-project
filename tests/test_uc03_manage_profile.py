"""UC-03 Manage profile (preferred sports, skill levels, availability)."""

import pytest

from campusevent.exceptions import ValidationError
from campusevent.models import SkillLevel
from tests.helpers import slot, verified_user


def test_student_saves_sports_skill_levels_and_availability(app, email_sender):
    user = verified_user(app, email_sender, "deniz@bilgiedu.net")

    app.profiles.update_profile(
        user.id,
        sports={"football": SkillLevel.ADVANCED, "tennis": SkillLevel.BEGINNER},
        availability=[slot(day=3, hour=17, hours=2)],
    )

    profile = app.profiles.get_profile(user.id)
    assert profile.sports == {"football": SkillLevel.ADVANCED, "tennis": SkillLevel.BEGINNER}
    assert profile.availability == [slot(day=3, hour=17, hours=2)]


def test_profile_requires_at_least_one_sport(app, email_sender):
    user = verified_user(app, email_sender, "deniz@bilgiedu.net")

    with pytest.raises(ValidationError):
        app.profiles.update_profile(user.id, sports={}, availability=[])
