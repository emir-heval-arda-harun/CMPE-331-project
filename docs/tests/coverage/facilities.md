# Coverage – facilities (UC-07, UC-08)

**Author:** Harun Gündaş · **Date of the results:** 20.11.2026 · **Code:** `main` with PR #22 · Part of the Software Testing Report, see the [facilities section](../../testing/facility_test_section.md).

## Traceability matrix
Requirement → rule → tests → code, with the result on 20.11.2026. Unit = `tests/test_facility_service.py`, DB = `tests/db/test_facility_repository.py`, Web = `tests/web/test_web_facilities.py`, Req = the requirement tests `tests/test_uc07_*`, `tests/test_uc08_*`, `tests/test_nfr.py`.

| Requirement | Rule | Tests | Code | Result |
|---|---|---|---|---|
| UC-08 step 1 | Staff add a facility with name and capacity | Unit `test_staff_adds_facility`; DB `test_add_get_find_and_list`; Web `test_staff_adds_a_facility` | `FacilityService.add_facility`, `FacilityRepository.add`, route `add_facility` | ✅ |
| UC-08 alt. 1a, BR-09, NFR-04 | Only facility staff manage facilities and blocks | Unit `test_student_cannot_add_facility_or_block`, `test_student_cannot_remove_a_block`; Web `test_only_staff_can_open_the_page`, `test_only_staff_can_remove_a_block`; Req `test_student_cannot_manage_facilities`, `test_nfr04_student_cannot_manage_facilities`, `test_nfr04_student_cannot_block_a_facility` | `AuthService.require_role` in every `FacilityService` change, `staff_required` | ✅ (Req with PR #23) |
| UC-08 alt. 1b | Capacity is a whole number of at least 2 | Unit `test_capacity_must_be_a_whole_number_of_at_least_2`, `test_smallest_capacity_and_longest_name_are_accepted`; Web `test_wrong_capacity_is_explained_and_the_name_is_kept` | `add_facility` | ✅ |
| Data design §6 | Name required, at most 100 characters, unique without regard to case | Unit `test_name_is_required_and_short`, `test_facility_names_are_unique_without_regard_to_case`; DB `test_duplicate_name_becomes_a_validation_error`; Web `test_duplicate_facility_name_is_refused` | `add_facility`, `find_by_name`, constraint `uq_facility_name` | ✅ |
| UC-08 step 2 | Staff block a time with a reason | Unit `test_block_makes_the_facility_unavailable`, `test_block_needs_a_short_reason`, `test_block_must_end_after_it_starts`, `test_blocks_get_an_id`; Web `test_staff_blocks_a_time_in_istanbul_time`, `test_wrong_block_input_is_explained` | `FacilityService.add_block`, route `add_block` | ✅ |
| UC-08 alt. 2a, BR-10 | Blocks of one facility do not overlap | Unit `test_overlapping_blocks_are_rejected`; DB `test_overlapping_blocks_become_a_validation_error`; Web `test_overlapping_block_is_refused_and_the_form_is_kept` | `add_block`, constraint `ex_facility_block_no_overlap` | ✅ |
| UC-08 alt. 2b (#19) | Staff remove a block; its time is free again | Unit `test_staff_removes_a_block_and_the_time_is_free_again`, `test_removing_an_unknown_block`, `test_a_removed_block_cannot_be_removed_twice`; DB `test_blocks_get_ids_and_can_be_removed`, `test_service_removes_a_block_from_the_database`; Web `test_staff_removes_a_block`, `test_each_block_has_a_remove_button_with_a_confirmation`, `test_removing_an_unknown_block_or_one_of_another_facility` | `FacilityService.remove_block`, `FacilityRepository.get_block` / `remove_block`, route `remove_block` | ✅ |
| BR-06 | An event and a block never share a slot | Unit `test_block_over_a_booked_event_is_rejected`, `test_check_bookable_refuses_busy_slots`; Web `test_block_over_an_event_booking_is_refused`; Req `test_overlapping_event_in_same_facility_is_rejected` | `add_block`, `check_bookable`, constraint `ex_event_facility_no_overlap` | ✅ (Req since #33) |
| UC-08 postcondition | Students cannot book a blocked time | Unit `test_check_bookable_refuses_busy_slots`; Web `test_a_blocked_time_cannot_be_booked`; Req `test_staff_blocks_facility_and_events_cannot_use_it` | `check_bookable` | ✅ (Req since #33) |
| UC-07 step 2 | The schedule shows the blocks and events of a day, sorted, with reasons and titles | Unit `test_schedule_lists_blocks_and_active_events_sorted`, `test_get_bookings_lists_active_events_of_the_day_sorted`; Web `test_schedule_shows_blocks_and_bookings_of_the_istanbul_day`, `test_schedule_shows_event_titles_and_pending_requests`; Req `test_schedule_shows_existing_events` | `get_schedule`, `get_blocks`, `get_bookings`, `_day_schedule` | ✅ (Req since #33) |
| UC-07 step 2, BR-16 (CR-01) | Pending, open and full events hold their slot; cancelled, rejected and completed events free it | Unit `test_active_events_hold_their_slot`, `test_inactive_events_free_their_slot`; Web `test_cancelled_events_do_not_show_in_the_schedule` | `ACTIVE_STATUSES`, `_active_events` | ✅ |
| UC-07 step 3–4, alt. 3a | Conflict check for a new event (`check_bookable`, used by UC-04) | Unit `test_check_bookable_returns_the_facility`, `test_check_bookable_refuses_busy_slots`, `test_check_bookable_unknown_facility` | `check_bookable`, `is_available` | ✅ |
| UC-04 alt. 3b, BR-04 | Event capacity at most the facility capacity | Unit `test_check_bookable_refuses_more_people_than_the_facility_holds` | `check_bookable` | ✅ |
| Design report 5.3, 7.1 (risk R-01) | The facility row is locked while a booking is checked | DB `test_get_for_update_locks_the_facility_row` | `get_for_update` (`SELECT … FOR UPDATE`) | ✅ |
| Design report 7.1 | A refused change leaves nothing in the database | DB `test_service_with_sql_repository_rolls_back_a_refused_block` | `UnitOfWork` in every service method | ✅ |
| Team time rule (#14, #16) | Services keep naive UTC; the page shows and takes Istanbul time | DB `test_blocks_keep_naive_utc_times_and_are_found_by_day`; Unit `test_slot_over_midnight_sees_a_block_on_the_next_day`; Web `test_staff_blocks_a_time_in_istanbul_time`, `test_event_of_the_evening_before_is_not_on_the_next_day` | `_to_db` / `_from_db`, `_days`, `_day_schedule` | ✅ |
| NFR-05 | The schedule shows no organizer names or e-mail addresses | Web `test_schedule_shows_no_organizer_names_or_e_mails` | `_day_schedule` | ✅ |
| NFR-01 | Usable on a phone | manual, see [non-functional tests](../non-func-tests/facilities.md) | `facilities.html` | ✅ |
| Robustness | Unknown facility or wrong address | Unit `test_unknown_facility_is_reported`, `test_block_of_unknown_facility`; DB `test_unknown_facility`; Web `test_block_for_an_unknown_facility`, `test_wrong_facility_or_date_in_the_address` | `get`, routes `manage`, `add_block` | ✅ |

**Requirements coverage:** 19 of 19 rows have passing tests (100 %). All 6 requirement tests pass on `main` since #33 (23.11.2026); before that 3 of them waited for `EventService.create_event` (task 3.4), and their rules were covered by unit and web tests in the same rows.

## Code coverage
Measured with coverage.py 7.17, statements **and** branches, all three facility suites (76 tests) on a local PostgreSQL 16:

| File | Statements | Missed | Branches | Partial | Coverage |
|---|---|---|---|---|---|
| `src/campusevent/facilities.py` | 120 | 0 | 26 | 0 | **100 %** |
| `src/campusevent/repositories/facility_repository.py` | 132 | 2 | 12 | 2 | **97 %** |
| `src/campusevent/web/facility_routes.py` | 92 | 0 | 18 | 0 | **100 %** |
| **Total** | 344 | 2 | 56 | 2 | **99 %** |

**Not covered:** lines 166 and 210 of `facility_repository.py`, the `raise` for an `IntegrityError` of a constraint that is not `uq_facility_name` or `ex_facility_block_no_overlap` (for example a foreign key). The service checks the facility first, so these errors cannot happen in a normal flow; the line only passes the error on unchanged.

**Without a database (like CI):** 84 %. The `SqlFacilityRepository` part is then not run (58 % of the repository file); the service and the page stay at 100 %.

### How to measure
```
pip install coverage
python -m coverage run --branch --source=src/campusevent -m pytest tests/test_facility_service.py tests/db/test_facility_repository.py tests/web/test_web_facilities.py
python -m coverage report -m --include="*facilit*"
```
Use `coverage run` as above. `pytest --cov=campusevent.facilities` (pytest-cov with a module name) makes the database tests fail inside SQLAlchemy (`'InternalTraversal' object is not callable`); this is a tool problem, not a problem of the code. The project-wide `pytest --cov` of CI (#36, source set in `pyproject.toml`) and `--cov=src/campusevent` work with the database tests (checked on 22 Nov 2026); only the dotted module name breaks them.
