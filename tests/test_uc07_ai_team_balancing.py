"""UC-07 AI skill-based team balancing."""

from campusevent import create_app
from campusevent.models import SkillLevel
from tests.helpers import open_match, verified_user


class FakeGeminiClient:
    """Stands in for Gemini Pro: returns a fixed rating per player."""

    def __init__(self, ratings_by_email):
        self.ratings_by_email = ratings_by_email
        self.email_by_user_id = {}

    def rate_players(self, sport, profiles):
        return {p.user_id: self.ratings_by_email[self.email_by_user_id[p.user_id]] for p in profiles}


class UnavailableClient:
    def rate_players(self, sport, profiles):
        raise ConnectionError("AI service is down")


RATINGS = {"p1@bilgiedu.net": 9.0, "p2@bilgiedu.net": 8.0, "p3@bilgiedu.net": 3.0, "p4@bilgiedu.net": 2.0}


def _full_match(app, email_sender):
    players = [verified_user(app, email_sender, email) for email in RATINGS]
    for p in players:
        app.profiles.update_profile(p.id, sports={"football": SkillLevel.INTERMEDIATE}, availability=[])
    match = open_match(app, email_sender, players[0], capacity=4)
    for p in players[1:]:
        app.matches.join_match(match.id, p.id)
    return match, players


def test_teams_are_balanced_by_ai_rating(email_sender):
    ai = FakeGeminiClient(RATINGS)
    app = create_app(email_sender=email_sender, ai_client=ai)
    match, players = _full_match(app, email_sender)
    ai.email_by_user_id = {p.id: p.email for p in players}
    rating = {p.id: RATINGS[p.email] for p in players}

    teams = app.matchmaking.balance_teams(match.id, team_count=2)

    assert sorted(uid for team in teams for uid in team) == sorted(p.id for p in players)
    totals = [sum(rating[uid] for uid in team) for team in teams]
    assert abs(totals[0] - totals[1]) <= 2.0


def test_falls_back_to_declared_skill_when_ai_is_unavailable(email_sender):
    app = create_app(email_sender=email_sender, ai_client=UnavailableClient())
    match, players = _full_match(app, email_sender)

    teams = app.matchmaking.balance_teams(match.id, team_count=2)

    assert [len(team) for team in teams] == [2, 2]
