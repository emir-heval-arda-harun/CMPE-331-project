"""Unit tests of AuthService for UC-01 (register, verify, new code) and UC-02 (log in, session tokens).

The requirement tests (test_uc01_*, test_uc02_*) check the main and alternative flows of the use cases;
these tests check the rules behind them: normalized e-mails, input checks, code expiry, the transaction,
and that a session token cannot be changed or used forever.
"""

from datetime import datetime, timedelta

import pytest

from campusevent.auth import CODE_LIFETIME, SESSION_LIFETIME, AuthService
from campusevent.exceptions import (
    AuthenticationError,
    DuplicateEmailError,
    EmailNotVerifiedError,
    InvalidEmailDomainError,
    InvalidVerificationCodeError,
    ValidationError,
)
from campusevent.models import Role
from campusevent.notifications import InMemoryEmailSender
from campusevent.repositories.unit_of_work import InMemoryUnitOfWork
from campusevent.repositories.user_repository import InMemoryUserRepository

PASSWORD = "S3cure-pass!"
EMAIL = "ayse@bilgiedu.net"


class Clock:
    def __init__(self):
        self.now = datetime(2026, 11, 20, 12, 0)

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def sender():
    return InMemoryEmailSender()


@pytest.fixture
def users():
    return InMemoryUserRepository()


@pytest.fixture
def uow():
    return InMemoryUnitOfWork()


@pytest.fixture
def auth(sender, users, uow, fast_hasher, clock):
    return AuthService(
        ("bilgiedu.net", "bilgi.edu.tr"), sender, users, uow=uow, hasher=fast_hasher, secret_key="test", clock=clock
    )


def registered(auth, sender, email=EMAIL):
    user = auth.register(email, PASSWORD, "Ayse Yilmaz")
    return user, sender.codes[email]


def verified(auth, sender, email=EMAIL):
    user, code = registered(auth, sender, email)
    return auth.verify_email(email, code)


# --------------------------------------------------------------------------- #
# UC-01 Register
# --------------------------------------------------------------------------- #
def test_register_stores_a_normalized_unverified_student(auth, sender, users):
    user = auth.register("  Ayse.Yilmaz@BilgiEdu.net ", PASSWORD, "  Ayse Yilmaz ")

    assert (user.email, user.full_name, user.role, user.is_verified) == (
        "ayse.yilmaz@bilgiedu.net", "Ayse Yilmaz", Role.STUDENT, False
    )
    assert users.get(user.id) == user
    assert "ayse.yilmaz@bilgiedu.net" in sender.codes


def test_password_and_code_are_stored_only_as_argon2_hashes(auth, sender, users):
    user, code = registered(auth, sender)

    password_hash = users.get_password_hash(user.id)
    code_hash = users.get_latest_code(user.id).code_hash
    assert password_hash.startswith("$argon2id$") and PASSWORD not in password_hash
    assert code_hash.startswith("$argon2id$") and code not in code_hash


def test_code_has_six_digits_and_expires_after_15_minutes(auth, sender, users, clock):
    user, code = registered(auth, sender)

    assert len(code) == 6 and code.isdigit()
    assert users.get_latest_code(user.id).expires_at == clock.now + CODE_LIFETIME


@pytest.mark.parametrize("email", ["ayse@bilgiedu.net.evil.com", "ayse@mail.bilgiedu.net", "ayse@gmail.com"])
def test_only_the_exact_university_domains_are_accepted(auth, email):
    with pytest.raises(InvalidEmailDomainError):
        auth.register(email, PASSWORD, "Ayse")


@pytest.mark.parametrize("email", ["", "ayse", "@bilgiedu.net", "ay se@bilgiedu.net", "a" * 250 + "@bilgiedu.net"])
def test_malformed_email_is_rejected(auth, email):
    with pytest.raises(ValidationError):
        auth.register(email, PASSWORD, "Ayse")


@pytest.mark.parametrize("password", ["", "short12", "x" * 129])
def test_password_length_is_checked(auth, password):
    with pytest.raises(ValidationError):
        auth.register(EMAIL, password, "Ayse")


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
def test_full_name_is_required_and_limited(auth, name):
    with pytest.raises(ValidationError):
        auth.register(EMAIL, PASSWORD, name)


def test_rejected_input_stores_nothing_and_sends_nothing(auth, sender, users):
    with pytest.raises(InvalidEmailDomainError):
        auth.register("ayse@gmail.com", PASSWORD, "Ayse")

    assert users.find_by_email("ayse@gmail.com") is None
    assert sender.codes == {}


def test_duplicate_in_other_case_is_rejected_and_rolled_back(auth, sender, uow):
    registered(auth, sender)

    with pytest.raises(DuplicateEmailError):
        auth.register("AYSE@bilgiedu.net", PASSWORD, "Ayse Y.")
    assert (uow.commits, uow.rollbacks) == (1, 1)


