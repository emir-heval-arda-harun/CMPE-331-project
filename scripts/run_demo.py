"""Starts the web UI on this computer with fake in-memory data, to look at the pages.

    python scripts/run_demo.py            (then open http://localhost:5055)

Nothing is stored: all data disappears when the program stops. The accounts below exist only in
this demo and only on your own computer; they are not real accounts and open nothing else.
The services are the stand-ins of tests/web/fakes.py, so this works before the real backend exists.

No password is written in this file. The demo password is CAMPUSEVENT_DEMO_PASSWORD from the
environment or from a local .env file (see .env.example); without it a random password is made
at every start and printed in the terminal.
"""

from __future__ import annotations

import os
import secrets
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from campusevent.facilities import FacilityService  # noqa: E402
from campusevent.models import Role, TimeSlot  # noqa: E402
from campusevent.web import create_web_app  # noqa: E402
from campusevent.web.common import campus_today, slot_to_utc  # noqa: E402
from tests.web.fakes import make_fake_services  # noqa: E402


def load_env_file(path: Path = ROOT / ".env") -> None:
    """Read KEY=VALUE lines of a local .env file. Values already set in the environment win."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and key and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()
DEMO_PASSWORD = os.environ.get("CAMPUSEVENT_DEMO_PASSWORD") or secrets.token_urlsafe(9)

# (e-mail, name, role). Every account uses DEMO_PASSWORD.
DEMO_ACCOUNTS = [
    ("demo@bilgiedu.net", "Demo Student", Role.STUDENT),
    ("organizer@bilgiedu.net", "Demo Organizer", Role.STUDENT),
    ("staff@bilgi.edu.tr", "Facility Staff", Role.FACILITY_STAFF),
    ("admin@bilgi.edu.tr", "Demo Admin", Role.ADMIN),  # reviews event requests (UC-12)
]


def at(days: int, hour: int, hours: int = 1) -> TimeSlot:
    """A slot ``days`` from today at ``hour`` campus (Istanbul) time, in naive UTC as the services keep it.
    The demo events are therefore always in the coming days, whatever the date of the demo is."""
    start = datetime.combine(campus_today() + timedelta(days=days), time(hour))
    return slot_to_utc(TimeSlot(start, start + timedelta(hours=hours)))


def build_services():
    services = make_fake_services(auto_approve=False)  # new events wait for the admin, as in CR-01
    # The fakes keep the fixed time of the tests; the demo uses the real time, so Join, Leave and Cancel
    # are offered as on the live site.
    services.events.clock = lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    # The real FacilityService (task 3.3) with the fake events, so the Facility Management page can add blocks.
    services.facilities = FacilityService(services.auth, events=services.events)
    services.events.facilities = services.facilities
    for email, name, role in DEMO_ACCOUNTS:
        services.auth.register(email, DEMO_PASSWORD, name, role)
        services.auth.verify_email(email, "123456")  # the fake e-mail sender always sends 123456
    staff = next(u for u in services.auth.users.values() if u.role == Role.FACILITY_STAFF)
    student = services.auth.users[1]
    organizer = services.auth.users[2]
    admin = next(u for u in services.auth.users.values() if u.role == Role.ADMIN)
    hall = services.facilities.add_facility(staff.id, "Santral Event Hall", 50)
    court = services.facilities.add_facility(staff.id, "Main Court", 20)
    services.facilities.add_facility(staff.id, "Indoor Sports Hall", 30)
    services.facilities.add_block(staff.id, court.id, at(2, 9, hours=3), "Physical education class")
    services.facilities.add_facility(staff.id, "Study Room A", 8)
    games = services.events.create_event(
        organizer.id, "Board game night", "board games", hall.id, at(1, 18), 8, "Bring your own games."
    )
    match = services.events.create_event(organizer.id, "Football friendly", "football", court.id, at(2, 17), 10)
    for event in (games, match):
        services.events.approve_event(event.id, admin.id)
    # One request in each review state, so the admin page and My Activities have something to show.
    services.events.create_event(
        student.id, "Chess club meetup", "chess", hall.id, at(3, 16), 12, "Beginners welcome."
    )
    refused = services.events.create_event(student.id, "Late night karaoke", "music", hall.id, at(4, 21), 30)
    services.events.reject_event(refused.id, admin.id, "The hall closes at 22:00; please choose an earlier time.")
    return services


def main(port: int = 5055) -> None:
    app = create_web_app(
        build_services(),
        {"SESSION_COOKIE_SECURE": False, "SECRET_KEY": secrets.token_hex(32)},  # plain http on localhost only
    )
    print(f"CampusEvent demo: http://localhost:{port}")
    print("Demo accounts: " + ", ".join(email for email, _, _ in DEMO_ACCOUNTS))
    if os.environ.get("CAMPUSEVENT_DEMO_PASSWORD"):
        print("Demo password: the one in CAMPUSEVENT_DEMO_PASSWORD")
    else:
        print(f"Demo password for this run: {DEMO_PASSWORD}")
    app.run(host="127.0.0.1", port=port)  # reachable from this computer only


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5055)
