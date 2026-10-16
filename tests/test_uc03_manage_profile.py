"""UC-03 Manage profile (interests and availability)."""

import pytest

from campusevent.exceptions import ValidationError
from tests.helpers import slot, verified_user


def test_student_saves_interests_and_availability(app, email_sender):
    user = verified_user(app, email_sender, "deniz@bilgiedu.net")

    app.profiles.update_profile(
        user.id,
        interests=["football", "board games"],
        availability=[slot(day=3, hour=17, hours=2)],
    )

    profile = app.profiles.get_profile(user.id)
    assert profile.interests == ["football", "board games"]
    assert profile.availability == [slot(day=3, hour=17, hours=2)]


def test_profile_requires_at_least_one_interest(app, email_sender):
    user = verified_user(app, email_sender, "deniz@bilgiedu.net")

    with pytest.raises(ValidationError):
        app.profiles.update_profile(user.id, interests=[], availability=[])
