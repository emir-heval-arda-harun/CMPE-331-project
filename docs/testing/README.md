# Software Testing Report – CampusEvent (task 4.1)

**Team:** Heval Hüseyin Demir (project manager), Emre Arda Kum, Emir Gül, Harun Gündaş, Onur Alioğlu · **Reviewer:** Yeşim · **Date:** 26.11.2026

This is the opening section of the report. It explains what we tested and how, gives the most important tests and results, and shows how to read the other sections. The numbers below come from the CI run of `main` on 26.11.2026 (commit `22825b5`). After the five report pull requests (#18, #29, #37, #39, #63) are merged, every number in the report is taken again from one final CI run.

## 1. What we tested
CampusEvent is the campus event and facility web application of the CMPE 331 team project (Flask, PostgreSQL 16, live on Render: https://campusevent-86ax.onrender.com). The report covers:
- the twelve use cases **UC-01 to UC-12**, in [`docs/requirements`](../requirements);
- the eighteen business rules **BR-01 to BR-18**, in section 6 of the [Requirement Analysis Report](../requirement_analysis_report.md);
- the seven non-functional requirements **NFR-01 to NFR-07**, in the [Requirements Specification](../requirements_specification.md).

## 2. How to read the report
Each team member tested the part they built. Parts 2 to 5 have the same outline: scope and approach, results, traceability, test design, defects found, limits. Each part has three files besides its main section, as the instructor asked on 17.11:
- **coverage:** a traceability matrix from requirement to rule to tests to code, with requirements and code coverage;
- **non-func-tests:** the non-functional tests and their results;
- **tdd:** the TDD evidence, with commits and CI runs that anyone can open.

| Part | Contents | Use cases | Author | Main section | Coverage, NFR, TDD |
|---|---|---|---|---|---|
| 1 | This opening section | all | Heval Hüseyin Demir | this file | – |
| 2 | Accounts, profiles and database | UC-01, UC-02, UC-03 | Heval Hüseyin Demir | [accounts_profiles_test_section.md](accounts_profiles_test_section.md) | [coverage](../tests/coverage/accounts-profiles.md), [NFR](../tests/non-func-tests/accounts-profiles.md), [TDD](../tests/tdd/accounts-profiles.md) |
| 3 | Facilities | UC-07, UC-08 | Harun Gündaş | [facility_test_section.md](facility_test_section.md) | [coverage](../tests/coverage/facilities.md), [NFR](../tests/non-func-tests/facilities.md), [TDD](../tests/tdd/facilities.md) |
| 4 | Events | UC-04 to UC-06, UC-09 to UC-12 | Emre Arda Kum | [events_test_section.md](events_test_section.md) | [coverage](../tests/coverage/events.md), [NFR](../tests/non-func-tests/events.md), [TDD](../tests/tdd/events.md) |
| 5 | Web UI | UC-01 to UC-06, UC-09 to UC-12 | Emir Gül | [web_ui_test_section.md](web_ui_test_section.md) | [coverage](../tests/coverage/web-ui.md), [NFR](../tests/non-func-tests/web-ui.md), [TDD](../tests/tdd/web-ui.md) |
| 6 | Security tests | all | Emir Gül, Onur Alioğlu | [web pentest](../tests/security/pentest-web.md), [deployment pentest](../tests/security/deployment.md) | [security scans](../tests/non-func-tests/security_scans.md) |
| 7 | Code coverage of the whole project | all | Onur Alioğlu | [coverage/README.md](../tests/coverage/README.md) | – |
| 8 | Code quality: SonarQube | all | Heval Hüseyin Demir | [quality/README.md](../tests/quality/README.md) | dated results in the same folder |

The results in parts 2 to 8 are those of the date at the top of each part. Section 4 of this file has the numbers of the whole suite.

## 3. Test levels and tools

| Level | What is tested | Where | Tests on `main` |
|---|---|---|---|
| Requirement (acceptance) | One file per use case (`tests/test_uc01_…` to `test_uc12_…`) and `tests/test_nfr.py`, through `create_app()` with the real services. Written with the requirements, before the code | local and CI | 51 (44 UC + 7 NFR) |
| Unit | `AuthService`, `ProfileService`, `FacilityService`, `EventService`, the wiring of `create_app` and the mail sender, with in-memory repositories and a test clock | local and CI | 158 |
| Database | Schema and constraints, the Alembic migration, the SQL repositories, row locks, and the services on a real PostgreSQL 16 database | CI (PostgreSQL service) and local | 73 |
| Web UI | Every page through the Flask test client: status codes, forms, error messages, access rules, Istanbul time, privacy, performance with 1,000 events | local and CI | 164 |
| Manual and browser | Phone width (360–375 px); Chromium, Firefox and WebKit; the live site; penetration tests | by hand, Playwright | see parts 2 to 6 |

**Tools:** Python 3.12, pytest, the Flask test client, coverage.py with branch coverage (pytest-cov), ruff, bandit, pip-audit, SonarQube Cloud, Playwright, PostgreSQL 16.

**CI:** GitHub Actions runs ruff, the whole test suite on PostgreSQL 16 with code coverage, and the security scans on every push and pull request; SonarQube Cloud analyses every pull request. Every change to `main` comes through a pull request with one approving review from a teammate, and a green `main` is deployed to Render.

**Run all tests with one command** (NFR-06):
```bash
pip install -r requirements-dev.txt
python -m pytest --cov          # the database tests need TEST_DATABASE_URL (PostgreSQL 16)
```

## 4. Results
CI run of `main` on 26.11.2026 (`22825b5`), whole suite on PostgreSQL 16:

- **446 tests passed, 0 failed, 0 skipped.** `ruff check .` is clean. bandit finds no medium or high issue in `src/`, and pip-audit finds no known vulnerability.
- **Code coverage 97 %** of 2,039 statements and 340 branches. The services are at 90–100 %, the SQL repositories at 95–100 %, the web layer at 94–100 %. The missed lines are explained in the coverage files and in [part 7](../tests/coverage/README.md).
- **SonarQube:** no finding in the Python code or the templates; the open findings and the plan for them are in [part 8](../tests/quality/README.md).
- **Defects:** the tests and reviews found defects in every part. Each part lists them with the fix, for example the slow pages on PostgreSQL (part 4 and 5, fixed in #58) and the limits from the penetration tests (part 6, fixed in #55 and #57).

## 5. The most important tests
These tests guard the rules that would hurt users most if they broke:

| What could go wrong | Test (file) | Requirement | Result |
|---|---|---|---|
| Two events or blocks booked in the same facility at the same time | `test_active_events_cannot_overlap_in_one_facility`, `test_blocks_of_one_facility_cannot_overlap` (`db/test_schema.py`); `test_get_for_update_locks_the_facility_row` (`db/test_facility_repository.py`) | BR-06, BR-10, BR-16, UC-07 | pass |
| A pending request loses its slot, or an old request is approved after its start | `test_pending_request_holds_the_slot_and_cancel_frees_it`, `test_request_not_reviewed_before_its_start_expires_and_cannot_be_approved` (`test_event_service.py`) | BR-16, BR-18, UC-12 | pass |
| Passwords stored in a readable form | `test_password_and_code_are_stored_only_as_argon2_hashes` (`test_auth_accounts.py`); `test_nfr03_password_is_never_stored_in_plain_text` (`test_nfr.py`) | BR-02, NFR-03 | pass |
| Guessing a verification code or a password | `test_p2_a_code_stops_working_after_five_wrong_tries`, `test_p1_log_in_pauses_after_five_wrong_passwords` (`test_auth_accounts.py`) | UC-01, UC-02, NFR-03 | pass |
| A user does what their role does not allow | `test_nfr04_only_an_admin_can_approve_or_reject_event_requests`, `test_nfr04_only_the_organizer_can_cancel_an_event`, `test_nfr04_student_cannot_manage_facilities` (`test_nfr.py`) | NFR-04, BR-09, BR-13, BR-17 | pass |
| A page shows another user's e-mail address | `test_event_details_never_show_email_addresses` (`web/test_web_events.py`), `test_schedule_shows_no_organizer_names_or_e_mails` (`web/test_web_facilities.py`) | NFR-05 | pass |
| Pages become slow with many events | `test_nfr02_search_is_fast_with_1000_open_events` (`test_nfr.py`); the web performance tests of part 5; PostgreSQL timing in parts 4 and 5 | NFR-02 | pass; on PostgreSQL 0.32–0.48 s since #58 |
| Times shown on the wrong day | `test_an_event_just_after_midnight_belongs_to_its_istanbul_day`, `test_today_is_the_istanbul_date_even_when_the_server_runs_in_utc` (`web/test_web_extras.py`) | team time rule (#16) | pass |

## 6. Requirements coverage
**Every use case, every business rule and every non-functional requirement has at least one passing test.** The full matrices (requirement → rule → tests → code → result) are in the coverage files of parts 2 to 5.

| Kind | Requirements | With passing tests | Coverage |
|---|---|---|---|
| Use cases | 12 (UC-01 to UC-12) | 12 | 100 % |
| Business rules | 18 (BR-01 to BR-18) | 18 | 100 % |
| Non-functional requirements | 7 (NFR-01 to NFR-07) | 7 (NFR-01, NFR-05 and NFR-07 also by hand in the browser) | 100 % |
| **Total** | **37** | **37** | **100 %** |

### 6.1 Use cases

| Use case | Requirement tests | Also tested by | Part |
|---|---|---|---|
| UC-01 Register and verify e-mail | 5 | accounts, database, web | 2, 5 |
| UC-02 Log in | 3 | accounts, database, web | 2, 5 |
| UC-03 Manage profile | 2 | profiles, database, web | 2, 5 |
| UC-04 Create event | 5 | events, facilities, database, web | 3, 4, 5 |
| UC-05 Browse and filter events | 4 | events, web | 4, 5 |
| UC-06 Join event | 3 | events, web | 4, 5 |
| UC-07 View facility schedule and check conflicts | 2 | facilities, database, web | 3 |
| UC-08 Manage facility schedule | 2 | facilities, database, web | 3 |
| UC-09 Activity history | 2 | events, web | 4, 5 |
| UC-10 Leave event | 3 | events, web | 4, 5 |
| UC-11 Cancel event | 4 | events, web | 4, 5 |
| UC-12 Review event requests | 9 | events, web | 4, 5 |

### 6.2 Business rules
One test per rule as an example; the matrices list all of them.

| Rule | Example test (file) | Part |
|---|---|---|
| BR-01 Only university e-mail domains | `test_only_the_exact_university_domains_are_accepted` (`test_auth_accounts.py`) | 2, 5 |
| BR-02 Passwords never in plain text | `test_nfr03_password_is_never_stored_in_plain_text` (`test_nfr.py`) | 2 |
| BR-03 Only verified users log in | `test_unverified_user_cannot_log_in` (`test_uc02_login.py`) | 2, 5 |
| BR-04 Capacity from 2 to the facility's capacity | `test_capacity_below_two_is_rejected`, `test_capacity_above_the_facility_capacity_is_rejected` (`test_event_service.py`) | 3, 4 |
| BR-05 The organizer is the first participant | `test_new_event_is_pending_and_organizer_is_first_participant` (`test_event_service.py`) | 4 |
| BR-06 No two active events or blocks at the same time | `test_active_events_cannot_overlap_in_one_facility` (`db/test_schema.py`) | 2, 3 |
| BR-07 Join at most once, never above capacity | `test_student_cannot_join_twice` (`test_uc06_join_event.py`) | 4 |
| BR-08 Full at capacity, Open again when someone leaves | `test_event_becomes_full_and_rejects_new_participants` (`test_uc06_join_event.py`) | 4 |
| BR-09 Only facility staff manage facilities | `test_nfr04_student_cannot_manage_facilities` (`test_nfr.py`) | 3 |
| BR-10 Blocks of one facility do not overlap | `test_overlapping_blocks_are_rejected` (`test_facility_service.py`) | 3 |
| BR-11 History: only completed events, newest first | `test_completed_events_appear_in_history` (`test_uc09_activity_history.py`) | 4 |
| BR-12 An organizer cannot leave their own event | `test_organizer_cannot_leave_and_non_participant_cannot_leave` (`test_event_service.py`) | 4 |
| BR-13 Only the organizer cancels | `test_only_the_organizer_can_cancel` (`test_uc11_cancel_event.py`) | 4, 5 |
| BR-14 Categories trimmed, case does not matter | `test_category_is_stored_trimmed_and_lower_case` (`test_event_service.py`), `test_interests_are_trimmed_lower_cased_and_kept_once` (`test_profiles.py`) | 2, 4 |
| BR-15 New events are Pending and not listed | `test_new_event_is_pending_and_organizer_is_first_participant`, `test_search_lists_only_open_events_and_filters_combine` (`test_event_service.py`) | 4, 5 |
| BR-16 A pending request holds its slot | `test_pending_request_holds_the_slot_and_cancel_frees_it` (`test_event_service.py`) | 3, 4 |
| BR-17 Only an admin reviews; a rejection needs a reason | `test_nfr04_only_an_admin_can_approve_or_reject_event_requests` (`test_nfr.py`) | 4 |
| BR-18 Requests not reviewed before the start are rejected | `test_request_not_reviewed_before_its_start_expires_and_cannot_be_approved` (`test_event_service.py`) | 4 |

### 6.3 Non-functional requirements

| Requirement | Automated tests | Also checked | Part |
|---|---|---|---|
| NFR-01 Usability, 360 px to desktop | web tests for forms and messages | by hand at 360–375 px in three browsers | 3, 5 |
| NFR-02 Search under 2 s with 1,000 events | `test_nfr02_search_is_fast_with_1000_open_events` and the web performance tests | PostgreSQL timing before and after #58 | 4, 5 |
| NFR-03 Salted password hashes, HTTPS | 2 NFR tests and the accounts tests | HTTPS and secure cookie on the live site | 2, 6 |
| NFR-04 Role-based access | 4 NFR tests and the role tests of every part | penetration tests | 2–6 |
| NFR-05 No e-mail addresses on pages | web and facility tests | by hand on the live site | 3, 5 |
| NFR-06 Maintainability: one command, tests per use case | the whole suite in CI | – | 3, 7 |
| NFR-07 Current browsers | – | Chromium, Firefox and WebKit by hand and with Playwright | 3, 5 |
