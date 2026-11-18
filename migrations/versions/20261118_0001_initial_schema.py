"""Initial schema: the 8 tables of the Software Design Report, section 6 (with CR-01).

Revision ID: 0001
Revises:
Create Date: 2026-11-18

op.f("name") means "use exactly this name" (no naming convention is added on top of it).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Copied here on purpose instead of imported from campusevent.models: a migration is a snapshot of
# the schema at one point in time and must give the same tables even after the code has changed.
ROLES = "'student', 'facility_staff', 'admin'"
EVENT_STATUSES = "'pending', 'rejected', 'open', 'full', 'completed', 'cancelled'"
ACTIVE_EVENT_STATUSES = "'pending', 'open', 'full'"


def _timestamp(name: str, **kwargs) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), **kwargs)


def upgrade() -> None:
    # btree_gist lets one GiST index compare an integer with "=" (facility_id) and a time range with
    # "&&" (overlaps); the two EXCLUDE constraints below need it. It is a "trusted" extension, so the
    # owner of the database can create it without superuser rights (also on Render).
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # ------------------------------------------------------------------ user
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), server_default="student", nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user")),
        sa.CheckConstraint(f"role IN ({ROLES})", name=op.f("ck_user_role_valid")),
        sa.CheckConstraint("btrim(email) <> ''", name=op.f("ck_user_email_not_empty")),
        sa.CheckConstraint("btrim(full_name) <> ''", name=op.f("ck_user_full_name_not_empty")),
    )
    # UC-01: one account per e-mail address, without regard to upper or lower case.
    op.create_index(op.f("ux_user_email_lower"), "user", [sa.text("lower(email)")], unique=True)

    # ------------------------------------------------------------------ verification_code
    op.create_table(
        "verification_code",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(255), nullable=False),
        _timestamp("expires_at", nullable=False),
        sa.Column("used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_verification_code")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_verification_code_user_id_user"), ondelete="CASCADE"
        ),
    )
    op.create_index(op.f("ix_verification_code_user_id"), "verification_code", ["user_id"])

    # ------------------------------------------------------------------ profile_interest
    op.create_table(
        "profile_interest",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("interest", sa.String(60), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "interest", name=op.f("pk_profile_interest")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_profile_interest_user_id_user"), ondelete="CASCADE"
        ),
        # BR-14: stored trimmed and in lower case.
        sa.CheckConstraint(
            "interest <> '' AND interest = lower(btrim(interest))", name=op.f("ck_profile_interest_interest_normalized")
        ),
    )

    # ------------------------------------------------------------------ availability_slot
    op.create_table(
        "availability_slot",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        _timestamp("start_time", nullable=False),
        _timestamp("end_time", nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_availability_slot")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_availability_slot_user_id_user"), ondelete="CASCADE"
        ),
        sa.CheckConstraint("end_time > start_time", name=op.f("ck_availability_slot_end_after_start")),
    )
    op.create_index(op.f("ix_availability_slot_user_id"), "availability_slot", ["user_id"])

    # ------------------------------------------------------------------ facility
    op.create_table(
        "facility",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("manager_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility")),
        sa.ForeignKeyConstraint(["manager_id"], ["user.id"], name=op.f("fk_facility_manager_id_user")),
        sa.UniqueConstraint("name", name=op.f("uq_facility_name")),
        sa.CheckConstraint("capacity >= 2", name=op.f("ck_facility_capacity_min")),
        sa.CheckConstraint("btrim(name) <> ''", name=op.f("ck_facility_name_not_empty")),
    )

    # ------------------------------------------------------------------ facility_block
    op.create_table(
        "facility_block",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        _timestamp("start_time", nullable=False),
        _timestamp("end_time", nullable=False),
        sa.Column("reason", sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_facility_block")),
        sa.ForeignKeyConstraint(
            ["facility_id"], ["facility.id"], name=op.f("fk_facility_block_facility_id_facility"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], name=op.f("fk_facility_block_created_by_user")),
        sa.CheckConstraint("end_time > start_time", name=op.f("ck_facility_block_end_after_start")),
    )
    # BR-10: blocks of one facility must not overlap each other.
    op.execute(
        """
        ALTER TABLE facility_block ADD CONSTRAINT ex_facility_block_no_overlap
            EXCLUDE USING gist (facility_id WITH =, tstzrange(start_time, end_time) WITH &&)
        """
    )

    # ------------------------------------------------------------------ event
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("organizer_id", sa.Integer(), nullable=False),
        sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        _timestamp("start_time", nullable=False),
        _timestamp("end_time", nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),  # BR-15
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        _timestamp("reviewed_at", nullable=True),
        # NOT NULL with default '': with NULL, "NULL <> ''" would be unknown and the CHECK would let it pass.
        sa.Column("rejection_reason", sa.Text(), server_default="", nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event")),
        sa.ForeignKeyConstraint(["organizer_id"], ["user.id"], name=op.f("fk_event_organizer_id_user")),
        sa.ForeignKeyConstraint(["facility_id"], ["facility.id"], name=op.f("fk_event_facility_id_facility")),
        sa.ForeignKeyConstraint(
            ["reviewed_by"], ["user.id"], name=op.f("fk_event_reviewed_by_user"), ondelete="SET NULL"
        ),
        sa.CheckConstraint("btrim(title) <> ''", name=op.f("ck_event_title_not_empty")),
        sa.CheckConstraint(
            "category <> '' AND category = lower(btrim(category))", name=op.f("ck_event_category_normalized")
        ),
        sa.CheckConstraint("capacity >= 2", name=op.f("ck_event_capacity_min")),  # BR-04
        sa.CheckConstraint("end_time > start_time", name=op.f("ck_event_end_after_start")),
        sa.CheckConstraint(f"status IN ({EVENT_STATUSES})", name=op.f("ck_event_status_valid")),
        # BR-17, BR-18: every rejected event has a reason (also the automatic rejection).
        sa.CheckConstraint(
            "status <> 'rejected' OR btrim(rejection_reason) <> ''", name=op.f("ck_event_rejected_has_reason")
        ),
    )
    op.create_index(op.f("ix_event_organizer_id"), "event", ["organizer_id"])
    op.create_index(op.f("ix_event_category_start_time"), "event", ["category", "start_time"])  # NFR-02
    op.create_index(op.f("ix_event_facility_id_start_time"), "event", ["facility_id", "start_time"])  # UC-07
    # UC-12: admin queue and expiry job; only pending rows are stored in this index.
    op.create_index(
        op.f("ix_event_pending_start_time"), "event", ["start_time"], postgresql_where=sa.text("status = 'pending'")
    )
    # BR-06, BR-16: no two ACTIVE events (pending, open, full) in the same facility at the same time.
    # [start, end) ranges: an event ending at 18:00 and one starting at 18:00 do not overlap.
    # An EXCLUDE constraint only compares rows of one table, so an overlap between an event and a
    # facility_block is checked in code (FacilityService.check_bookable, with the facility row locked).
    op.execute(
        f"""
        ALTER TABLE event ADD CONSTRAINT ex_event_facility_no_overlap
            EXCLUDE USING gist (facility_id WITH =, tstzrange(start_time, end_time) WITH &&)
            WHERE (status IN ({ACTIVE_EVENT_STATUSES}))
        """
    )

    # ------------------------------------------------------------------ event_participant
    op.create_table(
        "event_participant",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        _timestamp("joined_at", server_default=sa.func.now(), nullable=False),
        # A user joins an event at most once (BR-07).
        sa.PrimaryKeyConstraint("event_id", "user_id", name=op.f("pk_event_participant")),
        sa.ForeignKeyConstraint(
            ["event_id"], ["event.id"], name=op.f("fk_event_participant_event_id_event"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_event_participant_user_id_user"), ondelete="CASCADE"
        ),
    )
    op.create_index(op.f("ix_event_participant_user_id"), "event_participant", ["user_id"])


def downgrade() -> None:
    # Reverse order: a table can only be dropped after the tables that point to it.
    for table in (
        "event_participant",
        "event",
        "facility_block",
        "facility",
        "availability_slot",
        "profile_interest",
        "verification_code",
        "user",
    ):
        op.drop_table(table)  # also drops its indexes and constraints
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
