"""UC-06 Join match."""

import pytest

from campusevent.exceptions import AlreadyJoinedError, MatchFullError
from campusevent.models import MatchStatus
from tests.helpers import open_match, verified_user


def test_student_joins_open_match(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    player = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=4)

    joined = app.matches.join_match(match.id, player.id)

    assert player.id in joined.participant_ids


def test_match_becomes_full_and_rejects_new_players(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    player = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    late = verified_user(app, email_sender, "kerem@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=2)

    assert app.matches.join_match(match.id, player.id).status is MatchStatus.FULL
    with pytest.raises(MatchFullError):
        app.matches.join_match(match.id, late.id)


def test_student_cannot_join_twice(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    player = verified_user(app, email_sender, "zeynep@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=4)
    app.matches.join_match(match.id, player.id)

    with pytest.raises(AlreadyJoinedError):
        app.matches.join_match(match.id, player.id)
