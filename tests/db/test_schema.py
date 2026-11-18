"""Database tests for task 3.1: the tables, constraints and indexes of the migrations.

They run only when TEST_DATABASE_URL is set (see tests/db/conftest.py); otherwise they are skipped.
Each test stores rows straight with SQL, so it checks the database rules themselves, without the
services: wrong rows must be refused by the expected constraint, valid rows must be accepted.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from psycopg import errors
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from campusevent.repositories.tables import Base

TABLES = {
    "user",
    "verification_code",
    "profile_interest",
    "availability_slot",
    "facility",
    "facility_block",
    "event",
    "event_participant",
}


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 12, 1, hour, minute, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# Helpers: insert rows with plain SQL and return their id
# --------------------------------------------------------------------------- #
def insert(db, table: str, **values) -> int | None:
    names = ", ".join(values)
    params = ", ".join(f":{name}" for name in values)
    return db.execute(text(f'INSERT INTO "{table}" ({names}) VALUES ({params}) RETURNING *'), values).first()[0]


def add_user(db, email: str = "ayse@bilgiedu.net", role: str = "student") -> int:
    return insert(db, "user", email=email, full_name="Test User", password_hash="argon2-hash", role=role)


def add_facility(db, name: str = "Santral Event Hall", capacity: int = 50) -> int:
    manager = add_user(db, f"staff.{uuid4().hex[:8]}@bilgi.edu.tr", "facility_staff")
    return insert(db, "facility", manager_id=manager, name=name, capacity=capacity)


def add_event(db, facility_id: int, organizer_id: int, start: datetime, end: datetime, **values) -> int:
    row = {"title": "Game night", "category": "board games", "capacity": 6} | values
    return insert(
        db, "event", organizer_id=organizer_id, facility_id=facility_id, start_time=start, end_time=end, **row
    )


@contextmanager
def refused_by(db, constraint: str, error: type[Exception]):
    """Expect PostgreSQL to refuse the statement in the block because of ``constraint``.

    The statement runs inside a SAVEPOINT, so the test can go on using the connection afterwards.
    """
    savepoint = db.begin_nested()
    with pytest.raises(IntegrityError) as caught:
        yield
    savepoint.rollback()
    assert isinstance(caught.value.orig, error), f"expected {error.__name__}, got {type(caught.value.orig).__name__}"
    assert caught.value.orig.diag.constraint_name == constraint


@pytest.fixture
def hall(db) -> int:
    return add_facility(db)


@pytest.fixture
def student(db) -> int:
    return add_user(db)


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #
def test_migration_creates_the_eight_tables_and_btree_gist(db):
    assert TABLES <= set(inspect(db).get_table_names())
    assert db.scalar(text("SELECT count(*) FROM pg_extension WHERE extname = 'btree_gist'")) == 1


def test_tables_py_matches_the_migrations(db):
    """If this fails, tables.py and migrations/versions/ describe different tables: write a migration."""
    context = MigrationContext.configure(db, opts={"compare_type": True})
    assert compare_metadata(context, Base.metadata) == []


def test_migration_can_be_undone_and_done_again(engine, alembic_config):
    command.downgrade(alembic_config, "base")
    with engine.connect() as connection:
        assert not TABLES & set(inspect(connection).get_table_names())
    command.upgrade(alembic_config, "head")
    with engine.connect() as connection:
        assert TABLES <= set(inspect(connection).get_table_names())


def test_indexes_of_the_design_report_exist(db):
    indexes = dict(db.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'")).all())

    assert "lower" in indexes["ux_user_email_lower"] and "UNIQUE" in indexes["ux_user_email_lower"]
    assert "(category, start_time)" in indexes["ix_event_category_start_time"]
    assert "(facility_id, start_time)" in indexes["ix_event_facility_id_start_time"]
    assert "WHERE" in indexes["ix_event_pending_start_time"] and "pending" in indexes["ix_event_pending_start_time"]
    assert "gist" in indexes["ex_event_facility_no_overlap"]


# --------------------------------------------------------------------------- #
# user
# --------------------------------------------------------------------------- #
def test_email_is_unique_without_regard_to_case(db):
    add_user(db, "ayse@bilgiedu.net")

    with refused_by(db, "ux_user_email_lower", errors.UniqueViolation):
        add_user(db, "AYSE@BilgiEdu.net")


def test_role_must_be_student_facility_staff_or_admin(db):
    add_user(db, "admin@bilgi.edu.tr", "admin")  # CR-01

    with refused_by(db, "ck_user_role_valid", errors.CheckViolation):
        add_user(db, "boss@bilgi.edu.tr", "superuser")


def test_new_user_is_an_unverified_student(db):
    user_id = insert(db, "user", email="can@bilgiedu.net", full_name="Can", password_hash="argon2-hash")

    row = db.execute(text('SELECT role, is_verified FROM "user" WHERE id = :id'), {"id": user_id}).one()
    assert tuple(row) == ("student", False)


# --------------------------------------------------------------------------- #
# event: status and review fields (CR-01)
# --------------------------------------------------------------------------- #
def test_new_event_is_pending_without_review(db, hall, student):
    event_id = add_event(db, hall, student, at(18), at(20))

    row = db.execute(
        text("SELECT status, reviewed_by, reviewed_at, rejection_reason, description FROM event WHERE id = :id"),
        {"id": event_id},
    ).one()
    assert tuple(row) == ("pending", None, None, "", "")


@pytest.mark.parametrize("reason", ["", "   "])
def test_rejected_event_needs_a_reason(db, hall, student, reason):
    with refused_by(db, "ck_event_rejected_has_reason", errors.CheckViolation):
        add_event(db, hall, student, at(18), at(20), status="rejected", rejection_reason=reason)


def test_pending_event_cannot_be_rejected_without_a_reason(db, hall, student):
    event_id = add_event(db, hall, student, at(18), at(20))

    with refused_by(db, "ck_event_rejected_has_reason", errors.CheckViolation):
        db.execute(text("UPDATE event SET status = 'rejected' WHERE id = :id"), {"id": event_id})
    db.execute(
        text("UPDATE event SET status = 'rejected', rejection_reason = 'Exams week' WHERE id = :id"), {"id": event_id}
    )


@pytest.mark.parametrize(
    ("values", "constraint"),
    [
        ({"capacity": 1}, "ck_event_capacity_min"),
        ({"title": "  "}, "ck_event_title_not_empty"),
        ({"category": "Football "}, "ck_event_category_normalized"),
        ({"status": "draft"}, "ck_event_status_valid"),
    ],
)
def test_wrong_event_values_are_refused(db, hall, student, values, constraint):
    with refused_by(db, constraint, errors.CheckViolation):
        add_event(db, hall, student, at(18), at(20), **values)


def test_event_must_end_after_it_starts(db, hall, student):
    with refused_by(db, "ck_event_end_after_start", errors.CheckViolation):
        add_event(db, hall, student, at(20), at(20))


def test_event_needs_an_existing_facility(db, student):
    with refused_by(db, "fk_event_facility_id_facility", errors.ForeignKeyViolation):
        add_event(db, 999_999, student, at(18), at(20))


# --------------------------------------------------------------------------- #
# event: no double booking of a facility (BR-06, BR-16)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("taken_by", ["pending", "open", "full"])
def test_active_events_cannot_overlap_in_one_facility(db, hall, student, taken_by):
    add_event(db, hall, student, at(18), at(20), status=taken_by)

    with refused_by(db, "ex_event_facility_no_overlap", errors.ExclusionViolation):
        add_event(db, hall, student, at(19), at(21))


@pytest.mark.parametrize("status", ["rejected", "cancelled", "completed"])
def test_inactive_events_free_the_slot(db, hall, student, status):
    add_event(db, hall, student, at(18), at(20), status=status, rejection_reason="Not allowed")

    add_event(db, hall, student, at(18), at(20))  # no error


def test_back_to_back_events_and_other_facilities_are_allowed(db, hall, student):
    court = add_facility(db, "Main Court", 20)
    add_event(db, hall, student, at(18), at(20))

    add_event(db, hall, student, at(20), at(22))  # starts when the first one ends
    add_event(db, court, student, at(18), at(20))  # same time, other facility


def test_cancelled_event_cannot_come_back_into_a_taken_slot(db, hall, student):
    cancelled = add_event(db, hall, student, at(18), at(20), status="cancelled")
    add_event(db, hall, student, at(18), at(20))  # the freed slot is taken by a new request

    with refused_by(db, "ex_event_facility_no_overlap", errors.ExclusionViolation):
        db.execute(text("UPDATE event SET status = 'open' WHERE id = :id"), {"id": cancelled})


# --------------------------------------------------------------------------- #
# event_participant, facility, facility_block, profile_interest
# --------------------------------------------------------------------------- #
def test_user_joins_an_event_only_once(db, hall, student):
    event_id = add_event(db, hall, student, at(18), at(20))
    insert(db, "event_participant", event_id=event_id, user_id=student)

    with refused_by(db, "pk_event_participant", errors.UniqueViolation):
        insert(db, "event_participant", event_id=event_id, user_id=student)


def test_facility_name_is_unique_and_capacity_at_least_two(db, hall):
    with refused_by(db, "uq_facility_name", errors.UniqueViolation):
        add_facility(db, "Santral Event Hall", 30)
    with refused_by(db, "ck_facility_capacity_min", errors.CheckViolation):
        add_facility(db, "Phone Booth", 1)


def test_blocks_of_one_facility_cannot_overlap(db, hall):
    staff = add_user(db, "staff@bilgi.edu.tr", "facility_staff")

    def block(start: datetime, end: datetime) -> None:
        insert(db, "facility_block", facility_id=hall, created_by=staff, start_time=start, end_time=end, reason="Class")

    block(at(9), at(12))
    with refused_by(db, "ex_facility_block_no_overlap", errors.ExclusionViolation):
        block(at(11), at(13))
    block(at(12), at(13))  # starts when the first block ends


def test_interests_are_stored_trimmed_and_in_lower_case(db, student):
    insert(db, "profile_interest", user_id=student, interest="board games")

    with refused_by(db, "ck_profile_interest_interest_normalized", errors.CheckViolation):
        insert(db, "profile_interest", user_id=student, interest=" Football")
    with refused_by(db, "pk_profile_interest", errors.UniqueViolation):
        insert(db, "profile_interest", user_id=student, interest="board games")


def test_deleting_a_user_deletes_their_profile_rows(db, student):
    insert(db, "profile_interest", user_id=student, interest="chess")
    insert(db, "availability_slot", user_id=student, start_time=at(17), end_time=at(19))

    db.execute(text('DELETE FROM "user" WHERE id = :id'), {"id": student})

    assert db.scalar(text("SELECT count(*) FROM profile_interest WHERE user_id = :id"), {"id": student}) == 0
    assert db.scalar(text("SELECT count(*) FROM availability_slot WHERE user_id = :id"), {"id": student}) == 0


def test_times_are_stored_in_utc(db, hall, student):
    istanbul = timezone(timedelta(hours=3))
    event_id = add_event(db, hall, student, datetime(2026, 12, 1, 18, tzinfo=istanbul), at(17))

    start = db.scalar(text("SELECT start_time FROM event WHERE id = :id"), {"id": event_id})
    assert start == at(15) and start.utcoffset() == timedelta(0)
