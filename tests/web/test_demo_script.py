"""The demo of scripts/run_demo.py: its events are always upcoming, whatever today's date is."""

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path


def load_demo_script():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_demo.py"
    spec = importlib.util.spec_from_file_location("run_demo", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_demo_uses_the_real_time_and_all_its_events_are_in_the_coming_week():
    services = load_demo_script().build_services()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # The demo shows Join, Leave and Cancel by the real date, not by the fixed time of the tests.
    assert abs(services.events.clock() - now) < timedelta(minutes=1)
    events = list(services.events.events.values())
    assert len(events) == 4
    for event in events:
        assert now < event.slot.start < now + timedelta(days=7), (event.title, event.slot.start)
