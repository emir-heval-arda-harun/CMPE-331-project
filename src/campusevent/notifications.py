"""Outgoing e-mail abstraction."""

from __future__ import annotations

from typing import Protocol


class EmailSender(Protocol):
    def send_verification_code(self, email: str, code: str) -> None: ...


class InMemoryEmailSender:
    """Keeps sent verification codes in memory (used in development and tests)."""

    def __init__(self) -> None:
        self.codes: dict[str, str] = {}

    def send_verification_code(self, email: str, code: str) -> None:
        self.codes[email] = code
