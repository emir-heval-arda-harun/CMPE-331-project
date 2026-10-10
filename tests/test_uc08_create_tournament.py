"""UC-08 Create tournament."""

import pytest

from campusevent.exceptions import PermissionDeniedError, ValidationError
from campusevent.models import Role
from tests.helpers import verified_user

TEAMS = ["Eagles", "Lions", "Wolves", "Sharks"]


def test_club_representative_creates_tournament(app, email_sender):
    rep = verified_user(app, email_sender, "club@bilgiedu.net", Role.CLUB_REPRESENTATIVE)

    tournament = app.tournaments.create_tournament(rep.id, "Spring Cup", "football", TEAMS)

    assert app.tournaments.get_tournament(tournament.id).teams == TEAMS


def test_regular_student_cannot_create_tournament(app, email_sender):
    student = verified_user(app, email_sender, "student@bilgiedu.net")

    with pytest.raises(PermissionDeniedError):
        app.tournaments.create_tournament(student.id, "Spring Cup", "football", TEAMS)


def test_tournament_needs_at_least_two_unique_teams(app, email_sender):
    rep = verified_user(app, email_sender, "club@bilgiedu.net", Role.CLUB_REPRESENTATIVE)

    with pytest.raises(ValidationError):
        app.tournaments.create_tournament(rep.id, "Spring Cup", "football", ["Eagles", "Eagles"])
