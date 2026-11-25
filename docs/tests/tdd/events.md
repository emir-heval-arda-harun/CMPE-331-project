# Events TDD Evidence (Refs #34, Item D)

Tests for #33 were not written strictly before the initial implementation; instead, red -> green progression is visible across the reviews and fixes:

1. Red: Reviews of #33 exposed failures/gaps in the requirement tests (wrong exception types, missing `get_event`, past events, and statuses that did not change). There was no failing test written for the N+1 queries.
2. Green: Fixes in #38 resolved the #33 review findings so the requirement and service tests pass (56 passed across unit and use-case tests, plus `tests/test_nfr.py` and CI `tests/db/test_event_repository.py`), while #58 addressed the N+1 query issues on its branch.
