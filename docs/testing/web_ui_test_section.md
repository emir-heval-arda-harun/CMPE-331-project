# Software Testing Report – Web UI section (task 3.5)

**Status:** draft section for the team's Software Testing Report (task 4.1: pull request due 25.11.2026, PDF due 29.11.2026). It covers only the web UI of UC-01 to UC-06, UC-09 to UC-11 and UC-12 (admin review of event requests, CR-01). The backend, the facility pages (UC-07, UC-08) and the integration tests are written by the other team members and must be added to the full report.

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
| `tests/web` (this section) | 87 | 87 | 0 |
| Requirement tests of the team (`tests/test_*.py`) | 51 | 0 | 51 (expected: the services are skeletons) |

## 3. Traceability: use case to UI test
The tests are in [`tests/web/test_web_accounts.py`](../../tests/web/test_web_accounts.py), [`tests/web/test_web_events.py`](../../tests/web/test_web_events.py) and, for UC-12, [`tests/web/test_web_admin.py`](../../tests/web/test_web_admin.py).

| Use case | Page | Tests |
|---|---|---|
| UC-01 Register and verify | `/signup`, `/verify` | `test_signup_shows_code_box_after_registration`, `test_signup_rejects_non_university_email`, `test_signup_rejects_duplicate_email`, `test_verify_with_correct_code_goes_to_login`, `test_verify_with_wrong_code_shows_error_and_keeps_form` |
| UC-02 Log in | `/login`, `/logout` | `test_student_logs_in_and_lands_on_find_events`, `test_facility_staff_lands_on_facility_management`, `test_wrong_credentials_do_not_say_which_part_is_wrong`, `test_unverified_account_cannot_log_in_and_is_offered_the_code_page`, `test_pages_redirect_to_login_when_logged_out`, `test_logout_ends_the_session`, `test_login_and_signup_pages_have_a_show_password_button_and_no_main_navigation` |
| UC-03 Manage profile | `/profile` | `test_profile_saves_interests_and_availability`, `test_profile_requires_one_interest`, `test_profile_rejects_slot_that_ends_before_it_starts` |
| UC-04 Create event | `/events/new` | `test_create_event_redirects_to_its_details_and_adds_the_organizer`, `test_create_form_lists_facilities_with_capacity`, `test_create_form_offers_ready_made_categories_and_an_other_option`, `test_a_category_that_is_not_in_the_list_is_accepted`, `test_create_event_on_busy_slot_shows_message_and_the_busy_times`, `test_create_event_rejects_capacity_below_two_and_above_the_facility`, `test_create_event_rejects_bad_times_and_numbers`, `test_schedule_card_shows_free_facility` |
| UC-05 Browse and filter | `/events` | `test_find_events_lists_open_events_soonest_first`, `test_find_events_suggests_categories_in_the_filter`, `test_find_events_filters_by_keyword_category_and_date`, `test_find_events_empty_result_offers_create_event`, `test_find_events_rejects_invalid_date`, `test_full_event_is_not_in_the_open_list` |
| UC-06 Join event | `/events/<id>/join` | `test_join_then_leave`, `test_join_twice_shows_clear_message`, `test_join_full_event_shows_message`, `test_join_buttons_in_list_follow_the_rules` |
| UC-09 Activity history | `/activities` | `test_activities_empty_state`, `test_activities_list_completed_events_newest_first` |
| UC-10 Leave event | `/events/<id>/leave` | `test_join_then_leave`, `test_organizer_sees_cancel_but_not_leave_and_can_cancel` |
| UC-11 Cancel event | `/events/<id>/cancel` | `test_organizer_sees_cancel_but_not_leave_and_can_cancel`, `test_only_the_organizer_can_cancel`, `test_organizer_withdraws_a_pending_request` |
| UC-12 Review event requests | `/admin/requests`, `/approve`, `/reject`; organizer view on `/events/<id>` and `/activities` | `test_admin_lands_on_event_requests_after_login`, `test_only_admins_can_open_the_requests_page`, `test_a_student_cannot_approve_or_reject`, `test_requests_page_lists_pending_requests_soonest_first_without_e_mails`, `test_admin_approves_a_request_and_it_is_listed`, `test_admin_rejects_a_request_with_a_reason`, `test_rejection_without_a_reason_keeps_the_request_and_says_why`, `test_a_too_long_reason_is_refused_and_kept_in_the_box`, `test_a_request_that_is_no_longer_pending_cannot_be_reviewed_again`, `test_a_new_event_is_sent_for_review_and_not_listed`, `test_other_students_cannot_open_a_pending_or_rejected_request`, `test_organizer_sees_the_rejection_reason_and_can_submit_a_corrected_request`, `test_my_activities_lists_my_requests_in_every_status` |

