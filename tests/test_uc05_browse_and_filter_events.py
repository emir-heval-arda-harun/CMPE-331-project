"""UC-05 Browse and filter events by category, date and keyword."""

from tests.helpers import campus_hall, slot, verified_user


def _create_sample_events(app, email_sender):
    organizer = verified_user(app, email_sender, "selin@bilgiedu.net")
    hall = campus_hall(app, email_sender)
    study = app.events.create_event(organizer.id, "Calculus revision", "study group", hall.id, slot(day=2), 10)
    football = app.events.create_event(organizer.id, "Friday football", "football", hall.id, slot(day=4), 10)
    return study, football


def test_filter_by_category(app, email_sender):
    study, football = _create_sample_events(app, email_sender)

    assert app.events.search_events(category="study group") == [study]


def test_filter_by_date(app, email_sender):
    study, football = _create_sample_events(app, email_sender)

    assert app.events.search_events(day=football.slot.start.date()) == [football]


def test_filter_by_keyword_in_the_title(app, email_sender):
    study, football = _create_sample_events(app, email_sender)

    assert app.events.search_events(keyword="calculus") == [study]


def test_no_result_returns_empty_list(app, email_sender):
    _create_sample_events(app, email_sender)

    assert app.events.search_events(category="concert") == []
