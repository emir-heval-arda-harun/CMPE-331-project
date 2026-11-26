# Events Testing Section

## Scope and Approach
Covers the Events domain across UC-04, UC-05, UC-06, UC-09, UC-10, UC-11, and UC-12 (including BR-04 to BR-08, BR-11 to BR-18, NFR-02 and NFR-04). Combines service-level unit tests (`tests/test_event_service.py`), use-case tests (`test_uc04_create_event.py` through `test_uc12_review_event_requests.py`), and database repository tests (`tests/db/test_event_repository.py`).

## Results
- Unit and use-case suite: 56 passed, 0 failed (30 requirement tests across UC-04, UC-05, UC-06, UC-09, UC-10, UC-11, and UC-12 plus 26 unit tests in `tests/test_event_service.py`).
- Database tests: 8 tests in `tests/db/test_event_repository.py` are skipped locally without PostgreSQL and run in CI with `TEST_DATABASE_URL`, covering `SqlEventRepository`.
- Environment: Verified locally on Python 3.14.8 (`pytest-9.2.0`), while CI runs on Python 3.12 with `TEST_DATABASE_URL`.
- Coverage: `src/campusevent/events.py` reaches 96% (235 statements, 11 missed, 60 branches, 2 partial), and `src/campusevent/repositories/event_repository.py` (`SqlEventRepository`) reaches 95% (123 statements, 5 missed, 18 branches, 2 partial) on `main` (`439b670`, the final CI run 45879648843 of the report: 473 passed, 97% full-suite coverage, see `docs/tests/coverage/README.md`).

