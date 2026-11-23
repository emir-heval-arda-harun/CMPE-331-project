"""UC-01 Register & verify e-mail, UC-02 Log in, and the role check used by the other services (NFR-04).

Business rules:
- BR-01: only university e-mail domains are accepted.
- BR-02: passwords are never stored in plain text (argon2id hashes, NFR-03); verification codes neither.
- BR-03: only verified accounts can log in.

Sessions: ``login`` returns a token signed with HMAC-SHA256 that holds the user id, the time of the
login and the session version of the user. ``get_user_by_token`` checks the signature, the age and the
version, so a token cannot be changed or made up without the secret key, it stops working after
``SESSION_LIFETIME``, and ``logout`` ends it (and every copy of it) by raising the version.

Limits (penetration test, docs/tests/security/pentest-web.md, and issue #30):
- P1: after ``MAX_FAILED_LOGINS`` wrong passwords in a row, logging in to that account pauses for a minute,
  doubling with every further wrong password up to ``LOGIN_PAUSE_MAX``. The right password ends the count.
- P2: a verification code stops working after ``MAX_CODE_ATTEMPTS`` wrong tries; ``resend_code`` sends at
  most one new code per ``RESEND_INTERVAL``.
- P3: ``logout`` ends every session of the account, also a copied cookie.
- P6: the verify step gives the same answer for an unknown, an unverified and a verified address.
- P7: very common passwords and passwords of one repeated character are refused.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from campusevent.exceptions import (
    AuthenticationError,
    DuplicateEmailError,
    EmailNotVerifiedError,
    InvalidEmailDomainError,
    InvalidVerificationCodeError,
    NotFoundError,
    PermissionDeniedError,
    TooManyAttemptsError,
    ValidationError,
)
from campusevent.models import Role, User
from campusevent.notifications import EmailSender
from campusevent.repositories.unit_of_work import InMemoryUnitOfWork, UnitOfWork
from campusevent.repositories.user_repository import InMemoryUserRepository, UserRepository
from campusevent.security import Argon2PasswordHasher, PasswordHasher

# Message of the PermissionDeniedError raised by require_role, by the role that was needed.
ROLE_MESSAGES = {
    Role.STUDENT: "Only students can do this.",
    Role.FACILITY_STAFF: "Only facility staff can do this.",
    Role.ADMIN: "Only admins can do this.",
}

CODE_LIFETIME = timedelta(minutes=15)  # Software Design Report, section 6 (verification_code.expires_at)
CODE_DIGITS = 6
SESSION_LIFETIME = timedelta(hours=24)
PASSWORD_MIN = 8
PASSWORD_MAX = 128  # hashing a very long "password" on every login attempt would cost a lot of CPU
EMAIL_MAX = 254  # user.email is VARCHAR(254)
FULL_NAME_MAX = 100  # user.full_name is VARCHAR(100)

LOGIN_FAILED = "Invalid e-mail or password."  # UC-02 2a: never tell which one was wrong
LOGIN_PAUSED = "Too many wrong passwords. Please wait a few minutes and try again."  # the web UI shows LOGIN_FAILED
CODE_FAILED = "The code is wrong or has expired"  # UC-01 5a, also for unknown and already verified addresses

MAX_CODE_ATTEMPTS = 5  # wrong codes before a code stops working (P2, #30)
RESEND_INTERVAL = timedelta(minutes=1)  # at most one new code per address per minute (#30, review of #31)
MAX_FAILED_LOGINS = 5  # wrong passwords in a row before log in pauses (P1)
LOGIN_PAUSE = timedelta(minutes=1)  # the first pause; it doubles with every further wrong password
LOGIN_PAUSE_MAX = timedelta(minutes=15)

# P7: the most common passwords of 8 or more characters (shorter ones are refused anyway), in lower case.
# Not a full dictionary: it stops the guesses that are tried first. Compared without regard to case.
COMMON_PASSWORDS = frozenset(
    {
        "12345678", "123456789", "1234567890", "12345678910", "87654321", "11223344", "12341234", "12121212",
        "11111111", "00000000", "password", "password1", "password12", "password123", "passw0rd", "p@ssw0rd",
        "qwertyui", "qwerty12", "qwerty123", "qwertyuiop", "asdfghjk", "asdfghjkl", "zxcvbnm1", "1q2w3e4r",
        "1q2w3e4r5t", "q1w2e3r4", "1qaz2wsx", "zaq12wsx", "abc12345", "abcd1234", "abcdefgh", "iloveyou",
        "sunshine", "football", "baseball", "superman", "princess", "starwars", "whatever", "trustno1",
        "welcome1", "letmein1", "computer", "admin123", "administrator", "changeme", "istanbul", "galatasaray",
        "fenerbahce", "besiktas", "trabzonspor", "sifre123", "parola123", "bilgi123", "campusevent",
    }
)


def utc_now() -> datetime:
    """The current time as naive UTC (the team time rule)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_email(email: str) -> str:
    """Addresses are stored and compared in lower case without surrounding spaces."""
    return (email or "").strip().lower()


