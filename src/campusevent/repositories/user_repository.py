"""UserRepository: user accounts (layer 3, task 3.2).

This first part has what ``AuthService.get_user`` and ``require_role`` need (``add`` and ``get``).
The rest of the interface in class diagram 4.2 (``find_by_email``, ``get_password_hash``, the
verification code methods, ``mark_verified``) comes with UC-01 and UC-02.

``InMemoryUserRepository`` is used by the requirement tests, ``SqlUserRepository`` in production.
Both return ``campusevent.models.User``; the services never see a ``UserRow`` or a password hash.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, scoped_session

from campusevent.exceptions import DuplicateEmailError, NotFoundError
from campusevent.models import Role, User
from campusevent.repositories.tables import UserRow


class UserRepository(Protocol):
    def add(self, user: User, password_hash: str) -> User:
        """Store a new account; the ``id`` of the argument is ignored and the stored user returned."""
        ...

    def get(self, user_id: int) -> User:
        """Raise ``NotFoundError`` for an unknown id."""
        ...


class InMemoryUserRepository:
    """Users kept in a dictionary (requirement tests and development)."""

    def __init__(self) -> None:
        self._users: dict[int, User] = {}
        self._password_hashes: dict[int, str] = {}
        self._next_id = 1

    def add(self, user: User, password_hash: str) -> User:
        stored = User(
            id=self._next_id, email=user.email, full_name=user.full_name, role=user.role, is_verified=user.is_verified
        )
        self._next_id += 1
        self._users[stored.id] = stored
        self._password_hashes[stored.id] = password_hash
        return stored

    def get(self, user_id: int) -> User:
        try:
            return self._users[user_id]
        except KeyError:
            raise NotFoundError(f"User {user_id} does not exist") from None


# --------------------------------------------------------------------------- #
# PostgreSQL
# --------------------------------------------------------------------------- #
class SqlUserRepository:
    """Users in PostgreSQL. Shares the scoped session of ``SqlUnitOfWork`` (one transaction per request)."""

    def __init__(self, session: scoped_session[Session]) -> None:
        self.session = session

    @staticmethod
    def _user(row: UserRow) -> User:
        return User(id=row.id, email=row.email, full_name=row.full_name, role=Role(row.role), is_verified=row.is_verified)

    def add(self, user: User, password_hash: str) -> User:
        row = UserRow(
            email=user.email,
            full_name=user.full_name,
            password_hash=password_hash,
            role=user.role.value,
            is_verified=user.is_verified,
        )
        try:
            self.session.add(row)
            self.session.flush()  # constraint errors come out here, inside the repository
        except IntegrityError as error:  # the service's UnitOfWork rolls the transaction back
            if _constraint(error) == "ux_user_email_lower":
                raise DuplicateEmailError(f"An account with {user.email} already exists") from error
            raise
        return self._user(row)

    def get(self, user_id: int) -> User:
        row = self.session.get(UserRow, user_id)
        if row is None:
            raise NotFoundError(f"User {user_id} does not exist")
        return self._user(row)


def _constraint(error: IntegrityError) -> str | None:
    diag = getattr(error.orig, "diag", None)
    return getattr(diag, "constraint_name", None)
