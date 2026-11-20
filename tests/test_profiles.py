"""Unit tests of ProfileService (UC-03 Manage profile, BR-14, NFR-04).

The users are put straight into the in-memory repository, so these tests do not depend on register.
"""

from datetime import datetime

import pytest

from campusevent.auth import AuthService
from campusevent.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from campusevent.models import Profile, Role, TimeSlot, User
from campusevent.notifications import InMemoryEmailSender
from campusevent.profiles import ProfileService
from campusevent.repositories.profile_repository import InMemoryProfileRepository
from campusevent.repositories.unit_of_work import InMemoryUnitOfWork
from campusevent.repositories.user_repository import InMemoryUserRepository


def at(day, hour, hours=1):
    start = datetime(2026, 11, day, hour)
    return TimeSlot(start, start.replace(hour=hour + hours))


@pytest.fixture
def users():
    return InMemoryUserRepository()


@pytest.fixture
def uow():
    return InMemoryUnitOfWork()


@pytest.fixture
def profiles(users, uow):
    auth = AuthService(("bilgiedu.net", "bilgi.edu.tr"), InMemoryEmailSender(), users)
    return ProfileService(auth, InMemoryProfileRepository(), uow)


def add(users, email, role=Role.STUDENT):
    return users.add(User(0, email, email.split("@")[0].title(), role, True), "argon2-hash")


@pytest.fixture
def deniz(users):
    return add(users, "deniz@bilgiedu.net")


def test_new_student_has_an_empty_profile(profiles, deniz):
    assert profiles.get_profile(deniz.id) == Profile(deniz.id, [], [])


def test_interests_are_trimmed_lower_cased_and_kept_once(profiles, deniz):
    saved = profiles.update_profile(
        deniz.id, ["  Football ", "Board   Games", "football", "", "   ", "BOARD GAMES", "Chess"], []
    )

    assert saved.interests == ["football", "board games", "chess"]
    assert profiles.get_profile(deniz.id).interests == ["football", "board games", "chess"]


def test_turkish_capital_i_becomes_a_plain_i(profiles, deniz):
    saved = profiles.update_profile(deniz.id, ["İngilizce kulübü", "ingilizce kulübü", "İSTANBUL"], [])

    assert saved.interests == ["ingilizce kulübü", "istanbul"]
    assert "̇" not in "".join(saved.interests)  # no combining dot


@pytest.mark.parametrize("interests", [[], ["", "   "], None])
def test_at_least_one_interest_is_needed(profiles, deniz, interests):
    with pytest.raises(ValidationError, match="Add at least one interest"):
        profiles.update_profile(deniz.id, interests, [])


def test_interest_can_be_60_characters_long_but_not_more(profiles, deniz):
    assert profiles.update_profile(deniz.id, ["x" * 60], []).interests == ["x" * 60]

    with pytest.raises(ValidationError, match="at most 60"):
        profiles.update_profile(deniz.id, ["x" * 61], [])


def test_slot_must_end_after_it_starts(profiles, deniz):
    start = datetime(2026, 11, 3, 17)

    for bad in [TimeSlot(start, start), TimeSlot(start, start.replace(hour=16))]:
        with pytest.raises(ValidationError, match="end time must be after the start time"):
            profiles.update_profile(deniz.id, ["football"], [at(3, 10), bad])


def test_slots_are_returned_by_start_time_and_repeats_are_dropped(profiles, deniz):
    saved = profiles.update_profile(deniz.id, ["football"], [at(4, 18), at(3, 17, 2), at(4, 18)])

    assert saved.availability == [at(3, 17, 2), at(4, 18)]


def test_saving_replaces_the_old_profile(profiles, deniz):
    profiles.update_profile(deniz.id, ["football", "chess"], [at(3, 17)])

    profiles.update_profile(deniz.id, ["tennis"], [])

    assert profiles.get_profile(deniz.id) == Profile(deniz.id, ["tennis"], [])


def test_invalid_change_keeps_the_saved_profile(profiles, deniz):
    profiles.update_profile(deniz.id, ["football"], [at(3, 17)])

    with pytest.raises(ValidationError):
        profiles.update_profile(deniz.id, [], [at(5, 10)])

    assert profiles.get_profile(deniz.id) == Profile(deniz.id, ["football"], [at(3, 17)])


def test_save_runs_in_one_transaction(profiles, deniz, uow):
    profiles.update_profile(deniz.id, ["football"], [])

    assert (uow.commits, uow.rollbacks, uow.active) == (1, 0, False)


def test_profile_of_one_student_does_not_change_another(profiles, users, deniz):
    can = add(users, "can@bilgiedu.net")
    profiles.update_profile(deniz.id, ["football"], [at(3, 17)])

    assert profiles.get_profile(can.id) == Profile(can.id, [], [])


def test_returned_profile_is_a_copy(profiles, deniz):
    profiles.update_profile(deniz.id, ["football"], [])

    profiles.get_profile(deniz.id).interests.append("hacked")

    assert profiles.get_profile(deniz.id).interests == ["football"]


@pytest.mark.parametrize("role", [Role.FACILITY_STAFF, Role.ADMIN])
def test_only_students_can_change_a_profile(profiles, users, role):
    other = add(users, f"{role.value}@bilgi.edu.tr", role)

    with pytest.raises(PermissionDeniedError, match="Only students"):
        profiles.update_profile(other.id, ["football"], [])


def test_unknown_user_has_no_profile(profiles):
    with pytest.raises(NotFoundError):
        profiles.get_profile(99)
    with pytest.raises(NotFoundError):
        profiles.update_profile(99, ["football"], [])
