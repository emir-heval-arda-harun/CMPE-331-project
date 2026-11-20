# Software Testing Report – Facilities section (tasks 3.3 and 3.6)

**Author:** Harun Gündaş · **Status:** section for the team's Software Testing Report (task 4.1: pull request to Yeşim by 25.11.2026, PDF on Learn by 29.11.2026) · **Date of the results:** 20.11.2026

It covers UC-07 *View facility schedule and check conflicts* and UC-08 *Manage facility schedule*: the backend (`FacilityService`, `FacilityRepository`, task 3.3, PR #13), the Facility Management page (task 3.6, PR #15) and removing a block (issue #19, PR #22). The results below are for `main` together with PR #22. The other use cases are in the sections of the other team members, for example the [Web UI section](web_ui_test_section.md).

The parts the instructor asked for on 17.11 are in their own files:
- **Traceability matrix with code and requirements coverage:** [`docs/tests/coverage/facilities.md`](../tests/coverage/facilities.md)
- **Non-functional tests and their results:** [`docs/tests/non-func-tests/facilities.md`](../tests/non-func-tests/facilities.md)

## 1. Scope and approach
The facility part is tested on three levels, from the inside out:

| Level | What is tested | Test doubles | File | Run |
|---|---|---|---|---|
| Unit | `FacilityService`: business rules BR-04, BR-06, BR-09, BR-10, BR-16 and the input checks | Stand-ins for `AuthService` (only `require_role`) and for the event repository (only `active_on`); real `InMemoryFacilityRepository` and `InMemoryUnitOfWork` | [`tests/test_facility_service.py`](../../tests/test_facility_service.py) | `python -m pytest tests/test_facility_service.py` |
| Database | `SqlFacilityRepository` and `FacilityService` on a **real PostgreSQL 16** database: constraints, time conversion, row lock, rollback, delete | none | [`tests/db/test_facility_repository.py`](../../tests/db/test_facility_repository.py) | `python -m pytest tests/db` (needs `TEST_DATABASE_URL`, see [database README](../database/README.md)) |
| Web UI | The Facility Management page through the Flask test client: access, forms, error messages, Istanbul time, privacy | Fake `AuthService` and fake events of [`tests/web/fakes.py`](../../tests/web/fakes.py); the **real** `FacilityService` | [`tests/web/test_web_facilities.py`](../../tests/web/test_web_facilities.py) | `python -m pytest tests/web/test_web_facilities.py` |

**Why test doubles:** when these tests were written, `AuthService.register` (task 3.2) and the event service (task 3.4) still raised `NotImplementedError`. The stand-ins follow the interface of the class diagram (Software Design Report 4.2), so the facility rules could be tested before those tasks were done.

**Tools:** pytest 9.2, Flask 3.1 test client, SQLAlchemy 2.1, psycopg 3.3, PostgreSQL 16.16 (local), coverage.py 7.17 (branch coverage), ruff. CI (GitHub Actions) runs ruff and pytest on every push and pull request; it has no database, so the database tests are skipped there and were run locally.

## 2. Results

| Suite | Tests | Passed | Failed | Where |
|---|---|---|---|---|
| Unit, `tests/test_facility_service.py` | 41 | 41 | 0 | local and CI |
| Database, `tests/db/test_facility_repository.py` | 9 | 9 | 0 | local PostgreSQL 16.16 (skipped in CI) |
| Web UI, `tests/web/test_web_facilities.py` | 26 | 26 | 0 | local and CI |
| Requirement tests for UC-07, UC-08 and the facility part of NFR-04 | 6 | 3 | 3 | expected, see below |

**Code coverage** of the facility code with all three suites: **99 %** (statements and branches). `facilities.py` 100 %, `web/facility_routes.py` 100 %, `repositories/facility_repository.py` 97 %. Details and the two lines that are not covered: [coverage file](../tests/coverage/facilities.md#code-coverage).

`ruff check .` is clean.

**The 6 requirement tests:** they create users with `AuthService.register` and events with `EventService.create_event`, so they could not run before tasks 3.2 and 3.4. With Heval's PR #23 (register and log in), 3 of them pass: `test_student_cannot_manage_facilities`, `test_nfr04_student_cannot_manage_facilities` and `test_nfr04_student_cannot_block_a_facility`. The other 3 (`test_schedule_shows_existing_events`, `test_overlapping_event_in_same_facility_is_rejected`, `test_staff_blocks_facility_and_events_cannot_use_it`) stop at `EventService.create_event` (task 3.4) with `NotImplementedError`, before they reach `FacilityService`. The same rules are covered by the unit and web tests; the 3 tests are run again in integration testing (task 4.2).

## 3. Traceability
The matrix (requirement → tests → code, with the result of each requirement) is in [`docs/tests/coverage/facilities.md`](../tests/coverage/facilities.md#traceability-matrix). Every rule of UC-07 and UC-08 has at least one passing unit or web test; 3 requirement tests wait for task 3.4 (section 2).

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

## 6. Limits and what integration testing (task 4.2) must check
- The unit tests use stand-ins for `AuthService` and the event repository. After task 3.4: run the 3 waiting requirement tests of section 2 with the real services, and check that the real `EventRepository.active_on` returns pending, open and full events that overlap the UTC day.
- `check_bookable` must be called by `EventService.create_event` **after** `uow.begin()` and before the event is stored, so the row lock covers the whole booking.
- The database tests run only on a computer with `TEST_DATABASE_URL`; CI skips them, so the 97 % of the repository is a local result. A PostgreSQL service in CI would run them on every pull request (suggestion for task 3.7).
- After the wiring of the SQL classes (PR #25), the page must be tried once more on the Render deployment.
- The SonarQube analysis (`docs/tests/quality`) is done for the whole repository, not per section.
