"""PasswordHasher: hashing of passwords and verification codes (layer 3, NFR-03, BR-02).

The services only see the ``PasswordHasher`` interface. ``Argon2PasswordHasher`` is the implementation
of the Software Design Report (section 2 and 4.3): argon2id with a new random salt for every hash, so
the same password gives a different stored value for every user.
"""

from __future__ import annotations

from typing import Protocol

from argon2 import PasswordHasher as _Argon2
from argon2.exceptions import InvalidHashError, VerificationError


class PasswordHasher(Protocol):
    def hash(self, secret: str) -> str:
        """A salted hash of a password or a verification code; the secret itself is never stored."""
        ...

    def verify(self, secret_hash: str, secret: str) -> bool:
        """True if ``secret`` matches the hash, False otherwise (also for a damaged hash)."""
        ...


class Argon2PasswordHasher:
    """argon2id from argon2-cffi. Without arguments it uses the library's recommended cost settings.

    Smaller settings (``time_cost``, ``memory_cost``, ``parallelism``) are only for the tests, which hash
    hundreds of passwords; the hashes are still salted argon2id hashes.
    """

    def __init__(self, **cost) -> None:
        self._argon2 = _Argon2(**cost)

    def hash(self, secret: str) -> str:
        return self._argon2.hash(secret)

    def verify(self, secret_hash: str, secret: str) -> bool:
        try:
            return self._argon2.verify(secret_hash, secret)
        except (VerificationError, InvalidHashError):  # wrong secret, or not an argon2 hash at all
            return False
