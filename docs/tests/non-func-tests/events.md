# Events Non-Functional Tests

## NFR-02 - Search and Page Performance
- `test_nfr02_search_is_fast_with_1000_open_events` in `tests/test_nfr.py` (outside the 56 unit/UC tests): passed.
- PostgreSQL timings: #58 (merged 25.11) resolved the N+1 queries; as measured on `main` (`4f29421`) after the merge (#37, #59), whole-page timings on PostgreSQL 18 are Find Events 0.32–0.48 s, My Activities 0.47 s, and Event Requests 0.35–0.46 s (before #58, on 23.11: 2.1–3.4 s, over the 2 s of NFR-02, the same measurement as in the web UI section: 2.1–3.2 s on the server and up to 3.4 s in the browser, reported in #52).

## NFR-04 - Authorization and Ownership
- `test_nfr04_only_the_organizer_can_cancel_an_event` in `tests/test_nfr.py` (UC-11, BR-13): passed.
- `test_nfr04_only_an_admin_can_approve_or_reject_event_requests` in `tests/test_nfr.py` (UC-12, BR-17): passed.
