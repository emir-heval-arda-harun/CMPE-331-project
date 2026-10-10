"""UC-02 Log in."""

import pytest

from campusevent.exceptions import AuthenticationError, EmailNotVerifiedError
from tests.helpers import PASSWORD, verified_user


def test_verified_user_logs_in_and_gets_session(app, email_sender):
    user = verified_user(app, email_sender, "can@bilgiedu.net")

    token = app.auth.login("can@bilgiedu.net", PASSWORD)

    assert token
    assert app.auth.get_user_by_token(token).id == user.id


def test_wrong_password_is_rejected(app, email_sender):
    verified_user(app, email_sender, "can@bilgiedu.net")

    with pytest.raises(AuthenticationError):
        app.auth.login("can@bilgiedu.net", "wrong-password")


def test_unverified_user_cannot_log_in(app):
    app.auth.register("can@bilgiedu.net", PASSWORD, "Can")

    with pytest.raises(EmailNotVerifiedError):
        app.auth.login("can@bilgiedu.net", PASSWORD)
