"""Outgoing e-mail abstraction."""

from __future__ import annotations

from typing import Protocol


class EmailSender(Protocol):
    def send_verification_code(self, email: str, code: str) -> None: ...

    def send_event_decision(self, email: str, event_title: str, approved: bool, reason: str = "") -> None: ...


class InMemoryEmailSender:
    """Keeps sent verification codes in memory (used in development and tests)."""

    def __init__(self) -> None:
        self.codes: dict[str, str] = {}
        self.decisions: list[tuple[str, str, bool, str]] = []  # (email, title, approved, reason)

    def send_verification_code(self, email: str, code: str) -> None:
        self.codes[email] = code

    def send_event_decision(self, email: str, event_title: str, approved: bool, reason: str = "") -> None:
        self.decisions.append((email, event_title, approved, reason))