class AuthService:
    def __init__(
        self,
        allowed_email_domains: tuple[str, ...],
        email_sender: EmailSender,
        users: UserRepository | None = None,
        uow: UnitOfWork | None = None,
        hasher: PasswordHasher | None = None,
        secret_key: str | bytes | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.allowed_email_domains = tuple(d.strip().lower() for d in allowed_email_domains)
        self.email_sender = email_sender
        # Without a repository (requirement tests, create_app() today) the users are kept in memory.
        self.users = users if users is not None else InMemoryUserRepository()
        self.uow = uow if uow is not None else InMemoryUnitOfWork()
        self.hasher = hasher if hasher is not None else Argon2PasswordHasher()
        # Signs the session tokens. Without a key (tests) every AuthService makes its own random one, so its
        # tokens are refused by any other process. Production passes SECRET_KEY (see app.py).
        if not secret_key:
            secret_key = secrets.token_bytes(32)
        if isinstance(secret_key, str):
            secret_key = secret_key.encode()
        # A separate key for the tokens, derived from the secret, so it is never the same as Flask's cookie key.
        self._token_key = hmac.new(secret_key, b"campusevent session token", hashlib.sha256).digest()
        self.clock = clock
        self._dummy_hash: str | None = None

    # ------------------------------------------------------------------ #
    # UC-01 Register & verify e-mail
    # ------------------------------------------------------------------ #
    def register(self, email: str, password: str, full_name: str, role: Role = Role.STUDENT) -> User:
        """Create an unverified account and send a verification code by e-mail."""
        email = normalize_email(email)
        full_name = (full_name or "").strip()
        self._check_email(email)  # BR-01, before anything is stored (UC-01 2a)
        if not full_name:
            raise ValidationError("Please enter your full name.")
        if len(full_name) > FULL_NAME_MAX:
            raise ValidationError(f"The name can be at most {FULL_NAME_MAX} characters long.")
        self._check_password(password)
        if not isinstance(role, Role):
            raise ValidationError("Unknown role.")

        self.uow.begin()
        try:
            if self.users.find_by_email(email) is not None:  # UC-01 3a
                raise DuplicateEmailError(f"An account with {email} already exists")
            user = self.users.add(User(id=0, email=email, full_name=full_name, role=role), self.hasher.hash(password))
            code = self._new_code(user.id)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        # Sent after the commit: a code is never e-mailed for an account that was not stored.
        self.email_sender.send_verification_code(email, code)
        return user

    def verify_email(self, email: str, code: str) -> User:
        """Mark the account as verified if the code is correct."""
        email = normalize_email(email)
        code = (code or "").strip()
        self.uow.begin()
        try:
            user = self.users.find_by_email(email)
            # P6: an unknown and an already verified address get the same answer as a wrong code, so this step
            # does not tell which addresses have (verified) accounts. A hash is checked anyway, so the time
            # does not tell it either.
            if user is None or user.is_verified:
                self.hasher.verify(self._get_dummy_hash(), code)
                raise InvalidVerificationCodeError(CODE_FAILED)
            latest = self.users.get_latest_code(user.id)  # only the last code that was sent counts
            if latest is None or not latest.is_valid(self.clock()) or latest.attempts >= MAX_CODE_ATTEMPTS:
                raise InvalidVerificationCodeError(CODE_FAILED)  # UC-01 5a: expired, used or tried too often
            if not self.hasher.verify(latest.code_hash, code):
                self.users.record_wrong_code(latest.id)  # P2: kept, although the answer is an error
                self.uow.commit()
                raise InvalidVerificationCodeError(CODE_FAILED)
            self.users.mark_code_used(latest.id)  # a code works only once
            self.users.mark_verified(user.id)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return replace(user, is_verified=True)

    def resend_code(self, email: str) -> None:
        """Send a new verification code (UC-01 5a "request a new code", UC-02 3a). The older codes stop working.

        Nothing happens for an unknown or an already verified address, nor when the last code was sent less
        than ``RESEND_INTERVAL`` ago, and the caller is not told, so the page cannot be used to find out which
        addresses have accounts, nor to get a new set of tries every few seconds (#30). In those cases a dummy
        code is hashed, so the time of the answer tells less about it."""
        email = normalize_email(email)
        self.uow.begin()
        try:
            user = self.users.find_by_email(email)
            latest = self.users.get_latest_code(user.id) if user is not None and not user.is_verified else None
            too_soon = latest is not None and self.clock() < latest.expires_at - CODE_LIFETIME + RESEND_INTERVAL
            if user is None or user.is_verified or too_soon:
                self.uow.rollback()
                self.hasher.hash(secrets.token_hex(3))  # about the work of a real new code
                return
            code = self._new_code(user.id)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        self.email_sender.send_verification_code(email, code)

    # ------------------------------------------------------------------ #
    # UC-02 Log in
    # ------------------------------------------------------------------ #
    def login(self, email: str, password: str) -> str:
        """Return a session token for a verified user.

        P1: wrong passwords in a row are counted per account. From the ``MAX_FAILED_LOGINS``-th on, each one
        pauses logging in to that account (1, 2, 4, 8 and then 15 minutes); during a pause even the right
        password is refused with ``TooManyAttemptsError``. The right password sets the count back to 0."""
        user = self.users.find_by_email(normalize_email(email))
        if user is None:
            # Hash anyway, so an unknown e-mail takes as long as a wrong password and the time does not tell
            # which e-mails have accounts.
            self.hasher.verify(self._get_dummy_hash(), password or "")
            raise AuthenticationError(LOGIN_FAILED)
        now = self.clock()
        error: Exception | None = None
        self.uow.begin()
        try:
            failures, paused_until = self.users.get_login_failures(user.id)  # locks the row in PostgreSQL
            if paused_until is not None and now < paused_until:
                # The password is not checked, but a hash is, so a paused account answers as slowly as any
                # other and the time does not tell that the address has an account (pentest A4).
                self.hasher.verify(self._get_dummy_hash(), password or "")
                error = TooManyAttemptsError(LOGIN_PAUSED)
            elif not self.hasher.verify(self.users.get_password_hash(user.id), password or ""):
                failures += 1
                pause = None
                if failures >= MAX_FAILED_LOGINS:
                    pause = now + min(LOGIN_PAUSE * 2 ** (failures - MAX_FAILED_LOGINS), LOGIN_PAUSE_MAX)
                self.users.set_login_failures(user.id, failures, pause)
                error = AuthenticationError(LOGIN_FAILED)  # UC-02 2a
            else:
                if failures or paused_until is not None:
                    self.users.set_login_failures(user.id, 0, None)
                if not user.is_verified:  # BR-03, UC-02 3a
                    error = EmailNotVerifiedError("Please verify your e-mail address before logging in.")
                version = self.users.get_session_version(user.id)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        if error is not None:
            raise error
        return self._token_for(user.id, version)

    def logout(self, token: str) -> None:
        """End the session of this token and every other session of the same account (P3): a copy of the
        cookie, for example on a shared computer, stops working too. An invalid token is ignored."""
        try:
            user = self.get_user_by_token(token)
        except AuthenticationError:
            return
        self.uow.begin()
        try:
            self.users.next_session_version(user.id)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise

    def get_user_by_token(self, token: str) -> User:
        """The user of a session token. Raises ``AuthenticationError`` for a changed, made up or expired token."""
        try:
            user_id, issued, version, signature = (token or "").split(".")
            if not hmac.compare_digest(signature.encode(), self._sign(f"{user_id}.{issued}.{version}").encode()):
                raise ValueError("bad signature")
            user_id, version = int(user_id), int(version)
            issued_at = datetime.fromtimestamp(int(issued), timezone.utc).replace(tzinfo=None)
        except (ValueError, OverflowError, OSError):
            raise AuthenticationError("Your session is not valid. Please log in again.") from None
        age = self.clock() - issued_at
        if age > SESSION_LIFETIME or age < -timedelta(minutes=5):  # small allowance for clocks of other servers
            raise AuthenticationError("Your session has expired. Please log in again.")
        try:
            if self.users.get_session_version(user_id) != version:  # logged out since (P3)
                raise AuthenticationError("Your session has ended. Please log in again.")
            return self.users.get(user_id)
        except NotFoundError:  # the account was deleted after the login
            raise AuthenticationError("Your session is not valid. Please log in again.") from None

    # ------------------------------------------------------------------ #
    # Users and roles (NFR-04)
    # ------------------------------------------------------------------ #
    def get_user(self, user_id: int) -> User:
        """Raises ``NotFoundError`` for an unknown id."""
        return self.users.get(user_id)

    def require_role(self, user_id: int, role: Role) -> User:
        """The second role check of NFR-04, called by the services themselves (for example BR-09:
        only facility staff manage facilities), so a rule holds even if a route forgets its decorator.

        Returns the user. Raises ``NotFoundError`` for an unknown id (like the stand-ins in the tests) and
        ``PermissionDeniedError`` if the user has another role."""
        user = self.get_user(user_id)
        if user.role != role:
            raise PermissionDeniedError(ROLE_MESSAGES[role])
        return user

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _check_email(self, email: str) -> None:
        local, at, domain = email.rpartition("@")
        if not at or not local or not domain or len(email) > EMAIL_MAX or any(c.isspace() for c in email):
            raise ValidationError("Please enter a valid e-mail address.")
        if domain not in self.allowed_email_domains:
            raise InvalidEmailDomainError(f"{domain} is not a university e-mail domain")

    @staticmethod
    def _check_password(password: str) -> None:
        if not isinstance(password, str) or len(password) < PASSWORD_MIN:
            raise ValidationError(f"The password must be at least {PASSWORD_MIN} characters long.")
        if len(password) > PASSWORD_MAX:
            raise ValidationError(f"The password can be at most {PASSWORD_MAX} characters long.")
        if password.lower() in COMMON_PASSWORDS or len(set(password)) == 1:  # P7
            raise ValidationError("This password is too easy to guess. Please choose another one.")

    def _new_code(self, user_id: int) -> str:
        """Store the hash of a new random code (``secrets``, not ``random``) and return the code for the e-mail."""
        code = f"{secrets.randbelow(10**CODE_DIGITS):0{CODE_DIGITS}d}"
        self.users.save_code(user_id, self.hasher.hash(code), self.clock() + CODE_LIFETIME)
        return code

    def _sign(self, payload: str) -> str:
        digest = hmac.new(self._token_key, payload.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    def _token_for(self, user_id: int, version: int) -> str:
        issued = int(self.clock().replace(tzinfo=timezone.utc).timestamp())
        payload = f"{user_id}.{issued}.{version}"
        return f"{payload}.{self._sign(payload)}"

    def _get_dummy_hash(self) -> str:
        if self._dummy_hash is None:
            self._dummy_hash = self.hasher.hash(secrets.token_hex(16))
        return self._dummy_hash
