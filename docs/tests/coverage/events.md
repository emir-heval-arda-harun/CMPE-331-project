# Events Coverage

Full-suite project coverage is 97% in [docs/tests/coverage/README.md](README.md), where data access repositories reach 95–100% when run against PostgreSQL in CI (`TEST_DATABASE_URL`).

| File / Component | Coverage | Notes |
|---|---|---|
| `src/campusevent/events.py` | 96% (235 stmts, 11 miss, 60 branch, 2 partial) | Events service logic |
| `src/campusevent/repositories/event_repository.py` (`SqlEventRepository`) | 95–100% (repositories range in CI with PostgreSQL) | Skipped locally without `TEST_DATABASE_URL`; runs in CI with PostgreSQL |

The 44% figure seen when running only the Events tests covers only the subset of files touched in that run; see [docs/tests/coverage/README.md](README.md) for the full-suite total (97%).

## Requirement -> Test -> Code Mapping
- UC-04 (`test_uc04_create_event.py`, `test_event_service.py`) -> `EventService.create_event`
- UC-05 (`test_uc05_browse_and_filter_events.py`, `test_event_service.py`) -> `EventService.search_events`
- UC-06 (`test_uc06_join_event.py`, `test_event_service.py`) -> `EventService.join_event` (`test_student_cannot_join_twice` -> UC-06 2a, BR-07)
- UC-09 (`test_uc09_activity_history.py`, `test_event_service.py`) -> `EventService.complete_event`, `EventService.get_activity_history`
- UC-10 (`test_uc10_leave_event.py`, `test_event_service.py`) -> `EventService.leave_event`
- UC-11 (`test_uc11_cancel_event.py`, `test_event_service.py`) -> `EventService.cancel_event` (`test_only_the_organizer_can_cancel` -> UC-11, NFR-04)
- UC-12 (`test_uc12_review_event_requests.py`, `test_event_service.py`) -> `EventService.list_pending_events`, `approve_event`, `reject_event`, `expire_pending_requests`, `list_my_requests`

## Uncovered Lines in `src/campusevent/events.py`
- Line 37: Real system clock fallback when no explicit clock is provided.
- Line 213: `continue` in `expire_pending_requests` when a request is no longer pending.
- Lines 221–223: Rollback in `expire_pending_requests` on error.
- Line 326: Guard in `complete_event` checking that only an open or full event can be completed.
- Lines 330–332: Rollback in `complete_event` on error.
- Lines 351–352: Concurrent update / conflict path when another request modifies the same slot or record.

