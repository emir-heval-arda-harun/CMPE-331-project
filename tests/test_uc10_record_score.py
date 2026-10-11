"""UC-10 Record score and advance winning team."""

import pytest

from campusevent.exceptions import PermissionDeniedError, ValidationError
from campusevent.models import Role
from tests.helpers import verified_user


def _bracket(app, email_sender):
    rep = verified_user(app, email_sender, "club@bilgiedu.net", Role.CLUB_REPRESENTATIVE)
    tournament = app.tournaments.create_tournament(rep.id, "Spring Cup", "football", ["A", "B", "C", "D"])
    return rep, tournament, app.tournaments.generate_bracket(tournament.id)


def test_winner_advances_to_next_round(app, email_sender):
    rep, tournament, bracket = _bracket(app, email_sender)
    semi_1, semi_2 = [m for m in bracket if m.round_number == 1]

    app.tournaments.record_score(rep.id, semi_1.id, 3, 1)
    app.tournaments.record_score(rep.id, semi_2.id, 0, 2)

    final = [m for m in app.tournaments.get_tournament(tournament.id).bracket if m.round_number == 2][0]
    assert {final.team_a, final.team_b} == {semi_1.team_a, semi_2.team_b}


def test_final_result_sets_champion(app, email_sender):
    rep, tournament, bracket = _bracket(app, email_sender)
    semi_1, semi_2 = [m for m in bracket if m.round_number == 1]
    app.tournaments.record_score(rep.id, semi_1.id, 3, 1)
    app.tournaments.record_score(rep.id, semi_2.id, 2, 0)
    final = [m for m in app.tournaments.get_tournament(tournament.id).bracket if m.round_number == 2][0]

    app.tournaments.record_score(rep.id, final.id, 1, 0)

    assert app.tournaments.get_tournament(tournament.id).champion == final.team_a


def test_draw_is_not_allowed_in_elimination(app, email_sender):
    rep, tournament, bracket = _bracket(app, email_sender)

    with pytest.raises(ValidationError):
        app.tournaments.record_score(rep.id, bracket[0].id, 1, 1)


def test_only_organizer_can_record_scores(app, email_sender):
    rep, tournament, bracket = _bracket(app, email_sender)
    student = verified_user(app, email_sender, "student@bilgiedu.net")

    with pytest.raises(PermissionDeniedError):
        app.tournaments.record_score(student.id, bracket[0].id, 2, 0)
