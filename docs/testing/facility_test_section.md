# Software Testing Report – Facilities section (tasks 3.3 and 3.6)

**Author:** Harun Gündaş · **Status:** section for the team's Software Testing Report (task 4.1: pull request to Yeşim by 25.11.2026, PDF on Learn by 29.11.2026) · **Date of the results:** 20.11.2026, updated 26.11.2026 after the instructor's review

It covers UC-07 *View facility schedule and check conflicts* and UC-08 *Manage facility schedule*: the backend (`FacilityService`, `FacilityRepository`, task 3.3, PR #13), the Facility Management page (task 3.6, PR #15) and removing a block (issue #19, PR #22). The results below are for `main` together with PR #22. The other use cases are in the sections of the other team members, for example the [Web UI section](web_ui_test_section.md).

The parts the instructor asked for on 17.11 are in their own files:
- **Traceability matrix with code and requirements coverage:** [`docs/tests/coverage/facilities.md`](../tests/coverage/facilities.md)
- **Non-functional tests and their results:** [`docs/tests/non-func-tests/facilities.md`](../tests/non-func-tests/facilities.md)
- **TDD evidence (tests first, red → green):** [`docs/tests/tdd/facilities.md`](../tests/tdd/facilities.md)

## 1. Scope and approach
The facility part is tested on three levels, from the inside out:

| Level | What is tested | Test doubles | File | Run |
|---|---|---|---|---|
| Unit | `FacilityService`: business rules BR-04, BR-06, BR-09, BR-10, BR-16 and the input checks | Stand-ins for `AuthService` (only `require_role`) and for the event repository (only `active_on`); real `InMemoryFacilityRepository` and `InMemoryUnitOfWork` | [`tests/test_facility_service.py`](../../tests/test_facility_service.py) | `python -m pytest tests/test_facility_service.py` |
| Database | `SqlFacilityRepository` and `FacilityService` on a **real PostgreSQL 16** database: constraints, time conversion, row lock, rollback, delete | none | [`tests/db/test_facility_repository.py`](../../tests/db/test_facility_repository.py) | `python -m pytest tests/db` (needs `TEST_DATABASE_URL`, see [database README](../database/README.md)) |
| Web UI | The Facility Management page through the Flask test client: access, forms, error messages, Istanbul time, privacy | Fake `AuthService` and fake events of [`tests/web/fakes.py`](../../tests/web/fakes.py); the **real** `FacilityService` | [`tests/web/test_web_facilities.py`](../../tests/web/test_web_facilities.py) | `python -m pytest tests/web/test_web_facilities.py` |

**Why test doubles:** when these tests were written, `AuthService.register` (task 3.2) and the event service (task 3.4) still raised `NotImplementedError`. The stand-ins follow the interface of the class diagram (Software Design Report 4.2), so the facility rules could be tested before those tasks were done.

**Tools:** pytest 9.2, Flask 3.1 test client, SQLAlchemy 2.1, psycopg 3.3, PostgreSQL 16.16 (local), coverage.py 7.17 (branch coverage), ruff. CI (GitHub Actions) runs ruff and pytest on every push and pull request. Since #36 the CI test job has its own PostgreSQL 16, so the database tests run there too and are no longer skipped (CI run 45851087074 of `main` at `22825b5`, 26.11.2026: 446 passed, 0 skipped).

## 2. Results

| Suite | Tests | Passed | Failed | Where |
|---|---|---|---|---|
| Unit, `tests/test_facility_service.py` | 41 | 41 | 0 | local and CI |
| Database, `tests/db/test_facility_repository.py` | 9 | 9 | 0 | local PostgreSQL 16.16 and CI (PostgreSQL 16, since #36) |
| Web UI, `tests/web/test_web_facilities.py` | 26 | 26 | 0 | local and CI |
| Requirement tests for UC-07, UC-08 and the facility part of NFR-04 | 6 | 6 | 0 | `main` since #33 (23.11.2026), see below |

**Code coverage** of the facility code with all three suites: **99 %** (statements and branches). `facilities.py` 100 %, `web/facility_routes.py` 100 %, `repositories/facility_repository.py` 97 %. Details and the two lines that are not covered: [coverage file](../tests/coverage/facilities.md#code-coverage).

`ruff check .` is clean.

**The 6 requirement tests: all 6 pass on `main` since #33 (23 Nov 2026).** How they got there: they create users with `AuthService.register` and events with `EventService.create_event`, so they could not run before tasks 3.2 and 3.4. With Heval's PR #23 (register and log in), 3 of them pass: `test_student_cannot_manage_facilities`, `test_nfr04_student_cannot_manage_facilities` and `test_nfr04_student_cannot_block_a_facility`. The other 3 (`test_schedule_shows_existing_events`, `test_overlapping_event_in_same_facility_is_rejected`, `test_staff_blocks_facility_and_events_cannot_use_it`) stop at `EventService.create_event` (task 3.4) with `NotImplementedError`, before they reach `FacilityService`. The same rules are covered by the unit and web tests; the 3 tests are run again in integration testing (task 4.2). First check on 21 Nov 2026: with Arda's events backend (PR #33, not merged yet) merged locally into `main`, all 3 pass (UC-04, UC-07 and UC-08: 9 of 9 tests). **Since #33 was merged on 23 Nov 2026, all 6 pass on `main`** (checked again on 23 Nov: 6 of 6, and the 76 unit, database and web tests of the facility part still pass).

## 3. Traceability
The matrix (requirement → tests → code, with the result of each requirement) is in [`docs/tests/coverage/facilities.md`](../tests/coverage/facilities.md#traceability-matrix). Every rule of UC-07 and UC-08 has at least one passing unit or web test, and all 6 requirement tests pass on `main` since #33 (section 2).

## 4. Test design
- **Equivalence classes and boundary values.** Capacity: 1 (refused), 2 (smallest accepted), 0, negative, 2.5, `"10"` as text and `True` (all refused). Name: empty, only spaces, 100 characters (accepted), 101 characters (refused). Reason: empty, only spaces, 201 characters (refused).
- **Time boundaries.** Time ranges are half-open `[start, end)`, like `TimeSlot.overlaps` and the database's `tstzrange`. A block 09:00–12:00 and a booking 12:00–13:00 do **not** overlap; 11:00–13:00 does. A slot from 23:00 to 01:00 is checked against both days. An Istanbul day touches two UTC days; the page asks for both and keeps only what overlaps the Istanbul day (`test_event_of_the_evening_before_is_not_on_the_next_day`).
- **State-based tests.** Every event status was tested once against the facility schedule: pending, open and full hold the slot; cancelled, rejected and completed free it. A block can be removed once; the second time gives "not found".
- **Negative tests.** Wrong role, unknown facility or block, block of another facility in the address, end before start, overlapping input. Each one checks the error type and that nothing was stored or deleted (`InMemoryUnitOfWork.rollbacks`, row count in the database).
- **Concurrency.** The row lock is tested with a second database connection: while the first transaction holds `SELECT … FOR UPDATE`, `SELECT … FOR UPDATE NOWAIT` from the second connection fails with `LockNotAvailable`.
- **Coverage-guided tests.** After measuring the coverage, the one untested branch of the page (an event on the other UTC day) got a test, together with a privacy test (NFR-05).
- **Manual test (NFR-01).** The Facility Management page was used in a browser with the demo data (`scripts/run_demo.py`) as facility staff, at desktop width and at 375 px: list, schedule, add facility, add block, remove block with the confirmation window. No horizontal scrolling at 375 px (`scrollWidth` = 375).

## 5. Defects found while testing

| # | Found by | Defect | Fix |
|---|---|---|---|
| 1 | Code review before the first test run | `SqlFacilityRepository` called `session.rollback()` itself after a constraint error, which would also undo the other work of the same request | Removed; only the service's `UnitOfWork` rolls back (Design Report 7.1) |
| 2 | Database tests | The local test database refused the migration (`must be owner of extension btree_gist`) | Setup problem, not code: the extension had been created by hand with another user. Documented setup in the database README is correct |
| 3 | Web test `test_block_over_an_event_booking_is_refused` | Blocking over an event showed the student message "Please choose another time or facility" | The page shows the service text "An event is booked in this time, so it cannot be blocked." |
| 4 | Web tests | Test events were created in UTC but `fakes.slot()` takes Istanbul time, so they were 3 hours off | Tests use Istanbul time like the rest of `tests/web` |
| 5 | Manual test at 375 px | On a phone the schedule was below the *Add a facility* form, so choosing a facility seemed to do nothing | Facility links jump to the schedule (`#schedule`) |
| 6 | Review of the page by Emir (issue #19) | A block added by mistake could not be removed, and the schedule showed only "Booked" without the event | Remove button with confirmation (UC-08 alt. 2b) and event titles in the schedule (PR #22) |
| 7 | Coverage measurement | `pytest --cov=<module>` broke the database tests (`'InternalTraversal' object is not callable` inside SQLAlchemy) | Tool problem, not code: coverage is measured with `coverage run --source=src/campusevent -m pytest` (see the coverage file) |
| 8 | Review of #22 by Emir (Firefox and WebKit) | After the Glass Night theme (#20), the *Remove* button on the light yellow block row had a contrast of 1.7:1 (WCAG AA needs 4.5:1) | The button has its own colour `#b91c1c` on the block row: 5.9:1, measured in the demo (PR #22) |
| 9 | Emir, after the Glass Night theme | The facility names in the list were dark text on the dark glass and could hardly be read | Glass colours for the facility list in `_theme_glass.html` (Emir's PR #28) |

## 6. Limits and what integration testing (task 4.2) must check
- The unit tests use stand-ins for `AuthService` and the event repository. The 6 requirement tests of section 2 use the real services, and all 6 pass on `main` since #33 (23 Nov 2026). The real `EventRepository.active_on` is covered by the database tests of #38 (pending, open and full events that overlap the UTC day).
- `check_bookable` must be called by `EventService.create_event` **after** `uow.begin()` and before the event is stored, so the row lock covers the whole booking. It is (`events.py`, checked on 27 Nov 2026).
- **Integration test of risk R-01 (task 4.2, 27 Nov 2026):** [`tests/db/test_booking_race.py`](../../tests/db/test_booking_race.py) runs two requests of the real services (`create_app` with PostgreSQL) in two threads at the same moment: two students booking overlapping times, a block started while a booking is in progress, and a booking started while a block is in progress. The first request is held inside its transaction; the test checks in `pg_stat_activity` that the second one waits for the facility lock, then lets the first one finish. In all 3 cases the first request succeeds and the second gets `FacilityConflictError`, with nothing stored (3 of 3 pass, also 5 times in a row). With the lock removed from `get_for_update` all 3 fail, so the tests really check the lock. These 3 tests came after the final CI run of 26.11, so they are not in its 473 tests.
- The database tests need `TEST_DATABASE_URL`. Since #36 CI sets it for its own PostgreSQL 16, so they run on every push and pull request. The coverage figures (97 % of the repository) were measured locally; CI measures the whole package with `pytest --cov`.
- **Render (checked 22 Nov 2026, `main` at `c98923c`, demo data from `scripts/seed_db.py`):** https://campusevent-86ax.onrender.com. Facility staff log in and get the Facility Management page with the 4 demo facilities and a schedule (200); a student gets 403 on `/facilities` (NFR-04). The session cookie is `Secure; HttpOnly; SameSite=Lax` (NFR-03). Find Events still answered 500 there, because `EventService` on `main` was the skeleton.
- **Render again (checked 23 Nov 2026, after #33 was merged; deployed by the CI `deploy` job from `main` at `65f1781`):** Find Events, Event Details, My Activities (with the activity history of completed events) and Create Event answer 200 for a student; Event Requests answers 200 for the admin and 403 for facility staff (NFR-04). On Facility Management, the schedule of Santral Event Hall for 24 Nov shows the booking "18:00 – 21:00 Event: Board game night" next to the blocks, so the facility side and the event side now work together on the live site.
- The SonarQube analysis (`docs/tests/quality`) is done for the whole repository, not per section.
