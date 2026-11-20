"""Outgoing e-mail (layer 3: data access and integration).

``SmtpEmailSender`` is used in production (SMTP with STARTTLS, Software Design Report 3.2);
``InMemoryEmailSender`` keeps the e-mails in memory for the tests and development.
"""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from typing import Protocol

from campusevent.exceptions import EmailDeliveryError


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


class SmtpEmailSender:
    """Sends e-mails through an SMTP server, for example Gmail with an app password or a mail provider.

    Port 465 uses SMTP over TLS; every other port (normally 587) starts with plain SMTP and switches to
    TLS with STARTTLS before logging in. The server's certificate is checked. A failure becomes an
    ``EmailDeliveryError``, which the web pages show as a message.
    """

    def __init__(self, host: str, port: int = 587, username: str = "", password: str = "", sender: str = "",
                 timeout: float = 10) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender or username
        self.timeout = timeout

    def send_verification_code(self, email: str, code: str) -> None:
        self._send(
            email,
            f"Your CampusEvent verification code: {code}",
            f"Your CampusEvent verification code is {code}\n\n"
            "Enter it on the verification page to activate your account. It is valid for 15 minutes.\n"
            "If you did not sign up for CampusEvent, you can ignore this e-mail.\n",
        )

    def send_event_decision(self, email: str, event_title: str, approved: bool, reason: str = "") -> None:
        if approved:
            subject = f"Your event request was approved: {event_title}"
            body = f'Your event request "{event_title}" was approved. It is now listed on CampusEvent.\n'
        else:
            subject = f"Your event request was rejected: {event_title}"
            body = f'Your event request "{event_title}" was rejected.\n\nReason: {reason or "-"}\n'
        self._send(email, subject, body)

    def _send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        context = ssl.create_default_context()
        try:
            if self.port == 465:
                smtp = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout, context=context)
            else:
                smtp = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            with smtp:
                if self.port != 465:
                    smtp.starttls(context=context)
                if self.username:
                    smtp.login(self.username, self.password)
                smtp.send_message(message)
        except (smtplib.SMTPException, OSError) as error:  # OSError: no connection, timeout, TLS failure
            raise EmailDeliveryError("We could not send the e-mail. Please try again in a few minutes.") from error
