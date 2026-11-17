"""Starts the web UI on this computer with fake in-memory data, to look at the pages.

    python scripts/run_demo.py            (then open http://localhost:5055)

Nothing is stored: all data disappears when the program stops. The accounts below exist only in
this demo and only on your own computer; they are not real accounts and open nothing else.
The services are the stand-ins of tests/web/fakes.py, so this works before the real backend exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from campusevent.models import Role  # noqa: E402
from campusevent.web import create_web_app  # noqa: E402
from tests.web.fakes import make_fake_services, slot  # noqa: E402

DEMO_PASSWORD = "Campus-Demo-2026!"

# (e-mail, name, role). Every account uses DEMO_PASSWORD.
DEMO_ACCOUNTS = [
    ("demo@bilgiedu.net", "Demo Student", Role.STUDENT),
    ("organizer@bilgiedu.net", "Demo Organizer", Role.STUDENT),
    ("staff@bilgi.edu.tr", "Facility Staff", Role.FACILITY_STAFF),
]


def build_services():
    services = make_fake_services()
    for email, name, role in DEMO_ACCOUNTS:
        services.auth.register(email, DEMO_PASSWORD, name, role)
        services.auth.verify_email(email, "123456")  # the fake e-mail sender always sends 123456
    staff = next(u for u in services.auth.users.values() if u.role == Role.FACILITY_STAFF)
    organizer = services.auth.users[2]
    hall = services.facilities.add_facility(staff.id, "Santral Event Hall", 50)
    court = services.facilities.add_facility(staff.id, "Main Court", 20)
    services.facilities.add_facility(staff.id, "Indoor Sports Hall", 30)
    services.facilities.add_facility(staff.id, "Study Room A", 8)
    services.events.create_event(
        organizer.id, "Board game night", "board games", hall.id, slot(day=20, hour=18), 8, "Bring your own games."
    )
    services.events.create_event(organizer.id, "Football friendly", "football", court.id, slot(day=21, hour=17), 10)
    return services


def main(port: int = 5055) -> None:
    app = create_web_app(
        build_services(),
        {"SESSION_COOKIE_SECURE": False, "SECRET_KEY": "demo-only-not-a-secret"},
    )
    print(f"CampusEvent demo: http://localhost:{port}  (accounts: see DEMO_ACCOUNTS in this file)")
    app.run(port=port)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5055)
