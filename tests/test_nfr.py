"""Non-functional requirement tests (NFR-02 ... NFR-07).

NFR-01 (responsive UI), NFR-08 (single test command) and NFR-09 (browser
portability) cannot be checked by unit tests; see docs/requirements/README.md
for how they are verified.

Like the use case tests, these call the services inside the test body so that a
missing feature makes the test FAIL instead of ERROR.
"""

import time

import pytest

from campusevent import create_app
from campusevent.exceptions import PermissionDeniedError
from campusevent.models import Role, SkillLevel
from tests.helpers import PASSWORD, slot, verified_user

TEAMS = ["Eagles", "Lions", "Wolves", "Sharks"]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _leaves(obj, seen=None):
    """Yield every str/bytes value stored anywhere inside an object graph."""
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return
    seen.add(id(obj))
    if isinstance(obj, (str, bytes, bytearray)):
        yield obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield from _leaves(key, seen)
            yield from _leaves(value, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for value in obj:
            yield from _leaves(value, seen)
    elif hasattr(obj, "__dict__"):
        yield from _leaves(vars(obj), seen)


def _stored_text(app):
    """All text kept by the auth service (the e-mail sender is not part of the storage)."""
    storage = {k: v for k, v in vars(app.auth).items() if k != "email_sender"}
    for leaf in _leaves(storage):
        yield leaf.decode(errors="ignore") if isinstance(leaf, (bytes, bytearray)) else leaf


def _long_values(app, email_sender):
    """Stored values that are long enough to be a password hash or a salt."""
    codes = set(email_sender.codes.values())
    return {t for t in _stored_text(app) if len(t) >= 32 and t not in codes}


def _full_match(app, email_sender, emails):
    """A full football match; every player has a profile."""
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    pitch = app.facilities.add_facility(staff.id, "Santral Football Pitch", ["football"])
    players = [verified_user(app, email_sender, email) for email in emails]
    for player in players:
        app.profiles.update_profile(player.id, sports={"football": SkillLevel.INTERMEDIATE}, availability=[])
    match = app.matches.create_match(
        players[0].id, "football", pitch.id, slot(), len(players), SkillLevel.INTERMEDIATE
    )
    for player in players[1:]:
        app.matches.join_match(match.id, player.id)
    return match, players


class SlowClient:
    """Stands in for a slow Gemini Pro call."""

    def rate_players(self, sport, profiles):
        time.sleep(0.2)
        return {p.user_id: float(p.user_id % 10 + 1) for p in profiles}


class RecordingClient:
    """Remembers exactly what the application sends to the AI service."""

    def __init__(self):
        self.received = []

    def rate_players(self, sport, profiles):
        self.received.extend(profiles)
        return {p.user_id: 5.0 for p in profiles}


class TimeoutClient:
    def rate_players(self, sport, profiles):
        raise TimeoutError("AI service did not answer")


# --------------------------------------------------------------------------- #
# NFR-02 Performance: match search < 2 s for 1,000 open matches
# --------------------------------------------------------------------------- #
def test_nfr02_search_is_fast_with_1000_open_matches(app, email_sender):
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    for f in range(10):
        pitch = app.facilities.add_facility(staff.id, f"Pitch {f}", ["football"])
        organizer = verified_user(app, email_sender, f"organizer{f}@bilgiedu.net")
        for i in range(100):
            app.matches.create_match(
                organizer.id, "football", pitch.id, slot(day=1 + i // 24, hour=i % 24), 10, SkillLevel.INTERMEDIATE
            )

    started = time.perf_counter()
    result = app.matches.search_matches(sport="football", skill_level=SkillLevel.INTERMEDIATE)
    elapsed = time.perf_counter() - started

    assert len(result) == 1000
    assert elapsed < 2.0


# --------------------------------------------------------------------------- #
# NFR-03 Performance: team balancing < 10 s including the AI call
# --------------------------------------------------------------------------- #
def test_nfr03_team_balancing_finishes_within_10_seconds(email_sender):
    app = create_app(email_sender=email_sender, ai_client=SlowClient())
    match, players = _full_match(app, email_sender, [f"player{i}@bilgiedu.net" for i in range(20)])

    started = time.perf_counter()
    teams = app.matchmaking.balance_teams(match.id, team_count=2)
    elapsed = time.perf_counter() - started

    assert sorted(uid for team in teams for uid in team) == sorted(p.id for p in players)
    assert elapsed < 10.0


# --------------------------------------------------------------------------- #
# NFR-04 Security: passwords are stored only as salted hashes
# --------------------------------------------------------------------------- #
def test_nfr04_password_is_never_stored_in_plain_text(app, email_sender):
    verified_user(app, email_sender, "ayse@bilgiedu.net")

    assert not any(PASSWORD in text for text in _stored_text(app))


def test_nfr04_same_password_gives_different_stored_values(app, email_sender):
    verified_user(app, email_sender, "ayse@bilgiedu.net")
    after_first = _long_values(app, email_sender)
    verified_user(app, email_sender, "mehmet@bilgiedu.net")
    after_second = _long_values(app, email_sender)

    assert after_first, "no password hash was found in the stored data"
    assert after_second - after_first, "two users with the same password got the same stored value (no salt)"


# --------------------------------------------------------------------------- #
# NFR-05 Security: role-based access
# --------------------------------------------------------------------------- #
def test_nfr05_facility_staff_cannot_create_tournaments(app, email_sender):
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)

    with pytest.raises(PermissionDeniedError):
        app.tournaments.create_tournament(staff.id, "Spring Cup", "football", TEAMS)


def test_nfr05_club_representative_cannot_manage_facilities(app, email_sender):
    rep = verified_user(app, email_sender, "club@bilgiedu.net", Role.CLUB_REPRESENTATIVE)

    with pytest.raises(PermissionDeniedError):
        app.facilities.add_facility(rep.id, "Fake Court", ["basketball"])


def test_nfr05_student_cannot_block_a_facility(app, email_sender):
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    student = verified_user(app, email_sender, "baris@bilgiedu.net")
    court = app.facilities.add_facility(staff.id, "Dorm Basketball Court", ["basketball"])

    with pytest.raises(PermissionDeniedError):
        app.facilities.add_block(student.id, court.id, slot(hour=9, hours=3), "Fake class")


def test_nfr05_student_cannot_record_tournament_scores(app, email_sender):
    rep = verified_user(app, email_sender, "club@bilgiedu.net", Role.CLUB_REPRESENTATIVE)
    student = verified_user(app, email_sender, "baris@bilgiedu.net")
    tournament = app.tournaments.create_tournament(rep.id, "Spring Cup", "football", TEAMS)
    bracket = app.tournaments.generate_bracket(tournament.id)

    with pytest.raises(PermissionDeniedError):
        app.tournaments.record_score(student.id, bracket[0].id, 2, 1)


# --------------------------------------------------------------------------- #
# NFR-06 Privacy: no names or e-mail addresses are sent to the AI service
# --------------------------------------------------------------------------- #
def test_nfr06_ai_service_receives_no_names_or_emails(email_sender):
    ai = RecordingClient()
    app = create_app(email_sender=email_sender, ai_client=ai)
    emails = [f"{name}@bilgiedu.net" for name in ("zeynep.kaya", "can.ozturk", "elif.demir", "mert.aksoy")]
    match, players = _full_match(app, email_sender, emails)

    app.matchmaking.balance_teams(match.id, team_count=2)

    assert ai.received, "the AI service was never called"
    sent = repr(ai.received).lower()
    for player in players:
        assert player.email.lower() not in sent
        assert player.email.split("@")[0].lower() not in sent
        assert player.full_name.lower() not in sent
    assert not any(hasattr(profile, "email") or hasattr(profile, "full_name") for profile in ai.received)


# --------------------------------------------------------------------------- #
# NFR-07 Reliability: balancing still works when the AI service is unavailable
# --------------------------------------------------------------------------- #
def test_nfr07_balancing_works_when_ai_times_out(email_sender):
    app = create_app(email_sender=email_sender, ai_client=TimeoutClient())
    match, players = _full_match(app, email_sender, [f"player{i}@bilgiedu.net" for i in range(4)])

    teams = app.matchmaking.balance_teams(match.id, team_count=2)

    assert sorted(uid for team in teams for uid in team) == sorted(p.id for p in players)
    assert [len(team) for team in teams] == [2, 2]


def test_nfr07_balancing_works_without_any_ai_client(email_sender):
    app = create_app(email_sender=email_sender, ai_client=None)
    match, players = _full_match(app, email_sender, [f"player{i}@bilgiedu.net" for i in range(4)])

    teams = app.matchmaking.balance_teams(match.id, team_count=2)

    assert [len(team) for team in teams] == [2, 2]
