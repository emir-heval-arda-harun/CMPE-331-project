"""UC-01 Register & verify e-mail, UC-02 Log in, and the role check used by the other services (NFR-04).

Business rules:
- BR-01: only university e-mail domains are accepted.
- BR-02: passwords are never stored in plain text (argon2id hashes, NFR-03); verification codes neither.
- BR-03: only verified accounts can log in.

Sessions: ``login`` returns a token signed with HMAC-SHA256 that holds the user id and the time of the
login. ``get_user_by_token`` checks the signature and the age, so a token cannot be changed or made up
without the secret key, and it stops working after ``SESSION_LIFETIME``. The web UI keeps the token in
the (also signed) session cookie; logging out deletes the cookie.
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
            if user is None:  # same error as a wrong code: the page does not tell which e-mails have accounts
                raise InvalidVerificationCodeError("The code is wrong or has expired")
            if user.is_verified:
                raise ValidationError("This e-mail address is already verified. You can log in.")
            latest = self.users.get_latest_code(user.id)  # only the last code that was sent counts
            if latest is None or not latest.is_valid(self.clock()) or not self.hasher.verify(latest.code_hash, code):
                raise InvalidVerificationCodeError("The code is wrong or has expired")  # UC-01 5a
            self.users.mark_code_used(latest.id)  # a code works only once
            self.users.mark_verified(user.id)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return replace(user, is_verified=True)

    def resend_code(self, email: str) -> None:
        """Send a new verification code (UC-01 5a "request a new code", UC-02 3a). The older codes stop working.

        Nothing happens for an unknown or an already verified address, and the caller is not told, so the
        page cannot be used to find out which addresses have accounts."""
        email = normalize_email(email)
        self.uow.begin()
        try:
            user = self.users.find_by_email(email)
            if user is None or user.is_verified:
                self.uow.rollback()
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
        """Return a session token for a verified user."""
        user = self.users.find_by_email(normalize_email(email))
        if user is None:
            # Hash anyway, so an unknown e-mail takes as long as a wrong password and the time does not tell
            # which e-mails have accounts.
            self.hasher.verify(self._get_dummy_hash(), password or "")
            raise AuthenticationError(LOGIN_FAILED)
        if not self.hasher.verify(self.users.get_password_hash(user.id), password or ""):
            raise AuthenticationError(LOGIN_FAILED)  # UC-02 2a
        if not user.is_verified:
            raise EmailNotVerifiedError("Please verify your e-mail address before logging in.")  # BR-03, UC-02 3a
        return self._token_for(user.id)

    def get_user_by_token(self, token: str) -> User:
        """The user of a session token. Raises ``AuthenticationError`` for a changed, made up or expired token."""
        try:
            user_id, issued, signature = (token or "").split(".")
            if not hmac.compare_digest(signature.encode(), self._sign(f"{user_id}.{issued}").encode()):
                raise ValueError("bad signature")
            user_id, issued_at = int(user_id), datetime.fromtimestamp(int(issued), timezone.utc).replace(tzinfo=None)
        except (ValueError, OverflowError, OSError):
            raise AuthenticationError("Your session is not valid. Please log in again.") from None
        age = self.clock() - issued_at
        if age > SESSION_LIFETIME or age < -timedelta(minutes=5):  # small allowance for clocks of other servers
            raise AuthenticationError("Your session has expired. Please log in again.")
        try:
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

    def _new_code(self, user_id: int) -> str:
        """Store the hash of a new random code (``secrets``, not ``random``) and return the code for the e-mail."""
        code = f"{secrets.randbelow(10**CODE_DIGITS):0{CODE_DIGITS}d}"
        self.users.save_code(user_id, self.hasher.hash(code), self.clock() + CODE_LIFETIME)
        return code

    def _sign(self, payload: str) -> str:
        digest = hmac.new(self._token_key, payload.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    def _token_for(self, user_id: int) -> str:
        issued = int(self.clock().replace(tzinfo=timezone.utc).timestamp())
        payload = f"{user_id}.{issued}"
        return f"{payload}.{self._sign(payload)}"

    def _get_dummy_hash(self) -> str:
        if self._dummy_hash is None:
            self._dummy_hash = self.hasher.hash(secrets.token_hex(16))
        return self._dummy_hash
