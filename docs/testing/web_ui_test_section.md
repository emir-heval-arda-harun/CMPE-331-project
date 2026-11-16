# Software Testing Report – Web UI section (task 3.5)

**Status:** draft section for the team's Software Testing Report (task 4.1, due 22.11.2026). It covers only the web UI of UC-01 to UC-06 and UC-09 to UC-11. The backend, the facility pages (UC-07, UC-08) and the integration tests are written by the other team members and must be added to the full report.

## 1. Scope and approach
The web UI (`src/campusevent/web/`, layer 1 of the [Software Design Report](../software_design_report.md)) is tested through the Flask test client: each test sends the HTTP requests of a user and checks the status code, the redirect and the text of the page.

| Item | Decision |
|---|---|
| Test level | UI tests of layer 1 (routes, templates, error handling) |
| Test doubles | In-memory stand-ins for the services, [`tests/web/fakes.py`](../../tests/web/fakes.py). They follow the planned service interface of the design report and the rules written in the use cases. |
| Why doubles | On the date of writing the real services still raise `NotImplementedError`. The UI tests are independent of the backend. |
| Tool | pytest 9, Flask test client |
| Run | `python -m pytest tests/web` |

**Limit of this approach:** a passing UI test shows that the pages work with a service that behaves like the use case text. It does not show that the real service behaves that way. This must be checked in the integration tests (task 4.2), see section 5.

## 2. Result (at the time of writing)
| Suite | Tests | Passed | Failed |
|---|---|---|---|
| `tests/web` (this section) | 40 | 40 | 0 |
| Requirement tests of the team (`tests/test_*.py`) | 39 | 0 | 39 (expected: the services are skeletons) |

## 3. Traceability: use case to UI test
All tests are in [`tests/web/test_web_accounts.py`](../../tests/web/test_web_accounts.py) or [`tests/web/test_web_events.py`](../../tests/web/test_web_events.py).

| Use case | Page | Tests |
|---|---|---|
| UC-01 Register and verify | `/signup`, `/verify` | `test_signup_shows_code_box_after_registration`, `test_signup_rejects_non_university_email`, `test_signup_rejects_duplicate_email`, `test_verify_with_correct_code_goes_to_login`, `test_verify_with_wrong_code_shows_error_and_keeps_form` |
| UC-02 Log in | `/login`, `/logout` | `test_student_logs_in_and_lands_on_find_events`, `test_facility_staff_lands_on_facility_management`, `test_wrong_credentials_do_not_say_which_part_is_wrong`, `test_unverified_account_cannot_log_in_and_is_offered_the_code_page`, `test_pages_redirect_to_login_when_logged_out`, `test_logout_ends_the_session` |
| UC-03 Manage profile | `/profile` | `test_profile_saves_interests_and_availability`, `test_profile_requires_one_interest`, `test_profile_rejects_slot_that_ends_before_it_starts` |
| UC-04 Create event | `/events/new` | `test_create_event_redirects_to_its_details_and_adds_the_organizer`, `test_create_form_lists_facilities_with_capacity`, `test_create_event_on_busy_slot_shows_message_and_the_busy_times`, `test_create_event_rejects_capacity_below_two_and_above_the_facility`, `test_create_event_rejects_bad_times_and_numbers`, `test_schedule_card_shows_free_facility` |
| UC-05 Browse and filter | `/events` | `test_find_events_lists_open_events_soonest_first`, `test_find_events_filters_by_keyword_category_and_date`, `test_find_events_empty_result_offers_create_event`, `test_find_events_rejects_invalid_date`, `test_full_event_is_not_in_the_open_list` |
| UC-06 Join event | `/events/<id>/join` | `test_join_then_leave`, `test_join_twice_shows_clear_message`, `test_join_full_event_shows_message`, `test_join_buttons_in_list_follow_the_rules` |
| UC-09 Activity history | `/activities` | `test_activities_empty_state`, `test_activities_list_completed_events_newest_first` |
| UC-10 Leave event | `/events/<id>/leave` | `test_join_then_leave`, `test_organizer_sees_cancel_but_not_leave_and_can_cancel` |
| UC-11 Cancel event | `/events/<id>/cancel` | `test_organizer_sees_cancel_but_not_leave_and_can_cancel`, `test_only_the_organizer_can_cancel` |

Every use case of this section has at least one test of the main flow. UC-01 to UC-06, UC-10 and UC-11 also have tests of error or alternative flows. UC-09 has a test for the empty list but no error flow.

## 4. Non-functional requirements checked on the UI
| NFR | What was checked | How | Result |
|---|---|---|---|
| NFR-01 Usability | Layout at phone width | Manual: Event Details page at 375 px in the built-in browser: no horizontal scrolling, one column | Passed for this page only |
| NFR-01 Usability | Other pages at 360 px | – | **Not checked yet** |
| NFR-03 Security | CSRF token on forms | `test_forms_are_protected_by_csrf_tokens` | Passed |
| NFR-03 Security | Session cookie flags (`Secure`, `HttpOnly`, `SameSite=Lax`) | `test_session_cookie_is_secure_by_default` | Passed |
| NFR-03 Security | HTTPS on the deployed site | – | **Not checked** (deployment is task 4.4) |
| NFR-04 Access control | Staff cannot open student pages; only the organizer can cancel | `test_staff_cannot_open_student_pages`, `test_only_the_organizer_can_cancel` | Passed |
| NFR-05 Privacy | No e-mail address on event list and details | `test_event_details_never_show_email_addresses` | Passed |
| Security (XSS) | Text typed by users is escaped | `test_text_in_events_is_escaped` | Passed |
| NFR-07 Portability | Chrome, Firefox, Safari, Edge | – | **Not checked.** Only one Chromium-based browser was used so far. |

## 5. Open items and risks
| # | Item | Owner of the next step |
|---|---|---|
| 1 | Run the UI against the real services as soon as they exist and fix differences (integration test, task 4.2) | All |
| 2 | The UI needs three service methods that are not in the design report: `EventService.get_event`, `FacilityService.list_facilities`, `AuthService.get_user` raising `NotFoundError` ([details](../../src/campusevent/web/README.md)) | Backend owners (Heval, E. Arda, Harun) |
| 3 | Missing features because the service interface cannot do them: resend verification code (UC-01), time range filter (UC-05), "Upcoming" tab on My Activities (F-09), suggestion of free slots (UC-04/UC-07) | Team decision |
| 4 | Check all pages at 360 px and in Firefox, Safari and Edge (NFR-01, NFR-07) | Web UI owner |
| 5 | Add a GitHub Actions run for `tests/web` (CI, task 3.7) | Onur |
