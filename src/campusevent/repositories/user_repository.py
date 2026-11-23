"""UserRepository: user accounts and their verification codes (layer 3, UC-01, UC-02).

The interface is the one of class diagram 4.2. ``InMemoryUserRepository`` is used by the requirement
tests, ``SqlUserRepository`` in production. Both return ``campusevent.models`` objects; the services
never see a ``UserRow``. The password hash leaves the repository only through ``get_password_hash``.

E-mail addresses are compared without regard to case (``ux_user_email_lower``), like the database does.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Protocol

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, scoped_session

from campusevent.exceptions import DuplicateEmailError, NotFoundError
from campusevent.models import Role, User, VerificationCode
from campusevent.repositories.facility_repository import _from_db, _to_db  # the team time rule (naive UTC)
from campusevent.repositories.tables import UserRow, VerificationCodeRow


class UserRepository(Protocol):
    def add(self, user: User, password_hash: str) -> User:
        """Store a new account; the ``id`` of the argument is ignored and the stored user returned."""
        ...

    def get(self, user_id: int) -> User:
        """Raise ``NotFoundError`` for an unknown id."""
        ...

    def find_by_email(self, email: str) -> User | None:
        """The user with this e-mail address in any upper or lower case, or None."""
        ...

    def get_password_hash(self, user_id: int) -> str:
        ...

    def save_code(self, user_id: int, code_hash: str, expires_at: datetime) -> VerificationCode:
        ...

    def get_latest_code(self, user_id: int) -> VerificationCode | None:
        """The code sent last to the user (used or not), or None if no code was ever sent."""
        ...

    def mark_code_used(self, code_id: int) -> None:
        ...

    def mark_verified(self, user_id: int) -> None:
        ...

    def record_wrong_code(self, code_id: int) -> None:
        """Add 1 to the wrong attempts of a code (pentest P2, #30)."""
        ...

    def get_login_failures(self, user_id: int) -> tuple[int, datetime | None]:
        """Wrong passwords in a row and the end of the log in pause (or None). The SQL version locks the user
        row until the end of the transaction, so two log ins at the same moment cannot both count from the same
        number (pentest P1)."""
        ...

    def set_login_failures(self, user_id: int, failures: int, paused_until: datetime | None) -> None:
        ...

    def get_session_version(self, user_id: int) -> int:
        """Raise ``NotFoundError`` for an unknown id."""
        ...

    def next_session_version(self, user_id: int) -> None:
        """Add 1 to the session version: every token with the old version stops working (pentest P3)."""
        ...


class InMemoryUserRepository:
    """Users kept in a dictionary (requirement tests and development).

    Like the database it hands out copies, so changing a returned ``User`` does not change the stored one.
    """

    def __init__(self) -> None:
        self._users: dict[int, User] = {}
        self._password_hashes: dict[int, str] = {}
        self._codes: dict[int, VerificationCode] = {}
        self._login_failures: dict[int, tuple[int, datetime | None]] = {}
        self._session_versions: dict[int, int] = {}
        self._next_id = 1
        self._next_code_id = 1

    def add(self, user: User, password_hash: str) -> User:
        if self.find_by_email(user.email) is not None:
            raise DuplicateEmailError(f"An account with {user.email} already exists")
        stored = replace(user, id=self._next_id)
        self._next_id += 1
        self._users[stored.id] = stored
        self._password_hashes[stored.id] = password_hash
        return replace(stored)

    def get(self, user_id: int) -> User:
        try:
            return replace(self._users[user_id])
        except KeyError:
            raise NotFoundError(f"User {user_id} does not exist") from None

    def find_by_email(self, email: str) -> User | None:
        wanted = email.strip().lower()
        found = next((u for u in self._users.values() if u.email.lower() == wanted), None)
        return replace(found) if found else None

    def get_password_hash(self, user_id: int) -> str:
        self.get(user_id)
        return self._password_hashes[user_id]

    def save_code(self, user_id: int, code_hash: str, expires_at: datetime) -> VerificationCode:
        self.get(user_id)
        code = VerificationCode(id=self._next_code_id, user_id=user_id, code_hash=code_hash, expires_at=expires_at)
        self._next_code_id += 1
        self._codes[code.id] = code
        return replace(code)

    def get_latest_code(self, user_id: int) -> VerificationCode | None:
        codes = [c for c in self._codes.values() if c.user_id == user_id]
        return replace(max(codes, key=lambda c: c.id)) if codes else None

    def mark_code_used(self, code_id: int) -> None:
        self._codes[code_id].used = True

    def mark_verified(self, user_id: int) -> None:
        self.get(user_id)
        self._users[user_id].is_verified = True

    def record_wrong_code(self, code_id: int) -> None:
        self._codes[code_id].attempts += 1

    def get_login_failures(self, user_id: int) -> tuple[int, datetime | None]:
        self.get(user_id)
        return self._login_failures.get(user_id, (0, None))

    def set_login_failures(self, user_id: int, failures: int, paused_until: datetime | None) -> None:
        self.get(user_id)
        self._login_failures[user_id] = (failures, paused_until)

    def get_session_version(self, user_id: int) -> int:
        self.get(user_id)
        return self._session_versions.get(user_id, 0)

    def next_session_version(self, user_id: int) -> None:
        self._session_versions[user_id] = self.get_session_version(user_id) + 1


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

    @staticmethod
    def _code(row: VerificationCodeRow) -> VerificationCode:
        return VerificationCode(
            id=row.id,
            user_id=row.user_id,
            code_hash=row.code_hash,
            expires_at=_from_db(row.expires_at),
            used=row.used,
            attempts=row.attempts,
        )

    def _row(self, user_id: int) -> UserRow:
        row = self.session.get(UserRow, user_id)
        if row is None:
            raise NotFoundError(f"User {user_id} does not exist")
        return row

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
        return self._user(self._row(user_id))

    def find_by_email(self, email: str) -> User | None:
        # lower(email) = lower(:email) lets PostgreSQL use the unique index ux_user_email_lower
        row = self.session.scalars(
            select(UserRow).where(func.lower(UserRow.email) == email.strip().lower())
        ).one_or_none()
        return self._user(row) if row is not None else None

    def get_password_hash(self, user_id: int) -> str:
        return self._row(user_id).password_hash

    def save_code(self, user_id: int, code_hash: str, expires_at: datetime) -> VerificationCode:
        row = VerificationCodeRow(user_id=user_id, code_hash=code_hash, expires_at=_to_db(expires_at), used=False)
        self.session.add(row)
        self.session.flush()  # gives row.id
        return self._code(row)

    def get_latest_code(self, user_id: int) -> VerificationCode | None:
        row = self.session.scalars(
            select(VerificationCodeRow)
            .where(VerificationCodeRow.user_id == user_id)
            .order_by(VerificationCodeRow.id.desc())
            .limit(1)
        ).one_or_none()
        return self._code(row) if row is not None else None

    def mark_code_used(self, code_id: int) -> None:
        self.session.execute(update(VerificationCodeRow).where(VerificationCodeRow.id == code_id).values(used=True))

    def mark_verified(self, user_id: int) -> None:
        self._row(user_id).is_verified = True
        self.session.flush()

    def record_wrong_code(self, code_id: int) -> None:
        # attempts = attempts + 1 in the database, so two wrong codes at the same moment both count
        self.session.execute(
            update(VerificationCodeRow)
            .where(VerificationCodeRow.id == code_id)
            .values(attempts=VerificationCodeRow.attempts + 1)
        )

    def get_login_failures(self, user_id: int) -> tuple[int, datetime | None]:
        row = self.session.execute(
            select(UserRow.failed_logins, UserRow.login_paused_until).where(UserRow.id == user_id).with_for_update()
        ).one_or_none()
        if row is None:
            raise NotFoundError(f"User {user_id} does not exist")
        failures, paused_until = row
        return failures, (_from_db(paused_until) if paused_until is not None else None)

    def set_login_failures(self, user_id: int, failures: int, paused_until: datetime | None) -> None:
        self.session.execute(
            update(UserRow)
            .where(UserRow.id == user_id)
            .values(failed_logins=failures, login_paused_until=_to_db(paused_until) if paused_until else None)
        )

    def get_session_version(self, user_id: int) -> int:
        version = self.session.scalar(select(UserRow.session_version).where(UserRow.id == user_id))
        if version is None:
            raise NotFoundError(f"User {user_id} does not exist")
        return version

    def next_session_version(self, user_id: int) -> None:
        self.session.execute(
            update(UserRow).where(UserRow.id == user_id).values(session_version=UserRow.session_version + 1)
        )


def _constraint(error: IntegrityError) -> str | None:
    diag = getattr(error.orig, "diag", None)
    return getattr(diag, "constraint_name", None)
