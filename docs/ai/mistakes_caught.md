### 11. Wrong error types in EventService
- **What the assistant wrote:** `join_event` raised `ValidationError` when the event was full or the student had already joined, and `cancel_event` raised it when someone other than the organizer tried to cancel.
- **Effect:** The pages turn `EventFullError` and `AlreadyJoinedError` into 409 and `PermissionDeniedError` into 403. With `ValidationError` they answered 400, and four requirement tests failed (`test_only_the_organizer_can_cancel`, `test_nfr04_only_the_organizer_can_cancel_an_event`, the full-event test, and the join-twice test).
- **How it was caught:** Harun and Emir ran the whole suite against the real services while reviewing #33 (reviews of #33). The assistant's own unit test for joining twice expected `ValidationError` as well, so it passed.
- **Fix:** `PermissionDeniedError` for the non-organizer in #33; `EventFullError` and `AlreadyJoinedError` in #38 (commits of #38).
- **Lesson:** The assistant had not been given `exceptions.py` or the design report's error list, and wrote tests that agree with its own code. Errors follow the Software Design Report; roles raise `PermissionDeniedError` (`CLAUDE.md`).

### 12. Events in the past and statuses that never change
- **What the assistant wrote:** `create_event` accepted a start time in the past; the lists and `join_event` did not look at the time. Nothing called `complete_event` or `expire_pending_requests`, and `approve_event` approved a request whose start time had passed.
- **Effect:** Emir created an event for January 2025, approved it, saw it on Find Events, and a student joined it. The history stayed empty (BR-11) and pending requests never expired (BR-18).
- **How it was caught:** Emir tried these cases on the real pages (reviews of #33).
- **Fix:** Commits of #38: no events in the past, lists show upcoming events, `approve_event` refuses an expired request, and finished events and expired requests are settled before the lists are read. The test app gets a fixed clock.
- **Lesson:** Anything that depends on the date is tested with a clock that the test controls, not only with the dates that happen to be in the fixtures.

### 13. `get_event` missing
- **What the assistant did:** Implemented the methods named in the skeleton and the use cases, but not `get_event`, which Emir's pages call.
- **Effect:** Event Details, join, leave, cancel and "Add to calendar" answered 500.
- **How it was caught:** Emir ran his pages against the real `EventService`; with a stand-in `get_event` they all worked (reviews of #33).
- **Fix:** Commits of #38 add `get_event(event_id)` (`NotFoundError` for an unknown id).
- **Lesson:** The assistant is told which methods the other layers call, not only which use cases exist.

### 14. N+1 queries in `SqlEventRepository`
- **What the assistant wrote:** `_to_domain` reads `row.participants`, which loads the participants of each event with a separate `SELECT`.
- **Effect:** With 1,000 open events, Find Events took 2.1 to 3.1 s, My Activities 3.2 s and Event Requests 2.8 to 3.1 s, with about 3,000 to 4,500 SQL statements per request, over the 2 s of NFR-02. The in-memory performance tests could not show it.
- **How it was caught:** Emir measured the pages with the real services on PostgreSQL (issue #52).
- **Fix:** #58 loads the participants of a whole list with one more query (`selectinload`) in the four list methods. According to #52, on the #58 branch (not merged yet), whole pages (Find Events, My Activities, Event Requests) take 0.22 to 0.35 s on the server with 14 to 25 statements.
- **Lesson:** Repository methods that return lists are measured on PostgreSQL with real amounts of data, not only in memory.

Cases 11 to 14 are about the events backend (#33, #38, #52, and #58): wrong error types, time handling, a missing method, and a performance defect that only appeared on PostgreSQL.

## What we changed in the way we work
- **Peer review on every pull request** (branch protection on `main`, one approving review). All fourteen cases were caught by a person, in a review, while reading the assistant's output or by asking it a question, not by the assistant on its own.
- **The assistant merges nothing without an approving review** and the explicit OK of the team member who works with it (case 8). It shows a review or a comment to that person before posting it.
- **Claims are checked against the code:** every number, test name and "every …" in a report or document is compared with the code or a test, not only re-read (cases 6 and 10).
- **`CLAUDE.md`** (#35) writes down the project rules the assistant got wrong or could easily get wrong: UTC in the services, where settings are read, transactions, roles, CSRF, secrets.
- **Reviewers test like users:** real Turkish input, the real database, the live deployment, not only the assistant's tests.
- **Primary sources first:** dates come from the instructor's announcements copied into the plan, platform limits from the provider's documentation, and behaviour from the code itself.
