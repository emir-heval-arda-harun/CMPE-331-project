"""UC-01 Register with university e-mail and verify account."""

import pytest

from campusevent.exceptions import DuplicateEmailError, InvalidEmailDomainError, InvalidVerificationCodeError
from tests.helpers import PASSWORD


def test_registration_with_university_email_sends_verification_code(app, email_sender):
    user = app.auth.register("ayse.yilmaz@bilgiedu.net", PASSWORD, "Ayse Yilmaz")

    assert user.is_verified is False
    assert "ayse.yilmaz@bilgiedu.net" in email_sender.codes


def test_correct_code_verifies_account(app, email_sender):
    app.auth.register("ayse.yilmaz@bilgiedu.net", PASSWORD, "Ayse Yilmaz")

    user = app.auth.verify_email("ayse.yilmaz@bilgiedu.net", email_sender.codes["ayse.yilmaz@bilgiedu.net"])

    assert user.is_verified is True


def test_non_university_email_is_rejected(app):
    with pytest.raises(InvalidEmailDomainError):
        app.auth.register("ayse@gmail.com", PASSWORD, "Ayse Yilmaz")


def test_wrong_verification_code_is_rejected(app):
    app.auth.register("ayse.yilmaz@bilgiedu.net", PASSWORD, "Ayse Yilmaz")

    with pytest.raises(InvalidVerificationCodeError):
        app.auth.verify_email("ayse.yilmaz@bilgiedu.net", "000000-wrong")


def test_duplicate_email_is_rejected(app):
    app.auth.register("ayse.yilmaz@bilgiedu.net", PASSWORD, "Ayse Yilmaz")

    with pytest.raises(DuplicateEmailError):
        app.auth.register("ayse.yilmaz@bilgiedu.net", PASSWORD, "Ayse Y.")