# --------------------------------------------------------------------------- #
# UC-01 Verify and new code
# --------------------------------------------------------------------------- #
def test_verify_accepts_the_email_in_any_case_and_marks_the_account(auth, sender, users):
    user, code = registered(auth, sender)

    verified_user = auth.verify_email(" AYSE@bilgiedu.net ", f" {code} ")

    assert verified_user.is_verified is True
    assert users.get(user.id).is_verified is True


def test_code_does_not_work_after_15_minutes(auth, sender, clock):
    _, code = registered(auth, sender)
    clock.now += CODE_LIFETIME

    with pytest.raises(InvalidVerificationCodeError):
        auth.verify_email(EMAIL, code)


def test_code_works_just_before_it_expires(auth, sender, clock):
    _, code = registered(auth, sender)
    clock.now += CODE_LIFETIME - timedelta(seconds=1)

    assert auth.verify_email(EMAIL, code).is_verified is True


def test_unknown_email_gets_the_same_error_as_a_wrong_code(auth):
    with pytest.raises(InvalidVerificationCodeError):
        auth.verify_email("nobody@bilgiedu.net", "123456")


def test_verifying_twice_says_the_account_is_already_verified(auth, sender):
    _, code = registered(auth, sender)
    auth.verify_email(EMAIL, code)

    with pytest.raises(ValidationError, match="already verified"):
        auth.verify_email(EMAIL, code)


def test_new_code_replaces_the_old_one(auth, sender, clock):
    _, old_code = registered(auth, sender)
    clock.now += timedelta(minutes=20)  # the old code has expired
    auth.resend_code(EMAIL)
    new_code = sender.codes[EMAIL]

    if new_code != old_code:  # one chance in a million that both codes are the same
        with pytest.raises(InvalidVerificationCodeError):
            auth.verify_email(EMAIL, old_code)
    assert auth.verify_email(EMAIL, new_code).is_verified is True


def test_new_code_is_not_sent_to_unknown_or_verified_addresses(auth, sender):
    verified(auth, sender)
    sender.codes.clear()

    auth.resend_code(EMAIL)
    auth.resend_code("nobody@bilgiedu.net")

    assert sender.codes == {}


# --------------------------------------------------------------------------- #
# UC-02 Log in
# --------------------------------------------------------------------------- #
def test_login_accepts_the_email_in_any_case(auth, sender):
    user = verified(auth, sender)

    token = auth.login(" Ayse@BILGIEDU.net", PASSWORD)

    assert auth.get_user_by_token(token) == user


def test_unknown_email_and_wrong_password_give_the_same_message(auth, sender):
    verified(auth, sender)

    with pytest.raises(AuthenticationError) as unknown:
        auth.login("nobody@bilgiedu.net", PASSWORD)
    with pytest.raises(AuthenticationError) as wrong:
        auth.login(EMAIL, "wrong-password")
    assert str(unknown.value) == str(wrong.value) == "Invalid e-mail or password."


def test_unverified_user_with_wrong_password_is_not_told_that_the_account_exists(auth, sender):
    registered(auth, sender)

    with pytest.raises(AuthenticationError):
        auth.login(EMAIL, "wrong-password")
    with pytest.raises(EmailNotVerifiedError):
        auth.login(EMAIL, PASSWORD)


@pytest.mark.parametrize("password", ["", None])
def test_empty_password_is_a_failed_login(auth, sender, password):
    verified(auth, sender)

    with pytest.raises(AuthenticationError):
        auth.login(EMAIL, password)


# --------------------------------------------------------------------------- #
# Session tokens
# --------------------------------------------------------------------------- #
def test_changed_or_made_up_tokens_are_rejected(auth, sender):
    user = verified(auth, sender)
    token = auth.login(EMAIL, PASSWORD)
    user_id, issued, signature = token.split(".")

    for bad in ["", "garbage", f"{user_id + '0'}.{issued}.{signature}", f"{user_id}.{int(issued) + 60}.{signature}",
                f"{user_id}.{issued}.{signature[:-2]}", f"{user.id + 1}.{issued}.{signature}", token + ".x"]:
        with pytest.raises(AuthenticationError):
            auth.get_user_by_token(bad)


def test_token_of_another_secret_key_is_rejected(auth, sender, users, fast_hasher):
    verified(auth, sender)
    other = AuthService(("bilgiedu.net",), sender, users, hasher=fast_hasher, secret_key="another key")

    with pytest.raises(AuthenticationError):
        other.get_user_by_token(auth.login(EMAIL, PASSWORD))


def test_token_expires_after_the_session_lifetime(auth, sender, clock):
    user = verified(auth, sender)
    token = auth.login(EMAIL, PASSWORD)

    clock.now += SESSION_LIFETIME
    assert auth.get_user_by_token(token) == user
    clock.now += timedelta(seconds=1)
    with pytest.raises(AuthenticationError, match="expired"):
        auth.get_user_by_token(token)


def test_token_survives_a_restart_with_the_same_secret_key(auth, sender, users, fast_hasher, clock):
    user = verified(auth, sender)
    token = auth.login(EMAIL, PASSWORD)
    restarted = AuthService(("bilgiedu.net",), sender, users, hasher=fast_hasher, secret_key="test", clock=clock)

    assert restarted.get_user_by_token(token) == user