The helper features (free time suggestions for UC-04 4a, the facility schedule box, "Add to calendar", pagination, category shortcuts, interest tags, the password guide) are tested in [`tests/web/test_web_extras.py`](../../tests/web/test_web_extras.py). Their scripts (schedule reload, overlap warning, cancel confirmation window, interest tags) were also tried by hand in the built-in browser on 17.11.2026.

Every use case of this section has at least one test of the main flow. UC-01 to UC-06, UC-10, UC-11 and UC-12 also have tests of error or alternative flows. The automatic rejection of requests that are not reviewed before their start time (UC-12, BR-18) is done by the backend; the UI only shows the result as *Rejected*. UC-09 has a test for the empty list but no error flow.

## 4. Non-functional requirements checked on the UI
| NFR | What was checked | How | Result |
|---|---|---|---|
| NFR-01 Usability | Layout at phone width | Manual, 360 px wide in the built-in browser (Chromium), with demo data: Log in, Sign up (first step), Find Events, Create Event, My Profile, My Activities, Event Details. The page width was measured with `scrollWidth` and no element reached beyond the screen edge; the Create Event form was also looked at. | Passed for these 7 pages and the error page (404); measured again after the visual redesign of the pages on 17.11.2026 |
| NFR-01 Usability | Sign-up code step, error pages, long titles and many participants at 360 px | – | **Not checked yet** |
| NFR-03 Security | CSRF token on forms | `test_forms_are_protected_by_csrf_tokens` | Passed |
| NFR-03 Security | Session cookie flags (`Secure`, `HttpOnly`, `SameSite=Lax`) | `test_session_cookie_is_secure_by_default` | Passed |
| NFR-03 Security | HTTPS on the deployed site | – | **Not checked** (deployment is task 4.4) |
| NFR-04 Access control | Staff cannot open student pages; only the organizer can cancel; only admins review requests; other students cannot see pending or rejected requests | `test_staff_cannot_open_student_pages`, `test_only_the_organizer_can_cancel`, `test_only_admins_can_open_the_requests_page`, `test_a_student_cannot_approve_or_reject`, `test_other_students_cannot_open_a_pending_or_rejected_request` | Passed |
| NFR-05 Privacy | No e-mail address on event list and details | `test_event_details_never_show_email_addresses` | Passed |
| Security (XSS) | Text typed by users is escaped | `test_text_in_events_is_escaped` | Passed |
| NFR-07 Portability | Firefox (Gecko) and WebKit (Safari's engine), desktop 1280 px and phone 360 px | Automated walk-through with Playwright on 17.11.2026 against the demo (`scripts/run_demo.py`): sign up password guide, log in, category shortcut, schedule reload, overlap warning, free slot button, create event, cancel confirmation window, Add to calendar, interest tags; console errors and horizontal scrolling recorded | Passed in both browsers and both sizes; no console errors, no horizontal scrolling |
| NFR-07 Portability | CR-01 pages (Event Requests, pending and rejected requests, withdraw) in Firefox and WebKit, desktop 1280 px and phone 360 px | Automated walk-through with Playwright on 18.11.2026 against the demo: student sends two requests, admin lands on Event Requests, empty reason is blocked, reject with a reason, approve, organizer sees the reason on My Activities and on the event page, the corrected-request form is prefilled, withdraw through the confirmation window, favicon; console errors and horizontal scrolling recorded | Passed: 31 checks in Firefox, 30 in WebKit (one step needs data that the first size already used); no console errors, no horizontal scrolling |
| NFR-07 Portability | Chromium (Chrome, Edge) | Built-in browser of the development tool (Chromium) for all pages; Edge only for the log in page | Passed |
| NFR-07 Portability | Safari itself on macOS and iOS | – | **Not checked.** WebKit on Windows is the closest available test; a check on a Mac or an iPhone is still open. Note: WebKit on Windows shows the empty date filter without a date hint |

## 5. Open items and risks
| # | Item | Owner of the next step |
|---|---|---|
| 1 | Run the UI against the real services as soon as they exist and fix differences (integration test, task 4.2) | All |
| 2 | The UI needs three service methods that are not in the design report: `EventService.get_event`, `FacilityService.list_facilities`, `AuthService.get_user` raising `NotFoundError` ([details](../../src/campusevent/web/README.md)) | Backend owners (Heval, E. Arda, Harun) |
| 3 | Missing features because the service interface cannot do them: time range filter (UC-05), "Upcoming" tab on My Activities (F-09). Free slot suggestions (UC-04 4a) are now done in the UI, with assumed opening hours 08:00–22:00 | Team decision |
| 4 | Check the pages on a real Safari (Mac or iPhone) (NFR-07) and the remaining 360 px cases of NFR-01 | Web UI owner |
| 5 | Add a GitHub Actions run for `tests/web` (CI, task 3.7) | Onur |
