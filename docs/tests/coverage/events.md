# Events Coverage

Full-suite project coverage is 97% in [docs/tests/coverage/README.md](README.md), where data access repositories reach 95–100% when run against PostgreSQL in CI (`TEST_DATABASE_URL`).

| File / Component | Coverage | Notes |
|---|---|---|
| `src/campusevent/events.py` | 96% (235 stmts, 11 miss, 60 branch, 2 partial) | Events service logic |
| `src/campusevent/repositories/event_repository.py` (`SqlEventRepository`) | 95% (123 stmts, 5 miss, 18 branch, 2 partial) on `main` (`0c795fb`) | Skipped locally without `TEST_DATABASE_URL`; runs in CI with PostgreSQL |

The 44% figure seen when running only the Events tests covers only the subset of files touched in that run; see [docs/tests/coverage/README.md](README.md) for the full-suite total (97%).

## Traceability matrix
Requirement → rule → tests → code, with the result on `main` (CI run 45851087074 of `22825b5`, 26.11.2026: 446 passed, 0 failed). Req = the requirement tests `tests/test_uc04_*` to `tests/test_uc12_*`, Unit = `tests/test_event_service.py`, DB = `tests/db/test_event_repository.py` (PostgreSQL 16 in CI), NFR = `tests/test_nfr.py`. All 30 requirement tests, all 26 unit tests and all 8 database tests of the events part are in the table.

