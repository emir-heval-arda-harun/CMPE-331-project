"""UC-01 Register & verify e-mail, UC-02 Log in, and the role check used by the other services (NFR-04)."""

from __future__ import annotations

from campusevent.exceptions import PermissionDeniedError
from campusevent.models import Role, User
from campusevent.notifications import EmailSender
from campusevent.repositories.user_repository import InMemoryUserRepository, UserRepository

# Message of the PermissionDeniedError raised by require_role, by the role that was needed.
ROLE_MESSAGES = {
    Role.STUDENT: "Only students can do this.",
    Role.FACILITY_STAFF: "Only facility staff can do this.",
    Role.ADMIN: "Only admins can do this.",
}


class AuthService:
    def __init__(
        self,
        allowed_email_domains: tuple[str, ...],
        email_sender: EmailSender,
        users: UserRepository | None = None,
    ) -> None:
        self.allowed_email_domains = allowed_email_domains
        self.email_sender = email_sender
        # Without a repository (requirement tests, create_app() today) the users are kept in memory.
        self.users = users if users is not None else InMemoryUserRepository()

    def register(self, email: str, password: str, full_name: str, role: Role = Role.STUDENT) -> User:
        """Create an unverified account and send a verification code by e-mail."""
        raise NotImplementedError

    def verify_email(self, email: str, code: str) -> User:
        """Mark the account as verified if the code is correct."""
        raise NotImplementedError

    def login(self, email: str, password: str) -> str:
        """Return a session token for a verified user."""
        raise NotImplementedError

    def get_user_by_token(self, token: str) -> User:
        raise NotImplementedError

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
