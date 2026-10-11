"""UC-01 Register & verify e-mail, UC-02 Log in."""

from __future__ import annotations

from campusevent.models import Role, User
from campusevent.notifications import EmailSender


class AuthService:
    def __init__(self, allowed_email_domains: tuple[str, ...], email_sender: EmailSender) -> None:
        self.allowed_email_domains = allowed_email_domains
        self.email_sender = email_sender

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