| Requirement | Rule | Tests | Code | Result |
|---|---|---|---|---|
| UC-04, BR-15, BR-05 | A new event is a *Pending* request, and the organizer is its first participant | Req `test_student_creates_event_request_and_joins_it_as_organizer`; Unit `test_new_event_is_pending_and_organizer_is_first_participant`; DB `test_add_and_get_keep_naive_utc_and_the_participants` | `EventService.create_event`, `SqlEventRepository.add` | ✅ |
| UC-04, BR-04 | Capacity is at least 2 and at most the capacity of the facility | Req `test_event_with_invalid_capacity_is_rejected`, `test_capacity_cannot_exceed_the_facility_capacity`; Unit `test_capacity_below_two_is_rejected`, `test_capacity_above_the_facility_capacity_is_rejected` | `create_event`, `FacilityService.check_bookable` | ✅ |
| UC-04 | Title and category are required; at most 120 and 60 characters | Unit `test_title_and_category_are_required_and_limited` | `create_event` (`TITLE_MAX`, `CATEGORY_MAX`) | ✅ |
| UC-04, BR-14 | Any free-text category; stored trimmed and in lower case (also the Turkish İ) | Req `test_any_free_text_category_is_accepted`; Unit `test_category_is_stored_trimmed_and_lower_case` | `create_event` | ✅ |
| UC-04 | An event cannot start in the past | Unit `test_event_in_the_past_is_refused` | `create_event` (clock) | ✅ |
| UC-04, UC-07, BR-06, BR-16 | A pending request holds its facility slot; two active events never overlap in one facility | Req `test_pending_request_holds_the_facility_slot`; Unit `test_pending_request_holds_the_slot_and_cancel_frees_it`; DB `test_overlapping_active_event_becomes_a_facility_conflict`, `test_active_on_finds_events_that_overlap_the_utc_day` | `create_event`, `check_bookable`, `SqlEventRepository.active_on`, constraint `ex_event_facility_no_overlap` | ✅ |
| UC-05, BR-15 | Only *Open* events are listed; a pending request never | Req `test_pending_request_is_not_listed_until_approved`; Unit `test_search_lists_only_open_events_and_filters_combine` | `search_events` | ✅ |
| UC-05, BR-14 | Filters by category, date and keyword, also combined; sorted by start time; no match gives an empty list | Req `test_filter_by_category`, `test_filter_by_date`, `test_filter_by_keyword_in_the_title`, `test_no_result_returns_empty_list`; Unit `test_search_lists_only_open_events_and_filters_combine` | `search_events`, `SqlEventRepository.list_by_status` | ✅ |
| UC-05 | Full events only when asked; ended events are not listed | Unit `test_full_events_are_listed_only_when_asked`, `test_after_the_end_an_event_is_completed_and_in_the_history` | `search_events(only_open=False)` | ✅ |
| UC-05, UC-06 (Event Details) | Any event can be opened by id; an unknown id is *not found* | Unit `test_get_event_returns_any_status_and_unknown_id_is_not_found`; DB `test_unknown_event_is_not_found` | `get_event`, `SqlEventRepository.get` | ✅ |
| UC-06 | A student joins an open, upcoming event | Req `test_student_joins_open_event`; Unit `test_cannot_leave_or_cancel_after_the_start_time` (joining after the start is refused) | `join_event` | ✅ |
| UC-06, BR-15 | A pending request cannot be joined | Req `test_pending_request_cannot_be_joined`; Unit `test_pending_event_cannot_be_joined` | `join_event` | ✅ |
| UC-06 alt. 2a, BR-07 | A student joins at most once, and never above the capacity | Req `test_student_cannot_join_twice`; Unit `test_join_twice_is_rejected_and_capacity_is_never_exceeded` | `join_event` | ✅ |
| UC-06, UC-10, BR-08 | *Full* at capacity, *Open* again when a participant leaves | Req `test_event_becomes_full_and_rejects_new_participants`, `test_full_event_becomes_open_again_when_a_participant_leaves`; Unit `test_event_becomes_full_and_open_again_when_someone_leaves`; DB `test_save_changes_status_and_adds_and_removes_participants` | `join_event`, `leave_event`, `SqlEventRepository.save` | ✅ |
| UC-09, BR-11, BR-13 | The history shows only completed events, newest first; never cancelled or upcoming ones | Req `test_completed_events_appear_in_history`, `test_upcoming_events_are_not_in_history`; Unit `test_history_shows_completed_events_newest_first_and_never_cancelled_ones`, `test_after_the_end_an_event_is_completed_and_in_the_history`; DB `test_event_service_with_postgresql_from_request_to_history` | `complete_event`, `get_activity_history`, `SqlEventRepository.list_by_participant` | ✅ |
| UC-10 | A participant leaves and frees a place | Req `test_participant_leaves_event_and_frees_a_place` | `leave_event` | ✅ |
| UC-10, BR-12 | The organizer cannot leave their own event; a user who did not join cannot leave | Req `test_user_who_did_not_join_cannot_leave`; Unit `test_organizer_cannot_leave_and_non_participant_cannot_leave` | `leave_event` | ✅ |
| UC-10, UC-11 | No leaving or cancelling after the start time | Unit `test_cannot_leave_or_cancel_after_the_start_time` | `leave_event`, `cancel_event` (clock) | ✅ |
| UC-11 | The organizer cancels; the event is no longer listed | Req `test_organizer_cancels_event` | `cancel_event` | ✅ |
| UC-11, BR-13, NFR-04 | Only the organizer can cancel | Req `test_only_the_organizer_can_cancel`; Unit `test_only_the_organizer_can_cancel`; NFR `test_nfr04_only_the_organizer_can_cancel_an_event` | `cancel_event` | ✅ |
| UC-11, BR-13, BR-16 | A cancelled event or withdrawn request frees its slot; it cannot be cancelled twice | Req `test_cancelled_event_frees_the_facility_slot`, `test_organizer_withdraws_pending_request_and_frees_the_slot`; Unit `test_cancelled_event_cannot_be_cancelled_again_and_frees_its_slot` | `cancel_event`, `FacilityService.is_available` | ✅ |
| UC-12 | The admin sees the pending requests; an approved request becomes *Open* and is listed | Req `test_admin_sees_pending_requests`, `test_approved_request_becomes_open_and_listed`; Unit `test_admin_approves_and_the_event_becomes_listed` | `list_pending_events`, `approve_event` | ✅ |
| UC-12, BR-16, BR-17 | A rejection needs a reason; it frees the slot and the organizer sees the reason | Req `test_rejection_needs_a_reason`, `test_rejected_request_frees_the_slot_and_tells_the_organizer_why`; Unit `test_reject_needs_a_reason_frees_the_slot_and_keeps_the_reason` | `reject_event` | ✅ |
| UC-12, BR-17, NFR-04 | Only an admin reviews; only pending requests can be reviewed | Req `test_only_pending_requests_can_be_reviewed`; Unit `test_only_admins_review_and_only_pending_requests`; NFR `test_nfr04_only_an_admin_can_approve_or_reject_event_requests` | `approve_event`, `reject_event`, `list_pending_events` | ✅ |
| UC-12, BR-18 | A request not reviewed before its start is rejected automatically | Req `test_request_not_reviewed_before_start_expires`; Unit `test_request_not_reviewed_before_its_start_expires_and_cannot_be_approved`, `test_unreviewed_requests_are_rejected_at_their_start_time` | `expire_pending_requests` | ✅ |
| UC-12 | The organizer follows their own requests in every status | Req `test_organizer_follows_own_requests_in_every_status`; Unit `test_organizer_sees_all_own_requests_in_any_status`; DB `test_lists_by_status_participant_and_organizer` | `list_my_requests`, `SqlEventRepository.list_by_organizer` | ✅ |
| UC-12 step 5 | The organizer gets the decision by e-mail; a mail error does not undo the decision | Unit `test_decision_notification_is_sent_and_a_mail_error_does_not_undo_it` | `approve_event`, `reject_event` (`notify_decision`) | ✅ |
| Design report 5.3, 7.1 | The event row is locked while it changes (join, leave, cancel, review) | DB `test_get_for_update_locks_the_event_row` | `SqlEventRepository.get_for_update` (`SELECT … FOR UPDATE`) | ✅ |
| NFR-02 | Search stays under 2 s with 1,000 open events | NFR `test_nfr02_search_is_fast_with_1000_open_events`; PostgreSQL timing in the [non-functional tests](../non-func-tests/events.md) | `search_events`, `SqlEventRepository` (`selectinload`, #58) | ✅ |

**Requirements coverage:** all 7 use cases of this part (UC-04, UC-05, UC-06, UC-09, UC-10, UC-11, UC-12) and all 13 business rules they use (BR-04 to BR-08 and BR-11 to BR-18; BR-06 and BR-16 are shared with the facilities part, BR-14 with profiles) have passing tests: 29 of 29 rows ✅.

## Uncovered Lines in `src/campusevent/events.py`
- Line 37: Real system clock fallback when no explicit clock is provided.
- Line 213: `continue` in `expire_pending_requests` when a request is no longer pending.
- Lines 221–223: Rollback in `expire_pending_requests` on error.
- Line 326: Guard in `complete_event` checking that only an open or full event can be completed.
- Lines 330–332: Rollback in `complete_event` on error.
- Lines 351–352: Concurrent update / conflict path when another request modifies the same slot or record.

## Uncovered Lines in `src/campusevent/repositories/event_repository.py`
- Missed lines/branches (`0c795fb`): `78`, `116->exit`, `149`, `183–185`.
