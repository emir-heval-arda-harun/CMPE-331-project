# CampusEvent – Use Cases

Requirements are written in **use case format**. Each use case has its own file and a matching test file under [`tests/`](../../tests).

![Use case diagram](diagrams/use_case_diagram.png)

| ID | Use Case | Primary Actor | Priority | Test |
|---|---|---|---|---|
| [UC-01](UC-01_register_and_verify.md) | Register with university e-mail and verify account | Student | High | [test](../../tests/test_uc01_register_and_verify.py) |
| [UC-02](UC-02_login.md) | Log in | All registered users | High | [test](../../tests/test_uc02_login.py) |
| [UC-03](UC-03_manage_profile.md) | Manage profile (sports, skill levels, availability) | Student | High | [test](../../tests/test_uc03_manage_profile.py) |
| [UC-04](UC-04_create_match.md) | Create match | Student | High | [test](../../tests/test_uc04_create_match.py) |
| [UC-05](UC-05_browse_and_filter_matches.md) | Browse and filter matches | Student | High | [test](../../tests/test_uc05_browse_and_filter_matches.py) |
| [UC-06](UC-06_join_match.md) | Join match | Student | High | [test](../../tests/test_uc06_join_match.py) |
| [UC-07](UC-07_ai_team_balancing.md) | AI skill-based team balancing | Student (organizer), Gemini Pro | Medium | [test](../../tests/test_uc07_ai_team_balancing.py) |
| [UC-08](UC-08_create_tournament.md) | Create tournament | Club Representative | Medium | [test](../../tests/test_uc08_create_tournament.py) |
| [UC-09](UC-09_generate_bracket.md) | Generate tournament bracket | Club Representative | Medium | [test](../../tests/test_uc09_generate_bracket.py) |
| [UC-10](UC-10_record_score.md) | Record score and advance teams | Club Representative | Medium | [test](../../tests/test_uc10_record_score.py) |
| [UC-11](UC-11_facility_availability.md) | View facility schedule and check conflicts | Student | High | [test](../../tests/test_uc11_facility_availability.py) |
| [UC-12](UC-12_manage_facility_schedule.md) | Manage facility schedule | Facility Staff | Medium | [test](../../tests/test_uc12_manage_facility_schedule.py) |
| [UC-13](UC-13_activity_history.md) | Track activity history | Student | Low | [test](../../tests/test_uc13_activity_history.py) |
| [UC-14](UC-14_leave_match.md) | Leave match | Student | Medium | [test](../../tests/test_uc14_leave_match.py) |
| [UC-15](UC-15_cancel_match.md) | Cancel match | Student (organizer) | Medium | [test](../../tests/test_uc15_cancel_match.py) |

The diagram is generated from [`diagrams/make_use_case_diagram.py`](diagrams/make_use_case_diagram.py).

## Non-functional requirement tests
The non-functional requirements (NFR-01 ... NFR-09) are defined in the [Requirements Specification](../requirements_specification.md#5-non-functional-requirements). The ones that can be checked by code are tested in [`tests/test_nfr.py`](../../tests/test_nfr.py). Like the use case tests, they fail until the feature is implemented.

| NFR | Category | Check | Test / how it is verified |
|---|---|---|---|
| NFR-01 | Usability | Responsive from 360 px to desktop width | Manual: open each page in the browser developer tools at 360 px and desktop width |
| NFR-02 | Performance | Match search < 2 s for 1,000 open matches | `test_nfr02_search_is_fast_with_1000_open_matches` |
| NFR-03 | Performance | Team balancing < 10 s including the AI call | `test_nfr03_team_balancing_finishes_within_10_seconds` |
| NFR-04 | Security | Passwords stored only as salted hashes | `test_nfr04_password_is_never_stored_in_plain_text`, `test_nfr04_same_password_gives_different_stored_values` |
| NFR-05 | Security | Role-based access | `test_nfr05_facility_staff_cannot_create_tournaments`, `test_nfr05_club_representative_cannot_manage_facilities`, `test_nfr05_student_cannot_block_a_facility`, `test_nfr05_student_cannot_record_tournament_scores` |
| NFR-06 | Privacy | No names or e-mail addresses sent to the AI service | `test_nfr06_ai_service_receives_no_names_or_emails` |
| NFR-07 | Reliability | Balancing works when the AI is unavailable | `test_nfr07_balancing_works_when_ai_times_out`, `test_nfr07_balancing_works_without_any_ai_client` |
| NFR-08 | Maintainability | One command runs all tests | Verified by running `python -m pytest` |
| NFR-09 | Portability | Works in Chrome, Firefox, Safari and Edge | Manual: open the main pages in each browser |

HTTPS (NFR-04) is a deployment setting and is checked during the CI/CD & Deploy task.
