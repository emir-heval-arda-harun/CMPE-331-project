# Events Non-Functional Tests

## NFR-02 - Search and Page Performance
- `test_nfr02_search_is_fast_with_1000_open_events` in `tests/test_nfr.py` (outside the 56 unit/UC tests): passed.
- PostgreSQL timings: #58 is not merged yet; in the review of #58 on its branch, whole-page timings (Find Events, My Activities, Event Requests) were 0.33–0.56 s (compared to 2.1–3.4 s reported before #58 in #52).

## NFR-04 - Authorization and Ownership
- `test_nfr04_only_the_organizer_can_cancel_an_event` in `tests/test_nfr.py`: passed.
- `test_nfr04_only_an_admin_can_approve_or_reject_event_requests` in `tests/test_nfr.py`: passed.
