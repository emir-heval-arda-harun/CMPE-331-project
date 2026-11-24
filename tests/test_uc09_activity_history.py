"""UC-09 Track past activities."""

from tests.helpers import open_event, slot, verified_user


def test_completed_events_appear_in_history(app, email_sender):
    organizer = verified_user(app, email_sender, "irem@bilgiedu.net")
    guest = verified_user(app, email_sender, "omer@bilgiedu.net")
    event = open_event(app, email_sender, organizer, capacity=4, category="football", title="Friday football")
    app.events.join_event(event.id, guest.id)

    app.events.complete_event(event.id)

    history = app.events.get_activity_history(guest.id)
    assert [record.event_id for record in history] == [event.id]
    assert history[0].category == "football"


def test_upcoming_events_are_not_in_history(app, email_sender):
    organizer = verified_user(app, email_sender, "irem@bilgiedu.net")
    open_event(app, email_sender, organizer, capacity=4, when=slot(day=20))

    assert app.events.get_activity_history(organizer.id) == []
