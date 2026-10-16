"""UC-14 Leave match."""

import pytest

from campusevent.exceptions import NotFoundError, ValidationError
from campusevent.models import MatchStatus
from tests.helpers import open_match, verified_user


def test_participant_leaves_match_and_frees_a_place(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    player = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=4)
    app.matches.join_match(match.id, player.id)

    left = app.matches.leave_match(match.id, player.id)

    assert player.id not in left.participant_ids


def test_full_match_becomes_open_again_when_a_player_leaves(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    player = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=2)
    assert app.matches.join_match(match.id, player.id).status is MatchStatus.FULL

    assert app.matches.leave_match(match.id, player.id).status is MatchStatus.OPEN


def test_user_who_did_not_join_cannot_leave(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    stranger = verified_user(app, email_sender, "kerem@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=4)

    with pytest.raises((NotFoundError, ValidationError)):
        app.matches.leave_match(match.id, stranger.id)
