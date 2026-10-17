"""Non-functional requirement tests (NFR-02, NFR-03, NFR-04).

NFR-01 (responsive UI), NFR-05 (privacy), NFR-06 (single test command) and NFR-07
(browser portability) cannot be checked by unit tests; see docs/requirements/README.md
for how they are verified.

Like the use case tests, these call the services inside the test body so that a
missing feature makes the test FAIL instead of ERROR.
"""

import time

import pytest

from campusevent.exceptions import PermissionDeniedError
from campusevent.models import Role
from tests.helpers import PASSWORD, campus_hall, slot, verified_user


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _leaves(obj, seen=None):
    """Yield every str/bytes value stored anywhere inside an object graph."""
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return
    seen.add(id(obj))
    if isinstance(obj, (str, bytes, bytearray)):
        yield obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield from _leaves(key, seen)
            yield from _leaves(value, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for value in obj:
            yield from _leaves(value, seen)
    elif hasattr(obj, "__dict__"):
        yield from _leaves(vars(obj), seen)


def _stored_text(app):
    """All text kept by the auth service (the e-mail sender is not part of the storage)."""
    storage = {k: v for k, v in vars(app.auth).items() if k != "email_sender"}
    for leaf in _leaves(storage):
        yield leaf.decode(errors="ignore") if isinstance(leaf, (bytes, bytearray)) else leaf


def _long_values(app, email_sender):
    """Stored values that are long enough to be a password hash or a salt."""
    codes = set(email_sender.codes.values())
    return {t for t in _stored_text(app) if len(t) >= 32 and t not in codes}


# --------------------------------------------------------------------------- #
# NFR-02 Performance: event search < 2 s for 1,000 open events
# --------------------------------------------------------------------------- #
def test_nfr02_search_is_fast_with_1000_open_events(app, email_sender):
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    for f in range(10):
        hall = app.facilities.add_facility(staff.id, f"Hall {f}", 500)
        organizer = verified_user(app, email_sender, f"organizer{f}@bilgiedu.net")
        for i in range(100):
            app.events.create_event(
                organizer.id, f"Event {f}-{i}", "social", hall.id, slot(day=1 + i // 24, hour=i % 24), 10
            )

    started = time.perf_counter()
    result = app.events.search_events(category="social")
    elapsed = time.perf_counter() - started

    assert len(result) == 1000
    assert elapsed < 2.0


# --------------------------------------------------------------------------- #
# NFR-03 Security: passwords are stored only as salted hashes
# --------------------------------------------------------------------------- #
def test_nfr03_password_is_never_stored_in_plain_text(app, email_sender):
    verified_user(app, email_sender, "ayse@bilgiedu.net")

    assert not any(PASSWORD in text for text in _stored_text(app))


def test_nfr03_same_password_gives_different_stored_values(app, email_sender):
    verified_user(app, email_sender, "ayse@bilgiedu.net")
    after_first = _long_values(app, email_sender)
    verified_user(app, email_sender, "mehmet@bilgiedu.net")
    after_second = _long_values(app, email_sender)

    assert after_first, "no password hash was found in the stored data"
    assert after_second - after_first, "two users with the same password got the same stored value (no salt)"


# --------------------------------------------------------------------------- #
# NFR-04 Security: role-based access
# --------------------------------------------------------------------------- #
def test_nfr04_student_cannot_manage_facilities(app, email_sender):
    student = verified_user(app, email_sender, "baris@bilgiedu.net")

    with pytest.raises(PermissionDeniedError):
        app.facilities.add_facility(student.id, "Fake Hall", 20)


def test_nfr04_student_cannot_block_a_facility(app, email_sender):
    staff = verified_user(app, email_sender, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    student = verified_user(app, email_sender, "baris@bilgiedu.net")
    hall = app.facilities.add_facility(staff.id, "Santral Event Hall", 50)

    with pytest.raises(PermissionDeniedError):
        app.facilities.add_block(student.id, hall.id, slot(hour=9, hours=3), "Fake class")


def test_nfr04_only_the_organizer_can_cancel_an_event(app, email_sender):
    organizer = verified_user(app, email_sender, "ali@bilgiedu.net")
    other = verified_user(app, email_sender, "kerem@bilgiedu.net")
    hall = campus_hall(app, email_sender)
    event = app.events.create_event(organizer.id, "Game night", "board games", hall.id, slot(), 6)

    with pytest.raises(PermissionDeniedError):
        app.events.cancel_event(event.id, other.id)
