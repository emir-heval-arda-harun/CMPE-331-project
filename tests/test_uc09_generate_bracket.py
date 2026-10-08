"""UC-09 Generate tournament bracket automatically."""

from campusevent.models import Role
from tests.helpers import verified_user


def _tournament(app, email_sender, teams):
    rep = verified_user(app, email_sender, "club@bilgiedu.net", Role.CLUB_REPRESENTATIVE)
    return app.tournaments.create_tournament(rep.id, "Spring Cup", "football", teams)


def test_four_teams_produce_two_semi_finals_and_a_final(app, email_sender):
    tournament = _tournament(app, email_sender, ["A", "B", "C", "D"])

    bracket = app.tournaments.generate_bracket(tournament.id)

    first_round = [m for m in bracket if m.round_number == 1]
    assert len(first_round) == 2
    assert len([m for m in bracket if m.round_number == 2]) == 1
    assert sorted(t for m in first_round for t in (m.team_a, m.team_b)) == ["A", "B", "C", "D"]


def test_odd_number_of_teams_gets_a_bye(app, email_sender):
    tournament = _tournament(app, email_sender, ["A", "B", "C"])

    bracket = app.tournaments.generate_bracket(tournament.id)

    byes = [m for m in bracket if m.round_number == 1 and None in (m.team_a, m.team_b)]
    assert len(byes) == 1
    assert byes[0].winner is not None
