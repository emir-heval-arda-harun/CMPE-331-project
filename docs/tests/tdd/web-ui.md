# TDD evidence – Web UI (UC-01 to UC-06, UC-09 to UC-12)

Part of the Software Testing Report, web UI section ([`docs/testing/web_ui_test_section.md`](../../testing/web_ui_test_section.md)). Task 3.5, Emir. Same method as the [facilities page](facilities.md).

This page shows, with commits and test runs that anyone can repeat, that the web UI was written **against tests that describe the use cases and fail without the code**, and then made them pass (red → green).

## 1. The pages were tested before the services existed
The web tests run against in-memory stand-ins ([`tests/web/fakes.py`](../../../tests/web/fakes.py)) that follow the interfaces of the class diagram (Design Report 4.2) and the rules of the use cases. So the tests fixed what the pages expect from the services **before** the services were written:

| Date | Commit | What happened |
|---|---|---|
| 16 Nov 2026 | `48ee85a` (PR #7) | Pages for accounts, profiles and events with their web tests. `AuthService`, `ProfileService` and `EventService` were still skeletons (`NotImplementedError`). The methods the pages need but the design report does not have (`get_event`, `list_facilities`, `get_user` with `NotFoundError`) were written down in [`src/campusevent/web/README.md`](../../../src/campusevent/web/README.md). |
| 18 Nov 2026 | `9386a76` (PR #14) | Admin Event Requests page and request statuses (CR-01, UC-12), again before any UC-12 backend. |
| 20 Nov 2026 | PR #23, #24 merged | The real `AuthService` and `ProfileService` arrive, and the requirement tests of UC-01 to UC-03 pass with them. Since PR #31 (`178e0c9`), `test_works_with_the_real_auth_service` also runs sign up, verify and a new code through the pages with the real service. |
| 21 Nov 2026 | review of PR #33 | First run of the event pages against the real `EventService`: the pages expect `get_event` and the errors `EventFullError`, `AlreadyJoinedError`, `PermissionDeniedError`; the run showed which of these the backend does not meet yet. The expectations came first, the backend is being changed to meet them. |
| 23 Nov 2026 | #33 (with #38) merged | The real `EventService` meets what the pages expected: the requirement tests of UC-04 to UC-06 and UC-09 to UC-12 pass, the 7 performance tests with the real services run, and the event pages pass 36 of 36 checks on `main`. |

## 2. Red → green, repeated for each step of the code
The web tests of a feature were committed in the **same commit** as the page code, so git does not show which line was typed first. To show the test-first order anyway, the web tests of each commit (`tests/web/` of that commit, including the stand-ins) were run on the code of the commit **before** it (red) and on the commit itself (green):

| Step | Commit | On the code before (red) | On the commit (green) | The tests that fail without the change |
|---|---|---|---|---|
| Ready-made categories with *Other…* (UC-04, UC-05) | `6347ecb` | 2 failed, 42 passed | 44 passed | the category list on Create Event and the suggestions in the Find Events filter |
| An event status the page does not know | `3cf9257` | 1 failed, 67 passed | 68 passed | the event page still opens instead of failing |
| Admin Event Requests (CR-01, UC-12) | `9386a76` | 18 failed, 69 passed | 87 passed | admin lands on Event Requests, only admins open it, a student cannot approve or reject, approve, reject with a reason, empty and too long reason, a request no longer pending, the reason is escaped, a new event is not listed, other students cannot see a pending or rejected request, withdraw, My Activities in every status; also the schedule box waiting for a complete date (defect 5), the favicon (defect 6) and the warning for a missing secret key |
| Leave from the card on Find Events (UC-10) | `756f36c` | 1 failed, 93 passed | 94 passed | the *Leave* button on a joined card returns to the same list |
| *Add to calendar* with a time zone (defect 4) | `e2eae80` | 1 failed, 93 passed | 94 passed | the `.ics` file marks its times |
| "Today" from the Istanbul clock (defect 3) | `0cb56bb` | 1 failed, 94 passed | 95 passed | today's event is "Today" even when the server runs in UTC (on the old code the test stops because `campus_today` does not exist yet) |
| Team time rule: UTC in the services, Istanbul time on the pages | `3c434da` | 42 failed, 55 passed | 97 passed | the test helper `slot()` now gives times in UTC, as the real services keep them. 39 of the 42 tests stop at once because the conversion helper `slot_to_utc` does not exist yet in the old code (like "cannot be imported" on the facilities page). The other 3 fail on the rule itself: Create Event sends 18:00 to the service instead of 15:00 UTC, My Profile sends availability in Istanbul time (17 instead of 14), and the helper `to_utc` is missing |
| *Send a new code* (UC-01 5a, UC-02 3a, PR #31) | `178e0c9` | 7 failed, 117 passed | 124 passed | all 7 tests of `test_web_resend_code.py`: the button, the new code replaces the old one, the same answer for every address (NFR-05), an empty address, the one-minute wait, no address in a link, the real `AuthService` |
| Label for the category box (defect 11, PR #32) | `c66359c` | 2 failed, 120 passed | 122 passed | every form field has a label; the *Category* label follows the visible field |
| No *Join*, *Leave* or *Cancel* after the start (defect 12, PR #42) | `3d1628e` | 3 failed, 136 passed | 139 passed | all 3 new tests: the buttons are gone after the start, they stay until the start minute, the real time is used when the service has no clock |
| Event Requests in pages of 20, safe page numbers (defect 13, PR #43) | `4a51fc7` | 6 failed, 138 passed | 144 passed | 20 requests per page, a decision returns to the same page, a wrong page number (such as `²`) gives no error page (2 pages), no link behind a greyed-out *Previous* or *Next* (2 pages). The other 2 new tests are guards for behaviour that was already right |
| Bootstrap and Inter from `static/`, no `autofocus` (defect 15, PR #44) | `656c402` | 4 failed, 136 passed | 140 passed | no field takes the focus by itself, nothing is loaded from other sites, the own copies are served, the Bootstrap file is the published one (SHA-256) |
| Long words without spaces (defect 14, PR #45) | `00649ed` | 1 failed, 136 passed | 137 passed | long words break instead of widening the page |
| Security headers on every answer (section 6, item 9, PR #46) | `881fe77` | 2 failed, 148 passed | 150 passed | the headers on pages, a redirect, the 404 page, a static file and log out; the headers on the 500 page |
| Findings of the penetration test in the web UI (P4, P5, P8, PR #49) | `452dbbb` | 3 failed, 148 passed | 151 passed | `HEAD` never runs the form code; no lines can be added to the calendar file; a form over 1 MB gets 413 |
| Full Content-Security-Policy with a nonce (NFR-03, PR #57) | `1e1c7fd` | 2 failed, 154 passed | 156 passed | the policy allows only our own site and blocks an injected script; every `<script>` on every page has the nonce of its answer |

In every step all tests pass on the commit itself, so the change broke none of the older tests (no regression). Apart from the rows `3c434da` and `0cb56bb`, and one of the seven tests of `178e0c9` (it sets the clock through `auth_routes.time`, which the old code does not have), the red runs fail on the behaviour (a wrong status code, a missing text or form field), not because a name is missing.

Run 21 Nov 2026 (the six rows before the last 23 Nov 2026, the last row 25 Nov 2026), Python 3.14, pytest 9.2.

## 3. Tests that caught a defect first
Section 5 of the report lists the defects. These follow the red → green order:
- **Defects 1 and 2** (PR #14): found by the web tests of UC-12 and BR-15 while the page was written (report, section 5): an error for a request that had left the list was not shown, and joining a waiting or rejected request of someone else gave 400 instead of 404. The fix is in the same commit (`9386a76`), so git does not show these runs; the replay of that commit is in section 2.
- **Defects 3 and 4:** found by thinking about the time rule and by checking a downloaded calendar file. The test was written for the defect and fails on the code before the fix (rows `0cb56bb` and `e2eae80` above).
- **Defect 11:** `test_every_form_field_has_a_label` was written while checking the report. It failed on the code of `main` and found exactly one field without a label. The first fix still left the category list without a name; the test failed again, and passed after the list got an `aria-label`.
- **Defects 12 to 15** (23 Nov): found by the run against the real `EventService`, a re-check, the check of long texts and SonarQube. For each one a test was written that fails on the code before the fix (the rows of `3d1628e`, `4a51fc7`, `656c402` and `00649ed` in section 2); for defect 13 the wrong page number `²` itself is one of the test values.
- **Penetration test** (23 Nov, [report](../security/pentest-web.md)): for the three findings in the web UI (P4, P5, P8) a test was written first and failed on the code before the fix (the row of `452dbbb`); for `HEAD` the old code really signed up, logged in, saved a profile and created an event without a CSRF token.

## 4. Honest limits
- The tests sit in the same commit as their code (section 2). The replay shows that the tests describe the new behaviour and fail without it, but not the minute-by-minute order of typing. Code and tests were written with an AI assistant (Claude Code), and a team member ran and checked each commit.
- The 11 tests of [`test_web_error_paths.py`](../../../tests/web/test_web_error_paths.py) (`4e3d0c0`, 21 Nov) were written **after** the code: eight because the coverage run showed untested paths, three because the traceability matrix showed alternative flows without a test. All passed at once: replayed like section 2, they pass on the code before `4e3d0c0` too (131 of 131), because no code changed. They are test-after, not TDD, and are listed here so the evidence above is not overstated.
- The 15 tests of [`test_web_performance.py`](../../../tests/web/test_web_performance.py) (23 Nov) are measurements of NFR-02, also written after the code. No code changed for them.
- The visual commits (Glass Night design, backgrounds: `1622a15`, `d3271d4`, `3fbc33e`, `1b74298`, `39d6cd6`) were checked mainly in the browser and by measuring contrast; their few web tests check that the right background or band is on the page, not how it looks.

## 5. How to repeat section 2
In a separate clone (so the working copy is not touched):
```bash
X=c66359c                                   # any commit of the table
git checkout --detach $X^
rm -rf tests/web && git checkout $X -- tests/web
PYTHONPATH=src python -m pytest tests/web   # red
git checkout -f --detach $X
PYTHONPATH=src python -m pytest tests/web   # green
```
