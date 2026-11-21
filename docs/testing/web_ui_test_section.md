# Software Testing Report – Web UI section (task 3.5)

**Author:** Emir Gül · **Status:** section for the team's Software Testing Report (task 4.1: pull request to Yeşim by 25.11.2026, PDF on Learn by 29.11.2026) · **Date of the results:** 21.11.2026

It covers the web UI (layer 1 of the [Software Design Report](../software_design_report.md), `src/campusevent/web/`) for UC-01 to UC-06, UC-09 to UC-11 and UC-12 (admin review of event requests, change request CR-01), with the design of the [UI/UX document](../ui_ux_design.md). The results below are for `main` of 21.11.2026 (`c98923c`), after PR #31 (*Send a new code*), PR #22 (remove a block) and PR #32 (category label) were merged. The facility page (UC-07, UC-08) is in the [facilities section](facility_test_section.md); the services behind the pages are in the sections of their owners.

The parts the instructor asked for on 17.11 are in their own files:
- **Traceability matrix with code and requirements coverage:** [`docs/tests/coverage/web-ui.md`](../tests/coverage/web-ui.md)
- **Non-functional tests and their results:** [`docs/tests/non-func-tests/web-ui.md`](../tests/non-func-tests/web-ui.md)
- **TDD evidence (red → green, repeatable):** [`docs/tests/tdd/web-ui.md`](../tests/tdd/web-ui.md)

## 1. Scope and approach
| Level | What is tested | Test doubles | File | Run |
|---|---|---|---|---|
| Web UI | Every page through the Flask test client: status code, redirect, the text and the forms of the page, error messages, access rules, Istanbul time, privacy | In-memory stand-ins for the services, [`tests/web/fakes.py`](../../tests/web/fakes.py), that follow the interface of the class diagram (Design Report 4.2) and the rules of the use cases | `tests/web/test_web_accounts.py`, `test_web_events.py`, `test_web_admin.py`, `test_web_extras.py`, `test_web_resend_code.py`, `test_web_error_paths.py` | `python -m pytest tests/web` |
| Web UI with real services | The pages against the real `AuthService` (task 3.2): sign up, verify, a new code | none for accounts | `test_works_with_the_real_auth_service` in `test_web_resend_code.py` | as above |
| Browser | The pages in Firefox and WebKit (the engine of Safari) at 1280 px and 360 px: scripts, dialogs, layout, console errors | none (the demo, `scripts/run_demo.py`) | Playwright scripts, results in the [non-functional tests](../tests/non-func-tests/web-ui.md) | by hand |

**Why test doubles:** the pages were built before the services (tasks 3.2 to 3.4). The doubles let every page and every error message be tested from the start, and the web tests stay fast and need no database. **Limit:** a passing web test shows that the page works with a service that behaves like the use case text, not that the real service does. Since 20.11 the real `AuthService` and `ProfileService` are on `main`, and the requirement tests of UC-01 to UC-03 pass with them; for the events this check waits for task 3.4 (section 6).

**Tools:** pytest 9.2, Flask 3.1 test client, coverage.py 7.17 (branch coverage), Playwright 1.65 (Firefox, WebKit), ruff. CI (GitHub Actions) runs ruff and pytest on every push and pull request, so the web tests run on every change.

## 2. Results
| Suite | Tests | Passed | Failed |
|---|---|---|---|
| Web UI tests of this section (6 files) | 118 | 118 | 0 |
| All web tests (with the facility page, 26, and the composition root, 3) | 147 | 147 | 0 |
| Requirement tests of UC-01, UC-02, UC-03 (`tests/test_uc01_*` to `test_uc03_*`) | 10 | 10 | 0 |
| Requirement tests of UC-04 to UC-06, UC-09 to UC-12 and their NFR tests | 33 | 0 | 33, all `NotImplementedError` of `EventService` (task 3.4) |

