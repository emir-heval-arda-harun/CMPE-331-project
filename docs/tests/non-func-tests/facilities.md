# Non-functional tests – facilities (UC-07, UC-08)

**Author:** Harun Gündaş · **Date of the results:** 20.11.2026 · **Code:** `main` with PR #22 · Part of the Software Testing Report, see the [facilities section](../../testing/facility_test_section.md).

The non-functional requirements are in the [Requirements Specification](../../requirements_specification.md) (NFR-01 to NFR-07). This file lists the ones that apply to the Facility Management page and the facility backend.

| NFR | What was checked | How | Result |
|---|---|---|---|
| NFR-01 Usability (360 px to desktop) | The page at 375 px and at desktop width: facility list, schedule, add facility, add block, remove block with the confirmation window | Manual, in a browser with the demo data (`scripts/run_demo.py`) as facility staff; `document.documentElement.scrollWidth` measured | ✅ No horizontal scrolling at 375 px (`scrollWidth` = 375). One defect found and fixed: on a phone the schedule was below the form, so the facility links now jump to it (`#schedule`) |
| NFR-04 Security (role-based access) | Only facility staff add facilities, add blocks and remove blocks; the check is done twice, on the page and in the service | Automated: Unit `test_student_cannot_add_facility_or_block`, `test_student_cannot_remove_a_block`; Web `test_only_staff_can_open_the_page`, `test_only_staff_can_remove_a_block`; Req `test_nfr04_student_cannot_manage_facilities`, `test_nfr04_student_cannot_block_a_facility` | ✅ Students and admins get 403 on the page and `PermissionDeniedError` in the service |
| NFR-04 Security (CSRF) | Every form of the page (add facility, add block, remove block) sends a CSRF token | Flask-WTF `CSRFProtect` is on for the whole app (automated: `test_forms_are_protected_by_csrf_tokens` in `tests/web/test_web_accounts.py`, a post without a token gets 400); every form in `facilities.html` includes `csrf()` (checked in the page source). The facility web tests turn CSRF off to post directly | ✅ |
| NFR-05 Privacy | The schedule shows the event title and "waiting for approval", but no organizer name or e-mail address | Automated: Web `test_schedule_shows_no_organizer_names_or_e_mails` | ✅ |
| NFR-06 Maintainability | All facility tests run with one command; 99 % code coverage | `python -m pytest` (CI on every pull request); coverage in [coverage file](../coverage/facilities.md#code-coverage) | ✅ 76 facility tests, 0 failures |
| Reliability (Design report 5.3, 7.1, risk R-01) | Two requests cannot book the same slot at the same time; a refused change leaves nothing behind | Automated on PostgreSQL 16: DB `test_get_for_update_locks_the_facility_row` (a second connection gets `LockNotAvailable` while the first holds `SELECT … FOR UPDATE`), `test_service_with_sql_repository_rolls_back_a_refused_block`; the EXCLUDE constraints `ex_event_facility_no_overlap` and `ex_facility_block_no_overlap` are the last guard | ✅ |
| NFR-07 Portability | The page in current browsers | Manual: Chromium-based browser (Chrome, Edge). Bootstrap 5 and plain JavaScript; the remove confirmation falls back to the browser's own `confirm` without Bootstrap | ✅ Chromium; Firefox and Safari are checked in the team's browser test (task 4.2) |

**Not applicable here:** NFR-02 (search speed) is about event search (UC-05). NFR-03 (password hashing) is in the accounts section (PR #23).
