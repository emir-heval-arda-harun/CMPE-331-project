"""Errors raised by CampusEvent services."""


class CampusEventError(Exception):
    """Base class for all domain errors."""


class InvalidEmailDomainError(CampusEventError):
    """The e-mail address does not belong to the university domain."""


class DuplicateEmailError(CampusEventError):
    """An account with this e-mail address already exists."""


class InvalidVerificationCodeError(CampusEventError):
    """The e-mail verification code is wrong or expired."""


class AuthenticationError(CampusEventError):
    """Wrong e-mail/password combination."""


class TooManyAttemptsError(AuthenticationError):
    """Too many wrong passwords for this account in a row: logging in is paused for a while (pentest P1)."""


class EmailNotVerifiedError(CampusEventError):
    """The user tried to log in before verifying their e-mail address."""


class ValidationError(CampusEventError):
    """Input data is missing or invalid."""


class PermissionDeniedError(CampusEventError):
    """The user's role does not allow this action."""


class NotFoundError(CampusEventError):
    """The requested entity does not exist."""


class FacilityConflictError(CampusEventError):
    """The facility is not available in the requested time slot."""


class EventFullError(CampusEventError):
    """The event has no free places left."""


class AlreadyJoinedError(CampusEventError):
    """The user is already a participant of the event."""


class EmailDeliveryError(CampusEventError):
    """The mail server could not be reached or refused the e-mail."""
