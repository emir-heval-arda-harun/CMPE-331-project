"""UC-15 Cancel match."""

import pytest

from campusevent.exceptions import PermissionDeniedError
from campusevent.models import MatchStatus
from tests.helpers import open_match, slot, verified_user


def test_organizer_cancels_match(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=4)

    cancelled = app.matches.cancel_match(match.id, organizer.id)

    assert cancelled.status is MatchStatus.CANCELLED
    assert match.id not in [m.id for m in app.matches.search_matches(sport="football")]


def test_only_the_organizer_can_cancel(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    player = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=4)
    app.matches.join_match(match.id, player.id)

    with pytest.raises(PermissionDeniedError):
        app.matches.cancel_match(match.id, player.id)


def test_cancelled_match_frees_the_facility_slot(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=4)
    app.matches.cancel_match(match.id, organizer.id)

    again = app.matches.create_match(
        organizer.id, "football", match.facility_id, match.slot, 4, match.skill_level
    )

    assert again.status is MatchStatus.OPEN
