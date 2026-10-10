"""UC-13 Track past activities."""

from tests.helpers import open_match, slot, verified_user


def test_completed_matches_appear_in_history(app, email_sender):
    organizer = verified_user(app, email_sender, "irem@bilgiedu.net")
    player = verified_user(app, email_sender, "omer@bilgiedu.net")
    match = open_match(app, email_sender, organizer, capacity=4)
    app.matches.join_match(match.id, player.id)

    app.matches.complete_match(match.id)

    history = app.matches.get_activity_history(player.id)
    assert [record.match_id for record in history] == [match.id]
    assert history[0].sport == "football"


def test_upcoming_matches_are_not_in_history(app, email_sender):
    organizer = verified_user(app, email_sender, "irem@bilgiedu.net")
    open_match(app, email_sender, organizer, capacity=4, when=slot(day=20))

    assert app.matches.get_activity_history(organizer.id) == []
