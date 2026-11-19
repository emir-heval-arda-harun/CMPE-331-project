"""Unit tests of AuthService.get_user and require_role (task 3.2, NFR-04).

register and verify_email are not written yet, so the users are put straight into the in-memory
repository. FacilityService is used as a real caller of require_role (BR-09).
"""

import pytest

from campusevent.auth import AuthService
from campusevent.exceptions import NotFoundError, PermissionDeniedError
from campusevent.facilities import FacilityService
from campusevent.models import Role, User
from campusevent.notifications import InMemoryEmailSender
from campusevent.repositories.user_repository import InMemoryUserRepository


@pytest.fixture
def users():
    return InMemoryUserRepository()


@pytest.fixture
def auth(users):
    return AuthService(("bilgiedu.net", "bilgi.edu.tr"), InMemoryEmailSender(), users)


def add(users, email, role=Role.STUDENT):
    return users.add(User(0, email, email.split("@")[0].title(), role, True), "argon2-hash")


def test_repository_gives_new_ids_and_keeps_the_fields(users):
    ali = add(users, "ali@bilgiedu.net")
    staff = add(users, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)

    assert (ali.id, staff.id) == (1, 2)
    assert users.get(staff.id) == User(2, "staff@bilgi.edu.tr", "Staff", Role.FACILITY_STAFF, True)


def test_get_user_returns_the_user_and_rejects_an_unknown_id(auth, users):
    ali = add(users, "ali@bilgiedu.net")

    assert auth.get_user(ali.id) == ali
    with pytest.raises(NotFoundError):
        auth.get_user(99)


@pytest.mark.parametrize("role", list(Role))
def test_require_role_returns_the_user_with_that_role(auth, users, role):
    user = add(users, f"{role.value}@bilgi.edu.tr", role)

    assert auth.require_role(user.id, role) == user


@pytest.mark.parametrize("role", list(Role))
def test_require_role_refuses_every_other_role(auth, users, role):
    others = [add(users, f"{other.value}@bilgi.edu.tr", other) for other in Role if other is not role]

    for user in others:
        with pytest.raises(PermissionDeniedError):
            auth.require_role(user.id, role)


def test_require_role_names_the_needed_role(auth, users):
    student = add(users, "ali@bilgiedu.net")

    with pytest.raises(PermissionDeniedError, match="Only facility staff"):
        auth.require_role(student.id, Role.FACILITY_STAFF)
    with pytest.raises(PermissionDeniedError, match="Only admins"):
        auth.require_role(student.id, Role.ADMIN)


def test_require_role_rejects_an_unknown_user(auth):
    with pytest.raises(NotFoundError):
        auth.require_role(99, Role.ADMIN)


def test_auth_service_without_repository_starts_empty():
    auth = AuthService(("bilgiedu.net",), InMemoryEmailSender())

    with pytest.raises(NotFoundError):
        auth.get_user(1)


def test_facility_service_uses_the_real_role_check(auth, users):
    """BR-09 with the real AuthService instead of a stand-in."""
    staff = add(users, "staff@bilgi.edu.tr", Role.FACILITY_STAFF)
    student = add(users, "ali@bilgiedu.net")
    facilities = FacilityService(auth)

    hall = facilities.add_facility(staff.id, "Santral Event Hall", 50)

    assert facilities.get_facility(hall.id) == hall
    with pytest.raises(PermissionDeniedError):
        facilities.add_facility(student.id, "Fake Hall", 20)