**Code coverage** of the web UI of this section: **99 %** of statements and branches (498 statements, 90 branches); five of the six files are at 100 % or 99 %. Details and the two uncovered lines: [coverage file](../tests/coverage/web-ui.md#code-coverage).

**Browser checks** (Firefox and WebKit, 1280 px and 360 px): all passed, no console errors, no horizontal scrolling. Details: [non-functional tests](../tests/non-func-tests/web-ui.md).

## 3. Traceability
The [traceability matrix](../tests/coverage/web-ui.md#traceability-matrix) maps every step and alternative flow of the use cases of this section, the business rules (BR-01, BR-03, BR-04, BR-15), the team time rule and the NFRs to their tests and to the code. 31 of 31 rows have passing tests, and each of the 118 tests appears in the matrix.

## 4. Test design
- **One test per rule, named as a sentence** (`test_wrong_credentials_do_not_say_which_part_is_wrong`), so a failing test says which rule is broken.
- **Main flow and alternative flows:** every use case has a test of its main flow; every alternative flow written in the use cases of this section has its own test, except the automatic expiry of UC-12, which is done by the backend (the page only shows *Rejected*). Three alternative flows (UC-04 1a, UC-10 1a, UC-11 1b) got their test while this matrix was written.
- **Boundary values:** capacity 1 and a capacity far above the facility (UC-04, BR-04); a reason of 501 characters, one over the limit (UC-12); an event at 01:00 Istanbul time, which is 22:00 of the day before in UTC; a busy slot that lasts until closing time; the one-minute wait of *Send a new code*: a second request after 20 seconds is refused, one after 80 seconds is allowed.
- **Equivalence classes:** for *Send a new code*, unknown, verified and unverified addresses must give the same page (NFR-05); for the *Leave* redirect, five kinds of addresses (another site, `//`, another page, a backslash, empty) must all return to Find Events.
- **Negative tests for access** (NFR-04): the important pages of each role are opened with the other roles: Find Events by facility staff, Event Requests by a student and by facility staff, cancelling by a participant who is not the organizer, waiting and rejected requests by other students.
- **Coverage as a check of the tests:** the coverage run found eight error paths without a test (section 5, defect 10).

## 5. Defects found while testing
| # | Found by | Defect | Fix |
|---|---|---|---|
| 1 | Web test of UC-12 | When an admin decided a request that was no longer waiting, the error was attached to a card that was no longer in the list, so it was not shown | Errors for requests that left the list are shown above the list (`general_errors`, PR #14) |
| 2 | Web test of BR-15 | Joining a waiting or rejected request of someone else gave 400 and showed that it exists | 404, like opening it (`_visible_event`, PR #14) |
| 3 | Review of the team time rule (the server on Render runs in UTC) | Between 00:00 and 03:00 Istanbul time the server date is still the day before, so today's events were labelled "Tomorrow" | "Today" is taken from the Istanbul clock (`campus_today`, PR #14), with a test that runs the server clock in UTC |
| 4 | Check of a downloaded calendar file | The times in the `.ics` file had no time zone, so a calendar set to another time zone showed the wrong hour | First the Istanbul time zone was added; after the team time rule the times are written in UTC with `Z` (PR #14) |
| 5 | Browser, network log | Typing a date into Create Event loaded the schedule for the years 0002, 0020, 0202 | The schedule loads only for a complete date, with a short pause (PR #14) |
| 6 | Browser, console | Every page asked for `/favicon.ico` and got 404 | Favicon and a redirect (PR #14) |
| 7 | Contrast measurement after the Glass Night design | Muted text 4.1:1 and field labels 2.7:1 on the brightest part of the background (WCAG AA needs 4.5:1) | Darker glass and lighter text: every text colour at least 4.5:1 (PR #20) |
| 8 | Browser check of My Activities | The rejection reason was dark red on dark glass | Own class with a readable colour (PR #20) |
| 9 | Review of the facility page after the design change | The facility names were dark text on the dark glass | Glass colours for the facility list (PR #28) |
| 10 | Coverage measurement (97 % at first) | Eight error and edge paths had no test: start page for visitors, unknown address, unexpected error, a refused session token, approving a request that is no longer waiting, a busy slot until closing time, a deleted participant, a calendar file without description | Tests added (`test_web_error_paths.py`); all passed at once, so the code was right; coverage 99 % |
| 11 | Check of the report: every form field searched for a label | The category text box on Create Event had no label: without JavaScript the label *Category* named the hidden list, and the box for *Other…* had only a placeholder (WCAG 1.3.1, 3.3.2) | *Category* names the visible field; the *Other…* box has its own label *Your own category*; a test checks every field of every form (`test_every_form_field_has_a_label`) |

Defects found by this section in the code of others: the Turkish capital *İ* in interests (review of #24, Heval) and the *Remove* button contrast (review of #22, Harun); they are listed in those sections.

## 6. Limits and what integration testing (task 4.2) must check
| # | Item | Owner of the next step |
|---|---|---|
| 1 | Run the event pages (Find Events, Create Event, Event Details, join, leave, cancel, My Activities, Event Requests) against the real `EventService` as soon as task 3.4 is merged, and fix any difference | Emir with E. Arda |
| 2 | `EventService.get_event(event_id)` is used by the pages but is not in the class diagram ([details](../../src/campusevent/web/README.md)) | E. Arda (task 3.4) |
| 3 | Check the deployed site on Render (HTTPS, NFR-03; real e-mails for the codes) after the database wiring (#25, #27) | Onur, Emir |
| 4 | Safari itself on a Mac or an iPhone (NFR-07); WebKit on Windows is the closest test available | Web UI owner, on a team member's device |
| 5 | Features the service interface cannot do yet: time range filter (UC-05), an *Upcoming* list on My Activities | Team decision |
| 6 | SonarQube analysis of the whole repository (`docs/tests/quality`) | Team |