## Traceability
The full matrix (requirement → rule → tests → code → result) is in [`docs/tests/coverage/events.md`](../tests/coverage/events.md#traceability-matrix). It lists all 30 requirement tests, all 26 unit tests and all 8 database tests of this part in 29 rows, one per rule. All 29 rows pass on `main` (`439b670`, final CI run, 26.11.2026). In short:

| Use case | Business rules | Requirement tests | Unit tests | Database tests | NFR tests | Result |
|---|---|---|---|---|---|---|
| UC-04 Create event | BR-04, BR-05, BR-06, BR-14, BR-15, BR-16 | 5 | 7 | 3 | – | ✅ |
| UC-05 Browse and filter events | BR-14, BR-15 | 5 | 4 | 1 | – | ✅ |
| UC-06 Join event | BR-07, BR-08, BR-15 | 5 | 5 | 2 | – | ✅ |
| UC-09 Activity history | BR-11, BR-13 | 2 | 2 | 1 | – | ✅ |
| UC-10 Leave event | BR-08, BR-12 | 4 | 3 | 1 | – | ✅ |
| UC-11 Cancel event | BR-13, BR-16 | 4 | 3 | – | 1 | ✅ |
| UC-12 Review event requests | BR-16, BR-17, BR-18 | 7 | 7 | 1 | 1 | ✅ |

A test is counted under every use case whose rule it checks, so some tests count in two rows. BR-05 (the organizer is the first participant) is checked by `test_student_creates_event_request_and_joins_it_as_organizer` and `test_new_event_is_pending_and_organizer_is_first_participant`.

## Test Design
The unit tests use in-memory stand-ins for the facility and auth services and a **fixed clock** (`NOW` = 1 Nov 2026, 12:00; the events are on 1 Dec 2026 from 10:00 to 11:00 unless a test moves them, and some tests move the clock past the start or the end), so every time rule can be tested exactly at its edge. The requirement tests use the real services through `create_app()` with shared helpers (`verified_user`, `admin_user`, `campus_hall`, `slot`, `open_event`).

**Equivalence classes and boundary values**

| Input | Refused | Accepted | Tests |
|---|---|---|---|
| Capacity | 1, 0, −3; facility capacity + 1 (21 in a hall for 20) | 2 (smallest; *Full* with the second person) | `test_capacity_below_two_is_rejected`, `test_capacity_above_the_facility_capacity_is_rejected`, `test_event_with_invalid_capacity_is_rejected`, `test_capacity_cannot_exceed_the_facility_capacity`, `test_event_becomes_full_and_rejects_new_participants` |
| Title, category | empty or only spaces; title of 121 characters, category of 61 | up to 120 and 60 characters; any free text (`"chess club meeting"`) | `test_title_and_category_are_required_and_limited`, `test_any_free_text_category_is_accepted` |
| Category form | – | `"  Board   GAMES "` is stored as `"board games"`, `"İlk Yardım"` as `"ilk yardım"`; the search `" SPORTS "` finds `"Sports"` | `test_category_is_stored_trimmed_and_lower_case`, `test_search_lists_only_open_events_and_filters_combine` |
| Participants | a second join by the same student; the 4th person in an event for 3 | the 3rd person (organizer + 2) | `test_join_twice_is_rejected_and_capacity_is_never_exceeded` |
| Start time | an event in the past (2025); join, leave or cancel at 10:30 for an event that started at 10:00 | the same actions before 10:00 | `test_event_in_the_past_is_refused`, `test_cannot_leave_or_cancel_after_the_start_time` |
| Expiry (BR-18) | approving at 11:00 a request that started at 10:00 | at 10:00 a request for 09:00 expires, one for 15:00 stays pending | `test_request_not_reviewed_before_its_start_expires_and_cannot_be_approved`, `test_unreviewed_requests_are_rejected_at_their_start_time` |
| Rejection reason | `"   "` | `" Not suitable "`, stored as `"Not suitable"` | `test_reject_needs_a_reason_frees_the_slot_and_keeps_the_reason` |
| Search filters | – | each filter alone, all three together, a day without events (empty list) | `test_search_lists_only_open_events_and_filters_combine`, `test_no_result_returns_empty_list` |

**Status changes (state transition testing).** Every allowed change of `EventStatus` and the most important forbidden ones have a test:

| From | Event | To | Test |
|---|---|---|---|
| – | the organizer creates the event | *Pending* | `test_new_event_is_pending_and_organizer_is_first_participant` |
| *Pending* | the admin approves | *Open* | `test_admin_approves_and_the_event_becomes_listed` |
| *Pending* | the admin rejects with a reason | *Rejected* | `test_reject_needs_a_reason_frees_the_slot_and_keeps_the_reason` |
| *Pending* | nobody reviews it before the start | *Rejected* (automatic reason) | `test_unreviewed_requests_are_rejected_at_their_start_time` |
| *Pending* | the organizer withdraws it | *Cancelled* | `test_organizer_withdraws_pending_request_and_frees_the_slot` |
| *Open* | the last free place is taken | *Full* | `test_event_becomes_full_and_open_again_when_someone_leaves` |
| *Full* | a participant leaves | *Open* | `test_event_becomes_full_and_open_again_when_someone_leaves` |
| *Open* | the organizer cancels before the start | *Cancelled* | `test_only_the_organizer_can_cancel` |
| *Open* | the end time has passed | *Completed* | `test_after_the_end_an_event_is_completed_and_in_the_history` |
| *Pending* | a student tries to join | refused, stays *Pending* | `test_pending_event_cannot_be_joined` |
| *Open* | the admin tries to reject it | refused (only pending requests are reviewed) | `test_only_admins_review_and_only_pending_requests` |
| *Cancelled* | the organizer cancels again | refused | `test_cancelled_event_cannot_be_cancelled_again_and_frees_its_slot` |

**Roles and error types (NFR-04).** Every refused action is checked for the right error: `PermissionDeniedError` for the wrong role or someone else's event (cancel, review, list requests), `ValidationError` for wrong input or a wrong status, `AlreadyJoinedError`, `EventFullError`, `FacilityConflictError` and `NotFoundError` for their own cases.

## Defects Found
- Reviews of #33 found incorrect exception types, a missing `get_event`, past events, and unchanged statuses, which were fixed in #38 (matching items 11–13 of #59).
- N+1 query performance issues were identified in #52 and addressed in #58 (matching item 14 of #59).

## Limits
- Running only the Events tests reports 44% across the subset of files touched in that run; see `docs/tests/coverage/README.md` for the 97% full-suite coverage.
- `tests/db/test_event_repository.py` requires PostgreSQL (`TEST_DATABASE_URL`) and browser/UI flows are outside this section.
