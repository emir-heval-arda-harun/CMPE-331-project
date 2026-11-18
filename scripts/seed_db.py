"""Loads demo data into the database of DATABASE_URL (local PostgreSQL or Render).

    alembic upgrade head              (create the tables first)
    python scripts/seed_db.py         (only into an empty database)
    python scripts/seed_db.py --reset (deletes ALL rows of all tables first, then loads the demo data)

Run it again whenever the database is new, e.g. after Render's free database was recreated.
The dates are relative to today, so upcoming events are always in the future.

The demo accounts (demo.*@bilgiedu.net / demo.*@bilgi.edu.tr) are made up and open nothing else.
They all use the password CAMPUSEVENT_DEMO_PASSWORD from the environment or the local .env file;
without it a random password is made and printed. No password is written in this file.
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from argon2 import PasswordHasher  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import func, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from campusevent.models import EventStatus, Role  # noqa: E402
from campusevent.repositories.db import create_db_engine, create_session_factory  # noqa: E402
from campusevent.repositories.tables import (  # noqa: E402
    AvailabilitySlotRow,
    Base,
    EventParticipantRow,
    EventRow,
    FacilityBlockRow,
    FacilityRow,
    ProfileInterestRow,
    UserRow,
    VerificationCodeRow,
)

# Istanbul has been UTC+3 all year since 2016. A fixed offset needs no time zone database
# (Windows has none built in). The database stores everything in UTC.
ISTANBUL = timezone(timedelta(hours=3), "Europe/Istanbul")

# (key, e-mail, full name, role, verified)
USERS = [
    ("ayse", "demo.ayse@bilgiedu.net", "Ayşe Demir", Role.STUDENT, True),
    ("mehmet", "demo.mehmet@bilgiedu.net", "Mehmet Kaya", Role.STUDENT, True),
    ("deniz", "demo.deniz@bilgiedu.net", "Deniz Yıldız", Role.STUDENT, True),
    ("can", "demo.can@bilgiedu.net", "Can Arslan", Role.STUDENT, True),
    ("elif", "demo.elif@bilgiedu.net", "Elif Şahin", Role.STUDENT, False),  # signed up, code not entered yet
    ("staff", "demo.staff@bilgi.edu.tr", "Facility Staff (demo)", Role.FACILITY_STAFF, True),
    ("admin", "demo.admin@bilgi.edu.tr", "Student Affairs Admin (demo)", Role.ADMIN, True),
]

INTERESTS = {
    "ayse": ["football", "board games"],
    "mehmet": ["basketball", "chess"],
    "deniz": ["study group", "board games"],
    "can": ["football"],
}

# (key, name, capacity)
FACILITIES = [
    ("hall", "Santral Event Hall", 50),
    ("court", "Main Court", 20),
    ("sports", "Indoor Sports Hall", 30),
    ("study", "Study Room A", 8),
]


def at(days: int, hour: int, minute: int = 0) -> datetime:
    """A time in Istanbul, ``days`` from today, converted to UTC."""
    today = datetime.now(ISTANBUL).date()
    local = datetime(today.year, today.month, today.day, hour, minute, tzinfo=ISTANBUL) + timedelta(days=days)
    return local.astimezone(timezone.utc)


def load_demo_data(session: Session, password: str) -> str:
    """Insert the demo rows and return the verification code of the unverified demo user."""
    hasher = PasswordHasher()  # argon2id with a random salt per hash (NFR-03)
    now = datetime.now(timezone.utc)

    users = {}
    for key, email, name, role, verified in USERS:
        users[key] = UserRow(
            email=email, full_name=name, password_hash=hasher.hash(password), role=role.value, is_verified=verified
        )
    session.add_all(users.values())
    session.flush()  # sends the INSERTs, so the rows get their ids

    # UC-01: the unverified user has a code that is valid for 15 minutes (only its hash is stored).
    code = f"{secrets.randbelow(10**6):06d}"
    session.add(
        VerificationCodeRow(
            user_id=users["elif"].id, code_hash=hasher.hash(code), expires_at=now + timedelta(minutes=15)
        )
    )

    # UC-03: interests and availability.
    for key, interests in INTERESTS.items():
        session.add_all(ProfileInterestRow(user_id=users[key].id, interest=i) for i in interests)
    session.add_all(
        [
            AvailabilitySlotRow(user_id=users["ayse"].id, start_time=at(2, 17), end_time=at(2, 22)),
            AvailabilitySlotRow(user_id=users["mehmet"].id, start_time=at(3, 15), end_time=at(3, 19)),
            AvailabilitySlotRow(user_id=users["deniz"].id, start_time=at(4, 12), end_time=at(4, 16)),
        ]
    )

    # UC-08: facilities and blocked periods, managed by the facility staff member.
    staff_id = users["staff"].id
    facilities = {key: FacilityRow(manager_id=staff_id, name=name, capacity=cap) for key, name, cap in FACILITIES}
    session.add_all(facilities.values())
    session.flush()
    session.add_all(
        [
            FacilityBlockRow(
                facility_id=facilities["sports"].id,
                created_by=staff_id,
                start_time=at(1, 9),
                end_time=at(1, 12),
                reason="Physical education class",
            ),
            FacilityBlockRow(
                facility_id=facilities["hall"].id,
                created_by=staff_id,
                start_time=at(5, 8),
                end_time=at(5, 20),
                reason="Maintenance",
            ),
        ]
    )

    # UC-04 to UC-12: one event in every status. Every event has its organizer as first participant.
    admin_id = users["admin"].id
    approved = {"reviewed_by": admin_id, "reviewed_at": now - timedelta(days=1)}
    events = [
        # (event, participants after the organizer)
        (
            EventRow(
                organizer_id=users["ayse"].id, facility_id=facilities["hall"].id, title="Board game night",
                category="board games", description="Bring your own games.", start_time=at(2, 18),
                end_time=at(2, 21), capacity=8, status=EventStatus.OPEN.value, **approved,
            ),
            ["deniz", "can"],
        ),
        (
            # The same slot as the board game night: allowed, because a rejected request frees the slot.
            EventRow(
                organizer_id=users["mehmet"].id, facility_id=facilities["hall"].id, title="Poker night",
                category="card games", start_time=at(2, 18), end_time=at(2, 21), capacity=6,
                status=EventStatus.REJECTED.value, rejection_reason="Gambling is not allowed on campus", **approved,
            ),
            [],
        ),
        (
            EventRow(
                organizer_id=users["mehmet"].id, facility_id=facilities["study"].id, title="Chess club meetup",
                category="chess", start_time=at(3, 16), end_time=at(3, 18), capacity=4,
                status=EventStatus.FULL.value, **approved,
            ),
            ["ayse", "deniz", "can"],
        ),
        (
            EventRow(
                organizer_id=users["can"].id, facility_id=facilities["court"].id, title="Football friendly",
                category="football", description="5 vs 5, all levels welcome.", start_time=at(4, 17),
                end_time=at(4, 19), capacity=10,  # status: database default 'pending' (BR-15)
            ),
            [],
        ),
        (
            EventRow(
                organizer_id=users["mehmet"].id, facility_id=facilities["hall"].id, title="Movie night",
                category="movies", start_time=at(6, 19), end_time=at(6, 22), capacity=40,
            ),
            [],
        ),
        (
            # Overlaps the pending football friendly: allowed, because a cancelled event frees the slot.
            EventRow(
                organizer_id=users["deniz"].id, facility_id=facilities["court"].id, title="Basketball 3x3",
                category="basketball", start_time=at(4, 17, 30), end_time=at(4, 18, 30), capacity=6,
                status=EventStatus.CANCELLED.value, **approved,
            ),
            [],
        ),
        (
            EventRow(
                organizer_id=users["deniz"].id, facility_id=facilities["study"].id, title="CMPE 331 study group",
                category="study group", start_time=at(-3, 14), end_time=at(-3, 16), capacity=6,
                status=EventStatus.COMPLETED.value, reviewed_by=admin_id, reviewed_at=now - timedelta(days=6),
            ),
            ["ayse", "mehmet"],
        ),
        (
            EventRow(
                organizer_id=users["can"].id, facility_id=facilities["court"].id, title="Sunday football",
                category="football", start_time=at(-7, 10), end_time=at(-7, 12), capacity=10,
                status=EventStatus.COMPLETED.value, reviewed_by=admin_id, reviewed_at=now - timedelta(days=9),
            ),
            ["ayse", "mehmet"],
        ),
    ]
    for event, _ in events:
        session.add(event)
    session.flush()
    for event, others in events:
        joined = event.start_time - timedelta(days=5)
        # The organizer joins first (BR-05); the others a few minutes later, in this order.
        for minutes, key in enumerate([None, *others]):
            user_id = event.organizer_id if key is None else users[key].id
            joined_at = joined + timedelta(minutes=minutes)
            session.add(EventParticipantRow(event_id=event.id, user_id=user_id, joined_at=joined_at))
    return code


def reset(session: Session) -> None:
    """Delete every row of every table and restart the ids at 1."""
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="delete ALL existing rows before loading")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")  # real environment variables win over .env
    password = os.environ.get("CAMPUSEVENT_DEMO_PASSWORD") or secrets.token_urlsafe(9)

    engine = create_db_engine()
    print(f"Database: {engine.url.render_as_string(hide_password=True)}")
    session_factory = create_session_factory(engine)
    # One transaction: if anything fails, nothing is stored.
    with session_factory.begin() as session:
        if args.reset:
            reset(session)
            print("Deleted all existing rows.")
        elif session.scalar(select(func.count()).select_from(UserRow)):
            sys.exit("The database already has data. Use --reset to delete it and load the demo data again.")
        code = load_demo_data(session, password)

    with session_factory() as session:
        for table in Base.metadata.sorted_tables:
            count = session.scalar(select(func.count()).select_from(table))
            print(f"  {table.name:<18} {count:>3} rows")
    engine.dispose()

    print("Demo accounts: " + ", ".join(email for _, email, _, _, _ in USERS))
    if os.environ.get("CAMPUSEVENT_DEMO_PASSWORD"):
        print("Password: the one in CAMPUSEVENT_DEMO_PASSWORD")
    else:
        print(f"Password for all demo accounts: {password}")
    print(f"Verification code of demo.elif@bilgiedu.net (valid 15 minutes): {code}")


if __name__ == "__main__":
    main()
