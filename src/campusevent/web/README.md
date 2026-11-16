# Web UI (layer 1, task 3.5)

Flask + Jinja2 + Bootstrap 5 pages for **UC-01 to UC-06 and UC-09 to UC-11**. The facility pages (UC-07, UC-08, task 3.6) are not part of this package yet; staff are redirected to `/facilities` after login.

| Blueprint | Pages | Use cases |
|---|---|---|
| `auth_routes` | `/signup`, `/verify`, `/login`, `/logout` | UC-01, UC-02 |
| `profile_routes` | `/profile` | UC-03 |
| `event_routes` | `/events`, `/events/new`, `/events/<id>`, `/events/<id>/join`, `/leave`, `/cancel`, `/activities` | UC-04, UC-05, UC-06, UC-09, UC-10, UC-11 |

## Run the tests
```bash
pip install -r requirements-dev.txt
python -m pytest tests/web
```
The web tests use in-memory stand-ins for the services (`tests/web/fakes.py`), so they pass before the real backend exists. Once a real service is ready, run the same tests against it by replacing the fake in `make_fake_services`.

## Rules the UI follows
- Presentation calls only service methods (design report, section 3.1). Services raise `CampusEventError` subclasses; `common.message_for` maps them to the messages of the use cases and `common.status_for` to HTTP codes.
- Templates get view models with **names only, never e-mail addresses** (NFR-05).
- CSRF token on every POST (Flask-WTF); session cookie is `Secure`, `HttpOnly`, `SameSite=Lax` (NFR-03). Set `SECRET_KEY` as an environment variable in production.
- Role checks: `student_required` here **and** inside the services (NFR-04).
- Bootstrap grid, checked at 375 px with no horizontal scrolling (NFR-01).

## What the UI needs from the backend
Planned in the design report (class diagram 4.2) and used as they are:
`AuthService.get_user(user_id)`, `register`, `verify_email`, `login`, `get_user_by_token`, `ProfileService.get_profile/update_profile`, `FacilityService.get_schedule`, `EventService.create_event/search_events/join_event/leave_event/cancel_event/get_activity_history`.

**Not in the design report yet, but needed by the pages (please add):**

| Method | Used by | Reason |
|---|---|---|
| `EventService.get_event(event_id) -> Event` | Event Details, join/leave/cancel result page | There is no way to read one event; raise `NotFoundError` for an unknown id |
| `FacilityService.list_facilities() -> list[Facility]` | Create Event dropdown, facility name on every event | The pages show facility names and capacities |
| `AuthService.get_user` must raise `NotFoundError` for unknown ids | Participant and organizer names | Names are looked up per user id |

**Known gaps (use case text asks for them, the current service interface cannot):**
- "Send a new code" (UC-01): needs `AuthService.resend_code(email)`. The sign-up page has no resend button yet.
- Time range filter (UC-05): `search_events` has no time parameter, so Find Events filters by keyword, category and date only.
- "Upcoming" tab on My Activities (finding F-09 of the design report): needs a service method for events the user has joined that are still open.
- "Suggest free slots of the day" (UC-04, UC-07): the Create Event page shows the busy times of the chosen facility and day, it does not suggest free ones.
