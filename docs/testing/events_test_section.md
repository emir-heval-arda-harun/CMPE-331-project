[System.IO.File]::WriteAllText("$PWD\docs\testing\events_test_section.md", @'
# Events Testing Section

## Scope and Approach
Covers the Events domain across UC-04, UC-05, UC-06, UC-09, UC-10, UC-11, and UC-12 (including BR-04, BR-05, BR-07, BR-08, BR-11 to BR-18, and NFR-04). Combines service-level unit tests (`tests/test_event_service.py`), use-case tests (`test_uc04_create_event.py` through `test_uc12_review_event_requests.py`), and database repository tests (`tests/db/test_event_repository.py`).

## Results
- Unit and use-case suite: 56 passed, 0 failed (30 requirement tests across UC-04, UC-05, UC-06, UC-09, UC-10, UC-11, and UC-12 plus 26 unit tests in `tests/test_event_service.py`).
- Database tests: 8 tests in `tests/db/test_event_repository.py` are skipped locally without PostgreSQL and run in CI with `TEST_DATABASE_URL`, covering `SqlEventRepository`.
- Environment: Verified locally on Python 3.14.8 (`pytest-9.2.0`), while CI runs on Python 3.12 with `TEST_DATABASE_URL`.
- Coverage: `src/campusevent/events.py` reaches 96% (235 statements, 11 missed, 60 branches, 2 partial). Full-suite coverage is 97% in `docs/tests/coverage/README.md` (with repositories at 95–100% when run with PostgreSQL).

## Traceability
Representative test functions mapped to requirements and business rules:
- `test_student_cannot_join_twice` -> UC-06 2a, BR-07
- `test_join_full_event_raises_full_error` / full-capacity transitions -> UC-06, BR-08
- `test_only_the_organizer_can_cancel` -> UC-11, NFR-04
- `test_organizer_withdraws_pending_request_releases_slot` -> UC-11, BR-11
- `test_admin_approves_pending_event_request` / `test_admin_rejects_with_reason` -> UC-12, BR-12 to BR-18
- `test_activity_history_lists_completed_events` -> UC-09
- `test_leave_reopens_full_event` -> UC-10

## Test Design
Uses isolated in-memory fakes and a deterministic clock in `tests/test_event_service.py`, and shared fixtures/helpers (`verified_user`, `admin_user`, `campus_hall`, `slot`, `open_event`) in the use-case test files.

## Defects Found
- Reviews of #33 found incorrect exception types, a missing `get_event`, past events, and unchanged statuses, which were fixed in #38 (matching items 11–14 of #59).
- N+1 query performance issues were identified in #52 and addressed on the #58 branch (matching items 11–14 of #59).

## Limits
- Running only the Events tests reports 44% across the subset of files touched in that run; see `docs/tests/coverage/README.md` for the 97% full-suite coverage.
- `tests/db/test_event_repository.py` requires PostgreSQL (`TEST_DATABASE_URL`) and browser/UI flows are outside this section.
'@, [System.Text.UTF8Encoding]::new($false))
