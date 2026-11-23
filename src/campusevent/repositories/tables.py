"""SQLAlchemy table mappings (layer 3: data access and integration).

One class per table of the Software Design Report, section 6, with the changes of CR-01.
The classes end in ``Row`` so they are not confused with the domain classes of
``campusevent.models`` (``User``, ``Event``, ...). Only the data access layer uses them: the
``Sql*Repository`` classes turn rows into domain objects and back, so the services never see
SQLAlchemy.

Schema changes are made only through Alembic migrations (``migrations/versions/``). When you
change a class here, write a migration that makes the same change (see docs/database/README.md);
``tests/db/test_schema.py`` fails when the two do not match.

All times are ``timestamptz`` (stored in UTC, see ``campusevent.repositories.db``).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from campusevent.models import EventStatus, Role

# Fixed names for keys and constraints, so that later migrations can find them by name
# (for example ck_event_capacity_min, fk_event_facility_id_facility, uq_facility_name).
NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
}

ROLES = tuple(role.value for role in Role)
EVENT_STATUSES = tuple(status.value for status in EventStatus)
# Events that occupy their facility slot (BR-06, BR-16). Use this tuple in active_on() queries.
ACTIVE_EVENT_STATUSES = (EventStatus.PENDING.value, EventStatus.OPEN.value, EventStatus.FULL.value)


def _one_of(column: str, values: tuple[str, ...]) -> str:
    """SQL text ``column IN ('a', 'b')`` for a CHECK constraint or a partial index."""
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UserRow(Base):
    # "user" is a reserved word in PostgreSQL. SQLAlchemy quotes it for you; in psql write "user".
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(_one_of("role", ROLES), name="role_valid"),
        CheckConstraint("btrim(email) <> ''", name="email_not_empty"),
        CheckConstraint("btrim(full_name) <> ''", name="full_name_not_empty"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    # Unique without regard to case: see ux_user_email_lower below. Look users up with
    # lower(email) = lower(:email) so PostgreSQL can use that index.
    email: Mapped[str] = mapped_column(String(254))
    full_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))  # argon2id hash, never the password (BR-02)
    role: Mapped[str] = mapped_column(String(20), server_default=Role.STUDENT.value)
    is_verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    # Wrong passwords in a row and the end of the pause they caused (pentest P1, migration 0002).
    failed_logins: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    login_paused_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Part of every session token; log out adds 1, so every copy of an older token stops working (pentest P3).
    session_version: Mapped[int] = mapped_column(Integer, server_default=text("0"))

    interests: Mapped[list[ProfileInterestRow]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, order_by="ProfileInterestRow.interest"
    )
    availability: Mapped[list[AvailabilitySlotRow]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, order_by="AvailabilitySlotRow.start_time"
    )


class VerificationCodeRow(Base):
    __tablename__ = "verification_code"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(255))  # the code itself is only in the e-mail
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # 15 minutes after sending
    used: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    attempts: Mapped[int] = mapped_column(Integer, server_default=text("0"))  # wrong codes typed (pentest P2, #30)


class ProfileInterestRow(Base):
    __tablename__ = "profile_interest"
    __table_args__ = (
        # BR-14: interests are stored trimmed and in lower case, so "Football " and "football" are one interest.
        CheckConstraint("interest <> '' AND interest = lower(btrim(interest))", name="interest_normalized"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    interest: Mapped[str] = mapped_column(String(60), primary_key=True)  # the profile form allows 60 characters


class AvailabilitySlotRow(Base):
    __tablename__ = "availability_slot"
    __table_args__ = (CheckConstraint("end_time > start_time", name="end_after_start"),)  # UC-03 alt. 5b

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FacilityRow(Base):
    __tablename__ = "facility"
    __table_args__ = (
        CheckConstraint("capacity >= 2", name="capacity_min"),  # UC-08 alt. 1b
        CheckConstraint("btrim(name) <> ''", name="name_not_empty"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    # Must be a facility staff user. A CHECK cannot look at another table, so FacilityService checks the role.
    manager_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    name: Mapped[str] = mapped_column(String(100), unique=True)
    capacity: Mapped[int] = mapped_column(Integer)

    blocks: Mapped[list[FacilityBlockRow]] = relationship(
        passive_deletes=True, order_by="FacilityBlockRow.start_time"
    )


class FacilityBlockRow(Base):
    __tablename__ = "facility_block"
    __table_args__ = (CheckConstraint("end_time > start_time", name="end_after_start"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facility.id", ondelete="CASCADE"))
    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"))  # the facility staff member
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(200))


class EventRow(Base):
    __tablename__ = "event"
    __table_args__ = (
        CheckConstraint("btrim(title) <> ''", name="title_not_empty"),  # UC-04 alt. 1a
        # BR-14: categories are stored trimmed and in lower case.
        CheckConstraint("category <> '' AND category = lower(btrim(category))", name="category_normalized"),
        # BR-04. "At most the facility capacity" needs the facility row, so FacilityService checks it.
        CheckConstraint("capacity >= 2", name="capacity_min"),
        CheckConstraint("end_time > start_time", name="end_after_start"),
        CheckConstraint(_one_of("status", EVENT_STATUSES), name="status_valid"),
        # BR-17 (CR-01): a rejected event always has a reason. This also covers the automatic
        # rejection of BR-18, so expire_pending_requests() must store a reason as well.
        CheckConstraint("status <> 'rejected' OR btrim(rejection_reason) <> ''", name="rejected_has_reason"),
        Index("ix_event_category_start_time", "category", "start_time"),  # search (NFR-02)
        Index("ix_event_facility_id_start_time", "facility_id", "start_time"),  # conflict check (UC-07)
        # Admin queue and expiry job (UC-12): only pending rows are in this index.
        Index("ix_event_pending_start_time", "start_time", postgresql_where=text("status = 'pending'")),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facility.id"))
    title: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))  # free text (BR-14), same length as an interest
    description: Mapped[str] = mapped_column(Text, server_default="")
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), server_default=EventStatus.PENDING.value)  # BR-15
    # CR-01 review fields. reviewed_by stays empty when a request expires (BR-18).
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # NOT NULL with default '' (not NULL): "NULL <> ''" is unknown, and a CHECK lets unknown pass.
    rejection_reason: Mapped[str] = mapped_column(Text, server_default="")

    # The organizer is the first participant (BR-05), so the list is ordered by join time.
    participants: Mapped[list[EventParticipantRow]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, order_by="EventParticipantRow.joined_at"
    )


class EventParticipantRow(Base):
    __tablename__ = "event_participant"

    # The composite primary key means a user joins an event at most once (BR-07).
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --------------------------------------------------------------------------- #
# Constraints that need SQL expressions of the table columns
# --------------------------------------------------------------------------- #
_user = UserRow.__table__
_event = EventRow.__table__
_block = FacilityBlockRow.__table__

# UC-01: one account per e-mail address, without regard to upper or lower case.
Index("ux_user_email_lower", func.lower(_user.c.email), unique=True)

# BR-06, BR-16: no two ACTIVE events (pending, open, full) use the same facility at the same time.
# tstzrange(start, end) is the half-open range [start, end), so an event that ends at 18:00 and one
# that starts at 18:00 do not overlap (the same rule as TimeSlot.overlaps). The btree_gist extension
# lets the GiST index compare facility_id with "=". Rejected, cancelled and completed events are left
# out by the WHERE part, so they free the slot.
# An EXCLUDE constraint only compares rows of ONE table. An event that overlaps a facility_block is
# therefore not stopped here: FacilityService.check_bookable() checks it in code, inside the
# transaction that locks the facility row with SELECT ... FOR UPDATE (Software Design Report 5.3).
_event.append_constraint(
    ExcludeConstraint(
        (_event.c.facility_id, "="),
        (func.tstzrange(_event.c.start_time, _event.c.end_time), "&&"),
        name="ex_event_facility_no_overlap",
        using="gist",
        where=text(_one_of("status", ACTIVE_EVENT_STATUSES)),
    )
)

# BR-10 (UC-08 alt. 2a): blocks of one facility must not overlap each other.
_block.append_constraint(
    ExcludeConstraint(
        (_block.c.facility_id, "="),
        (func.tstzrange(_block.c.start_time, _block.c.end_time), "&&"),
        name="ex_facility_block_no_overlap",
        using="gist",
    )
)
