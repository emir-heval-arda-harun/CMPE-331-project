# Web UI (layer 1, tasks 3.5 and 3.6)

Flask + Jinja2 + Bootstrap 5 pages for **UC-01 to UC-06, UC-09 to UC-11 and UC-12** (admin review of event requests, change request CR-01). Facility staff manage facilities and blocked times on **Facility Management** (UC-07, UC-08, task 3.6). After login students go to `/events`, facility staff to `/facilities`, admins to `/admin/requests`.

| Blueprint | Pages | Use cases |
|---|---|---|
| `auth_routes` | `/signup`, `/verify`, `/login`, `/logout` | UC-01, UC-02 |
| `profile_routes` | `/profile` | UC-03 |
| `event_routes` | `/events`, `/events/new`, `/events/<id>`, `/events/<id>/join`, `/leave`, `/cancel`, `/activities` | UC-04, UC-05, UC-06, UC-09, UC-10, UC-11, organizer view of UC-12 |
| `admin_routes` | `/admin/requests`, `/admin/requests/<id>/approve`, `/reject` | UC-12 |
| `facility_routes` | `/facilities` (list, add facility, schedule of a day: `?facility=<id>&date=YYYY-MM-DD`), `/facilities/<id>/blocks` | UC-07, UC-08 (facility staff only) |

## Run the tests
```bash
pip install -r requirements-dev.txt
python -m pytest tests/web
```
The web tests use in-memory stand-ins for the services (`tests/web/fakes.py`), so they pass before the real backend exists. Once a real service is ready, run the same tests against it by replacing the fake in `make_fake_services`.

## Look of the pages ("Glass Night")
Every page uses one design: a dark animated background with frosted glass surfaces, the Inter typeface and an indigo-to-violet accent.
- `templates/_theme_glass.html`: colours, surfaces, buttons, forms, badges and the sign up / log in pages. Text on the glass is at least 4.5:1 against its background (WCAG AA), measured on the brightest part of the background.
- `templates/_backgrounds.html`: the animated background, the campus skyline (clock tower, library dome, stadium) drawn on a canvas. `campus-festival` (default, fireworks over the campus), `campus` (night), `campus-dusk` or `campus-neon`, chosen with the `BACKGROUND` setting of the app. Parts that do not move are drawn once and copied each frame. The animation pauses while the tab is hidden and shows one still picture for visitors who ask their system for reduced motion.
- Event lists show a coloured date tile (`date_panel` in `_macros.html`); its colour follows the category (`common.accent`), so events of one category look alike.

## Campus photo on the log in page
The left side of the sign up and log in pages shows a drawn campus skyline. To show a photo instead, put one file named `campus.jpg` (or `.jpeg`, `.png`, `.webp`) into `src/campusevent/web/static/img/`. No code change is needed; a dark blue layer is put over it so the text stays readable. Use a landscape photo about 1600 px wide and under 400 KB. Only add a photo that you own or that you are allowed to use: the repository is public.

## Rules the UI follows
- Presentation calls only service methods (design report, section 3.1). Services raise `CampusEventError` subclasses; `common.message_for` maps them to the messages of the use cases and `common.status_for` to HTTP codes.
- Templates get view models with **names only, never e-mail addresses** (NFR-05).
- CSRF token on every POST (Flask-WTF); session cookie is `Secure`, `HttpOnly`, `SameSite=Lax` (NFR-03). Set `SECRET_KEY` as an environment variable in production.
- Role checks: `student_required` / `admin_required` here **and** inside the services (NFR-04).
- **Times:** services and the database keep naive **UTC**; people see and type **Istanbul time** (UTC+3, no summer time). The UI converts only at the border, with `common.to_utc` / `slot_to_utc` before a service call and `to_campus` / `slot_to_campus` before a page shows a time. Methods that take a `day` work with a UTC day, so for the facility schedule the UI asks for both UTC days of the Istanbul day, and for the date filter it filters by Istanbul date itself. *Add to calendar* files are written in UTC (`…Z`).
- Pending and rejected requests are visible only to their organizer; for other students they do not exist (404), because BR-15 keeps them out of the public list.
- Bootstrap grid, checked at 375 px with no horizontal scrolling (NFR-01).

## What the UI needs from the backend
Planned in the design report (class diagram 4.2) and used as they are:
`AuthService.get_user(user_id)`, `register`, `verify_email`, `login`, `get_user_by_token`, `ProfileService.get_profile/update_profile`, `FacilityService.get_schedule`, `EventService.create_event/search_events/join_event/leave_event/cancel_event/get_activity_history`, and from CR-01 `list_pending_events/approve_event/reject_event/list_my_requests`.

**Not in the design report yet, but needed by the pages (please add):**

| Method | Used by | Reason |
|---|---|---|
| `EventService.get_event(event_id) -> Event` | Event Details, join/leave/cancel result page | There is no way to read one event; raise `NotFoundError` for an unknown id |
| `FacilityService.list_facilities() -> list[Facility]` | Create Event dropdown, facility name on every event | The pages show facility names and capacities |
| `AuthService.get_user` must raise `NotFoundError` for unknown ids | Participant and organizer names | Names are looked up per user id |

**Known gaps (use case text asks for them, the current service interface cannot):**
- "Send a new code" (UC-01 5a, UC-02 3a): `AuthService.resend_code(email)` exists now (task 3.2); the verify and log in pages still need a button for it.
- Time range filter (UC-05): `search_events` has no time parameter, so Find Events filters by keyword, category and date only.
- "Upcoming" tab on My Activities (finding F-09 of the design report): needs a service method for events the user has joined that are still open.

## Helper features of the pages
| Page | Feature | Note |
|---|---|---|
| Create Event | Schedule of the chosen facility and day reloads by itself (`/events/schedule`) | UC-07 |
| Create Event | Free times of the day as one-click suggestions, also after a "slot is busy" error | UC-04 4a. **Assumption:** opening hours 08:00–22:00 and gaps of at least one hour (`DAY_OPENS`, `DAY_CLOSES` in `common.py`), because the requirements do not define opening hours |
| Create Event | Warning while typing if the time overlaps a busy slot or ends before it starts; capacity limit of the facility | The server checks everything again |
| Find Events | One-click category filters, 20 events per page, "In 3 days" labels | Pagination as in the design report (NFR-02) |
| Event Details | "Add to calendar" (`/events/<id>/calendar.ics`), "Copy link", confirmation window before cancelling | |
| My Profile | Interests as tags with suggestions; remove button for availability rows | |
| Sign up | Password strength guide | Only advice; the rules are checked by the server |
| All pages | A form is sent only once; success messages fade out; footer | |

Every page still works without JavaScript; the scripts only add comfort.
