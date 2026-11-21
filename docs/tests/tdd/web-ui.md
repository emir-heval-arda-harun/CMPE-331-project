# TDD evidence – Web UI (UC-01 to UC-06, UC-09 to UC-12)

Part of the Software Testing Report, web UI section ([`docs/testing/web_ui_test_section.md`](../../testing/web_ui_test_section.md)). Tasks 3.5 and 2.3, Emir. Same method as the [facilities page](facilities.md).

This page shows, with commits and test runs that anyone can repeat, that the web UI was written **against tests that describe the use cases and fail without the code**, and then made them pass (red → green).

## 1. The pages were tested before the services existed
The web tests run against in-memory stand-ins ([`tests/web/fakes.py`](../../../tests/web/fakes.py)) that follow the interfaces of the class diagram (Design Report 4.2) and the rules of the use cases. So the tests fixed what the pages expect from the services **before** the services were written:

| Date | Commit | What happened |
|---|---|---|
| 16 Nov 2026 | `48ee85a` (PR #7) | Pages for accounts, profiles and events with their web tests. `AuthService`, `ProfileService` and `EventService` were still skeletons (`NotImplementedError`). The methods the pages need but the design report does not have (`get_event`, `list_facilities`, `get_user` with `NotFoundError`) were written down in [`src/campusevent/web/README.md`](../../../src/campusevent/web/README.md). |
| 18 Nov 2026 | `9386a76` (PR #14) | Admin Event Requests page and request statuses (CR-01, UC-12), again before any UC-12 backend. |
| 20 Nov 2026 | PR #23, #24 merged | The real `AuthService` and `ProfileService` arrive. The requirement tests of UC-01 to UC-03 pass, and `test_works_with_the_real_auth_service` runs sign up, verify and a new code through the pages with the real service. |
| 21 Nov 2026 | review of PR #33 | First run of the event pages against the real `EventService`: the pages expect `get_event` and the errors `EventFullError`, `AlreadyJoinedError`, `PermissionDeniedError`; the run showed which of these the backend does not meet yet. The expectations came first, the backend is being changed to meet them. |

## 2. Red → green, repeated for each step of the code
The web tests of a feature were committed in the **same commit** as the page code, so git does not show which line was typed first. To show the test-first order anyway, the web tests of each commit (`tests/web/` of that commit, including the stand-ins) were run on the code of the commit **before** it (red) and on the commit itself (green):

| Step | Commit | On the code before (red) | On the commit (green) | The tests that fail without the change |
|---|---|---|---|---|
| Ready-made categories with *Other…* (UC-04, UC-05) | `6347ecb` | 2 failed, 42 passed | 44 passed | the category list on Create Event and the suggestions in the Find Events filter |
| An event status the page does not know | `3cf9257` | 1 failed, 67 passed | 68 passed | the event page still opens instead of failing |
| Admin Event Requests (CR-01, UC-12) | `9386a76` | 18 failed, 69 passed | 87 passed | admin lands on Event Requests, only admins open it, approve, reject with a reason, empty and too long reason, a request no longer pending, the reason is escaped, a new event is not listed, other students cannot see a pending or rejected request, withdraw, My Activities in every status; also the schedule box waiting for a complete date (defect 5), the favicon (defect 6) and the warning for a missing secret key |
| Leave from the card on Find Events (UC-10) | `756f36c` | 1 failed, 93 passed | 94 passed | the *Leave* button on a joined card returns to the same list |
| *Add to calendar* with a time zone (defect 4) | `e2eae80` | 1 failed, 93 passed | 94 passed | the `.ics` file marks its times |
| "Today" from the Istanbul clock (defect 3) | `0cb56bb` | 1 failed, 94 passed | 95 passed | today's event is "Today" even when the server runs in UTC |
| Team time rule: UTC in the services, Istanbul time on the pages | `3c434da` | 42 failed, 55 passed | 97 passed | the stand-ins now keep UTC like the real services, so every page that shows or reads a time fails until the pages convert: create, find, join, leave, cancel, schedule box, calendar file, history, requests, the conversion helpers and an event just after midnight |
| *Send a new code* (UC-01 5a, UC-02 3a, PR #31) | `178e0c9` | 7 failed, 117 passed | 124 passed | all 7 tests of `test_web_resend_code.py`: the button, the new code replaces the old one, the same answer for every address (NFR-05), an empty address, the one-minute wait, no address in a link, the real `AuthService` |
| Label for the category box (defect 11, PR #32) | `c66359c` | 2 failed, 120 passed | 122 passed | every form field has a label; the *Category* label follows the visible field |

In every step the tests that pass on the old code are the older rules: adding the new tests did not change them (no regression).

Run 21 Nov 2026, Python 3.14, pytest 9.2.

## 3. Tests that caught a defect first
Section 5 of the report lists the defects. These follow the red → green order:
- **Defects 1 and 2** (PR #14): the web tests of UC-12 and BR-15 failed first. An error for a request that had left the list was not shown, and a waiting request of someone else gave 400 instead of 404. Both were fixed until the tests passed.
- **Defects 3 and 4:** found by thinking about the time rule and by checking a downloaded calendar file. The test was written for the defect and fails on the code before the fix (rows `0cb56bb` and `e2eae80` above).
- **Defect 11:** `test_every_form_field_has_a_label` was written while checking the report. It failed on the code of `main` and found exactly one field without a label. The first fix still left the category list without a name; the test failed again, and passed after the list got an `aria-label`.

## 4. Honest limits
- The tests sit in the same commit as their code (section 2). The replay shows that the tests describe the new behaviour and fail without it, but not the minute-by-minute order of typing. Code and tests were written with an AI assistant (Claude Code), and a team member ran and checked each commit.
- The 11 tests of [`test_web_error_paths.py`](../../../tests/web/test_web_error_paths.py) (`4e3d0c0`, 21 Nov) were written **after** the code: eight because the coverage run showed untested paths, three because the traceability matrix showed alternative flows without a test. All passed at once. They are test-after, not TDD, and are listed here so the evidence above is not overstated.
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
