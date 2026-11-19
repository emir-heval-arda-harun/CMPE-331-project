# Software Testing Report – Facilities section (tasks 3.3 and 3.6)

**Author:** Harun Gündaş · **Status:** section for the team's Software Testing Report (task 4.1, due 22.11.2026) · **Date of the results:** 19.11.2026

It covers UC-07 *View facility schedule and check conflicts* and UC-08 *Manage facility schedule*: the backend (`FacilityService`, `FacilityRepository`, task 3.3, PR #13) and the Facility Management page (task 3.6, PR #15). The other use cases are in the sections of the other team members, for example [Web UI section](web_ui_test_section.md).

## 1. Scope and approach
The facility part is tested on three levels, from the inside out:

| Level | What is tested | Test doubles | File | Run |
|---|---|---|---|---|
| Unit | `FacilityService`: business rules BR-04, BR-06, BR-09, BR-10, BR-16 and the input checks | Stand-ins for `AuthService` (only `require_role`) and for the event repository (only `active_on`); real `InMemoryFacilityRepository` and `InMemoryUnitOfWork` | [`tests/test_facility_service.py`](../../tests/test_facility_service.py) | `python -m pytest tests/test_facility_service.py` |
| Database | `SqlFacilityRepository` and `FacilityService` on a **real PostgreSQL 16** database: constraints, time conversion, row lock, rollback | none | [`tests/db/test_facility_repository.py`](../../tests/db/test_facility_repository.py) | `python -m pytest tests/db` (needs `TEST_DATABASE_URL`, see [database README](../database/README.md)) |
| Web UI | The Facility Management page through the Flask test client: access, forms, error messages, Istanbul time | Fake `AuthService` and fake events of [`tests/web/fakes.py`](../../tests/web/fakes.py); the **real** `FacilityService` | [`tests/web/test_web_facilities.py`](../../tests/web/test_web_facilities.py) | `python -m pytest tests/web/test_web_facilities.py` |

**Why test doubles:** on the date of writing, `AuthService.register` (task 3.2) and the event service (task 3.4) still raise `NotImplementedError`. The stand-ins follow the interface of the class diagram (Software Design Report 4.2), so the facility rules could be tested before those tasks are done.

**Tools:** pytest 9.2, Flask 3.1 test client, SQLAlchemy 2.1, psycopg 3.3, PostgreSQL 16.16 (local), ruff. CI (GitHub Actions) runs ruff and pytest on every push and pull request; it has no database, so the database tests are skipped there and were run locally.

## 2. Results

| Suite | Tests | Passed | Failed | Where |
|---|---|---|---|---|
| Unit, `tests/test_facility_service.py` | 35 | 35 | 0 | local and CI |
| Database, `tests/db/test_facility_repository.py` | 7 | 7 | 0 | local PostgreSQL 16.16 (skipped in CI) |
| Web UI, `tests/web/test_web_facilities.py` | 19 | 19 | 0 | local and CI |
| Requirement tests for UC-07, UC-08 and the facility part of NFR-04 | 6 | 0 | 6 | expected, see below |

Whole repository at the same time (with PR #15): 212 passed, 51 failed; all 51 failures are `NotImplementedError` of the skeleton tasks 3.2 and 3.4. `ruff check .` is clean.

**Why the 6 requirement tests still fail:** `test_uc07_*`, `test_uc08_*`, `test_nfr04_student_cannot_manage_facilities` and `test_nfr04_student_cannot_block_a_facility` first create users with `AuthService.register` and events with `EventService.create_event`. Both are not implemented yet, so these tests stop before they reach `FacilityService`. The same rules are covered by the unit and web tests above. When tasks 3.2 and 3.4 are merged, the 6 tests are run again (integration testing, task 4.2).

## 3. Traceability: requirement to test

| Requirement | Rule | Tests |
|---|---|---|
| UC-08 step 1 | Staff add a facility with name and capacity | `test_staff_adds_facility`, `test_add_get_find_and_list` (DB), `test_staff_adds_a_facility` (web) |
| UC-08 alt. 1a, BR-09 | Only facility staff manage facilities and blocks | `test_student_cannot_add_facility_or_block`, `test_only_staff_can_open_the_page` (web) |
| UC-08 alt. 1b | Capacity is a whole number of at least 2 | `test_capacity_must_be_a_whole_number_of_at_least_2`, `test_smallest_capacity_and_longest_name_are_accepted`, `test_wrong_capacity_is_explained_and_the_name_is_kept` (web) |
| Data design §6 | Name required, at most 100 characters, unique without regard to case | `test_name_is_required_and_short`, `test_facility_names_are_unique_without_regard_to_case`, `test_duplicate_name_becomes_a_validation_error` (DB), `test_duplicate_facility_name_is_refused` (web) |
| UC-08 step 2 | Staff block a time with a reason | `test_block_makes_the_facility_unavailable`, `test_block_needs_a_short_reason`, `test_block_must_end_after_it_starts`, `test_staff_blocks_a_time_in_istanbul_time` (web), `test_wrong_block_input_is_explained` (web) |
| UC-08 alt. 2a, BR-10 | Blocks of one facility do not overlap | `test_overlapping_blocks_are_rejected`, `test_overlapping_blocks_become_a_validation_error` (DB), `test_overlapping_block_is_refused_and_the_form_is_kept` (web) |
| BR-06 | An event and a block never share a slot | `test_block_over_a_booked_event_is_rejected`, `test_check_bookable_refuses_busy_slots`, `test_block_over_an_event_booking_is_refused` (web) |
| UC-08 postcondition | Students cannot book a blocked time | `test_check_bookable_refuses_busy_slots`, `test_a_blocked_time_cannot_be_booked` (web) |
| UC-07 step 2 | The schedule shows blocks and events of a day, sorted | `test_schedule_lists_blocks_and_active_events_sorted`, `test_schedule_shows_blocks_and_bookings_of_the_istanbul_day` (web) |
| UC-07 step 2, BR-16 (CR-01) | Pending, open and full events hold their slot; cancelled, rejected and completed events free it | `test_active_events_hold_their_slot`, `test_inactive_events_free_their_slot`, `test_cancelled_events_do_not_show_in_the_schedule` (web) |
| UC-07 step 3–4, alt. 3a | Conflict check for a new event (`check_bookable`, used by UC-04) | `test_check_bookable_returns_the_facility`, `test_check_bookable_refuses_busy_slots`, `test_check_bookable_unknown_facility` |
| UC-04 alt. 3b, BR-04 | Event capacity at most the facility capacity | `test_check_bookable_refuses_more_people_than_the_facility_holds` |
| Design report 5.3, 7.1 (risk R-01) | The facility row is locked while a booking is checked, so two requests cannot book the same slot | `test_get_for_update_locks_the_facility_row` (DB) |
| Design report 7.1 | A refused change leaves nothing in the database | `test_service_with_sql_repository_rolls_back_a_refused_block` (DB) |
| Team time rule (#14, #16) | Services keep naive UTC; the page shows and takes Istanbul time | `test_blocks_keep_naive_utc_times_and_are_found_by_day` (DB), `test_slot_over_midnight_sees_a_block_on_the_next_day`, `test_staff_blocks_a_time_in_istanbul_time` (web), `test_schedule_shows_blocks_and_bookings_of_the_istanbul_day` (web) |
| NFR-01 | Usable on a phone | manual check, section 4 |
| Robustness | Unknown facility or wrong address | `test_unknown_facility_is_reported`, `test_block_of_unknown_facility`, `test_unknown_facility` (DB), `test_block_for_an_unknown_facility` (web), `test_wrong_facility_or_date_in_the_address` (web) |

## 4. Test design
- **Equivalence classes and boundary values.** Capacity: 1 (refused), 2 (smallest accepted), 0, negative, 2.5, `"10"` as text and `True` (all refused). Name: empty, only spaces, 100 characters (accepted), 101 characters (refused). Reason: empty, only spaces, 201 characters (refused).
- **Time boundaries.** Time ranges are half-open `[start, end)`, like `TimeSlot.overlaps` and the database's `tstzrange`. A block 09:00–12:00 and a booking 12:00–13:00 do **not** overlap; 11:00–13:00 does. A slot from 23:00 to 01:00 is checked against both days.
- **State-based tests.** Every event status was tested once against the facility schedule: pending, open and full hold the slot; cancelled, rejected and completed free it.
- **Negative tests.** Wrong role, unknown facility, end before start, overlapping input. Each one checks the error type and that nothing was stored (`InMemoryUnitOfWork.rollbacks`, row count in the database).
- **Concurrency.** The row lock is tested with a second database connection: while the first transaction holds `SELECT … FOR UPDATE`, `SELECT … FOR UPDATE NOWAIT` from the second connection fails with `LockNotAvailable`.
- **Manual test (NFR-01).** The Facility Management page was used in a browser with the demo data (`scripts/run_demo.py`) as facility staff, at desktop width and at 375 px: list, schedule, add facility, add block. No horizontal scrolling at 375 px (`scrollWidth` = 375).

## 5. Defects found while testing

| # | Found by | Defect | Fix |
|---|---|---|---|
| 1 | Code review before the first test run | `SqlFacilityRepository` called `session.rollback()` itself after a constraint error, which would also undo the other work of the same request | Removed; only the service's `UnitOfWork` rolls back (Design Report 7.1) |
| 2 | Database tests | The local test database refused the migration (`must be owner of extension btree_gist`) | Setup problem, not code: the extension had been created by hand with another user. Documented setup in the database README is correct |
| 3 | Web test `test_block_over_an_event_booking_is_refused` | Blocking over an event showed the student message "Please choose another time or facility" | The page shows the service text "An event is booked in this time, so it cannot be blocked." |
| 4 | Web tests | Test events were created in UTC but `fakes.slot()` takes Istanbul time, so they were 3 hours off | Tests use Istanbul time like the rest of `tests/web` |
| 5 | Manual test at 375 px | On a phone the schedule was below the *Add a facility* form, so choosing a facility seemed to do nothing | Facility links jump to the schedule (`#schedule`) |

## 6. Limits and what integration testing (task 4.2) must check
- The unit tests use stand-ins for `AuthService` and the event repository. After tasks 3.2 and 3.4: run the 6 requirement tests of section 2 with the real services, and check that the real `EventRepository.active_on` returns pending, open and full events that overlap the UTC day.
- `check_bookable` must be called by `EventService.create_event` **after** `uow.begin()` and before the event is stored, so the row lock covers the whole booking.
- The database tests run only on a computer with `TEST_DATABASE_URL`; CI skips them. A PostgreSQL service in CI would run them on every pull request (suggestion for task 3.7).
- `app.py` still builds the in-memory repositories. After the wiring of the SQL classes (task 3.2), the page must be tried once more on the Render deployment.
