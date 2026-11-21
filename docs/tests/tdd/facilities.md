# TDD evidence – Facilities (UC-07, UC-08)

Part of the Software Testing Report, facilities section ([`docs/testing/facility_test_section.md`](../../testing/facility_test_section.md)). Tasks 3.3 and 3.6, Harun.

This page shows, with commits and test runs that anyone can repeat, that the facility code was written **against tests that already existed and failed**, and then made them pass (red → green).

## 1. Requirement tests were written before the code

| Date | Commit | Who | What happened |
|---|---|---|---|
| 08 Oct 2026 | `e21a13a` | Harun | Requirement tests for "view facility schedule and prevent booking conflicts" and "manage facility schedule" (then numbered UC-11 and UC-12). `FacilityService` was only a skeleton: every method raised `NotImplementedError`, so all these tests failed (red). |
| 17 Oct 2026 | `333c49a` (PR #5) | Heval | Requirement Analysis Report: use cases renumbered and the scope widened from sports matches to all campus events. The tests became [`tests/test_uc07_facility_availability.py`](../../../tests/test_uc07_facility_availability.py) and [`tests/test_uc08_manage_facility_schedule.py`](../../../tests/test_uc08_manage_facility_schedule.py) with the same rules (the schedule shows existing bookings, an overlapping booking is rejected, only staff manage facilities). Still red. |
| 18 Nov 2026 | `446ebf8` | Harun | First real `FacilityService` and `FacilityRepository` (task 3.3), written against these rules. |
| 20 Nov 2026 | PR #23 merged | Heval | `AuthService.register` works, so the requirement tests reach the facility code for the first time: 3 of the 6 facility requirement tests pass (section 2 of the report). The other 3 stop earlier, at `EventService.create_event` (task 3.4), and are run again in integration testing (task 4.2). |

So the tests that describe UC-07 and UC-08 are about **six weeks older** than the code that satisfies them.

## 2. Red → green, repeated for each step of the code

The unit and web tests of a feature were committed in the **same commit** as the code. Git therefore does not show which line was typed first inside one commit. To show the test-first order anyway, each commit's tests were run on the code of the commit **before** it (red) and on the commit itself (green):

| Step | Tests taken from | Run on code of | Result |
|---|---|---|---|
| Facility service (task 3.3) | `446ebf8` `tests/test_facility_service.py` | `5328ba5` (just before, skeleton) | **red**: cannot even be imported, `FacilityRepository` does not exist yet |
| | | `446ebf8` | **green**: 34 passed |
| Remove a block (issue #19, PR #22) | `b8527b7` `tests/test_facility_service.py` and `tests/web/test_web_facilities.py` | `b8527b7^` (before the feature) | **red**: 12 failed, 52 passed. The 12 failing tests are exactly the new rules: a block has an id, staff remove a block and the time is free again, a student cannot remove a block, an unknown block or one of another facility gives an error, a removed block cannot be removed twice, the Remove button asks for confirmation, the schedule shows event titles and pending requests |
| | | `b8527b7` | **green**: 64 passed |

The 52 tests that pass on the old code are the older rules: adding the new tests did not change them (no regression).

Run 21 Nov 2026, Python 3.12, pytest 9.2.

## 3. Tests that caught a defect first
Section 5 of the report lists the defects. Two of them follow the red → green order, and a third is guarded by a test:
- **Defect 3:** the web test `test_block_over_an_event_booking_is_refused` was written first and failed on the local run before commit `032d86b`, because the page showed the student message "Please choose another time or facility". The route was then changed to show the service text, and the test passed.
- **Defect 6 (issue #19):** Emir's review asked for a way to remove a block. The new rules became the 12 tests of section 2, which fail on the old code.
- **Defect 1:** found in code review, not by a test. The database test `test_service_with_sql_repository_rolls_back_a_refused_block` now guards the fix: after a refused block, only the first block is left in the table.

## 4. Honest limits
- The unit and web tests sit in the same commit as their code (section 2). The replay shows that the tests describe the new behaviour and fail without it, but not the minute-by-minute order of typing.
- Two web tests of 20 Nov (`185c5df`: no organizer data on the schedule, NFR-05; the evening before is not on the next day) were written **after** the code, when branch coverage showed an untested branch. They are test-after, not TDD, and are listed here so the evidence above is not overstated.

## 5. How to repeat section 2
```bash
git worktree add ../before 446ebf8^
git show 446ebf8:tests/test_facility_service.py > ../before/tests/test_facility_service.py
cd ../before && PYTHONPATH=src python -m pytest tests/test_facility_service.py   # red
git checkout --detach 446ebf8 -- . && PYTHONPATH=src python -m pytest tests/test_facility_service.py   # green
```
For the remove-block step, use `b8527b7^` and `b8527b7`, and copy both test files from `b8527b7`.
