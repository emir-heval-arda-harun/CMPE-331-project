# Events TDD Evidence (Refs #34, Item D)

Requirement tests for UC-04 to UC-12 were written before the implementation, showing a clear red -> green progression followed by review fixes:

1. Red: The requirement tests for UC-04 to UC-12 were written with the requirements (#5, 17.10; UC-12 in #8, 18.11), while `EventService` only raised `NotImplementedError`. CI on `main` failed with 36 `NotImplementedError` failures until #33 was merged (23.11).
2. Green: The initial implementation in #33 (21.11) made the requirement tests pass, and reviews of #33 exposed edge-case gaps (wrong exception types, missing `get_event`, past events, and statuses that did not change). There was no failing test written beforehand for the N+1 queries.
3. Follow-up fixes: Fixes in #38 (commits `1703b5f` and `12f519d`) resolved the #33 review findings so all requirement and service tests pass (56 passed across unit and use-case tests, plus `tests/test_nfr.py` and CI `tests/db/test_event_repository.py`), while #58 (merged 25.11) addressed the N+1 query issues.
