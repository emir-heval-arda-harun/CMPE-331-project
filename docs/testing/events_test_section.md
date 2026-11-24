@'

\# Events Testing Section



\## Scope and Approach

Covers the Events domain across UC-04, UC-05, UC-06, UC-09, UC-10, UC-11, and UC-12 (BR-04, BR-05, BR-07, BR-08, BR-11 to BR-18, and NFR-04). Combines service-level unit tests (tests/test\_event\_service.py) and use-case tests (test\_uc04\_create\_event.py, test\_uc05\_browse\_and\_filter\_events.py, test\_uc06\_join\_event.py, test\_uc09\_activity\_history.py, test\_uc10\_leave\_event.py, test\_uc11\_cancel\_event.py, test\_uc12\_review\_event\_requests.py) with repository persistence checks (tests/db/test\_event\_repository.py).



\## Results

\- Unit \& Use-Case Suite: 56 passed (0 failed), consisting of 30 requirement tests across UC-04, UC-05, UC-06, UC-09, UC-10, UC-11, and UC-12 plus 26 unit tests in tests/test\_event\_service.py.

\- Database Tests: The 8 tests in tests/db/test\_event\_repository.py are skipped locally without PostgreSQL and run in CI with TEST\_DATABASE\_URL, covering SqlEventRepository.

\- Environment: Verified locally on Python 3.14.8 (pytest-9.2.0), while CI runs on Python 3.12 with TEST\_DATABASE\_URL.

\- Coverage Highlights: src/campusevent/events.py reaches 96% (235 statements, 11 missed, 60 branches, 2 partial branches); see docs/tests/coverage/events.md and docs/tests/coverage/README.md (97% full-suite coverage).



\## Traceability

\- UC-04: Pending initial status, organizer auto-membership, capacity bounds, free-text categories, slot reservation, and keeping pending requests hidden from public search until approved.

\- UC-05: Filtering by category, day, and keyword, and returning an empty list when no events match.

\- UC-06: Joining open events, transitioning to FULL at capacity, raising EventFullError when full, rejecting duplicate joins (AlreadyJoinedError), and blocking joins on non-open/pending events.

\- UC-09: Showing completed events with category metadata in history while excluding upcoming events.

\- UC-10: Freeing capacity when a participant leaves, reopening a FULL event to OPEN, and rejecting users who did not join.

\- UC-11: Organizer cancellation removing events from active search, blocking non-organizers (PermissionDeniedError), and freeing facility slots on cancellation or pending request withdrawal.

\- UC-12: Admin listing pending requests, approving (OPEN, reviewed\_by, listing, notification), rejecting with a required reason (freeing slot, recording reason, notification), rejecting blank reasons or non-pending reviews, holding slots/blocking joins while pending, expiring unreviewed past-start requests (REJECTED, reviewed\_by is None), and listing own requests across statuses.



\## Test Design

Uses tests/test\_event\_service.py with isolated fakes/in-memory state and deterministic clock injection alongside app fixture and tests/helpers.py (verified\_user, admin\_user, campus\_hall, slot, open\_event) in the UC test files.



\## Defects Found

\- Reviews of #33 identified incorrect exception types, a missing get\_event, past events, and unchanged statuses, which were fixed in #38.

\- N+1 query performance issues were identified in #52 and resolved in #58 (matching items 11 to 14 tracked in #59).



\## Limits

\- The 44% figure seen when running only the Events tests reflects only the files touched during that run; full-suite coverage is 97% in docs/tests/coverage/README.md.

\- PostgreSQL-backed repository tests require TEST\_DATABASE\_URL (run in CI), and browser/UI flows are outside this service/repository scope.

'@ | Set-Content -Encoding UTF8 docs\\testing\\events\_test\_section.md

