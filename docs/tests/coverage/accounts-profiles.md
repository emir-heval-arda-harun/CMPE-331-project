# Coverage – accounts, profiles and database (UC-01, UC-02, UC-03)

**Author:** Heval Hüseyin Demir · **Date of the results:** 20.11.2026 · **Code:** `main` with PRs #23, #24 and #25 · Part of the Software Testing Report, see the [accounts, profiles and database section](../../testing/accounts_profiles_test_section.md).

## Traceability matrix
Requirement → rule → tests → code, with the result on 20.11.2026. Acc = `tests/test_auth_accounts.py`, Roles = `tests/test_auth_roles.py`, Prof = `tests/test_profiles.py`, Wire = `tests/test_wiring.py` and `tests/web/test_web_wiring.py`, Schema = `tests/db/test_schema.py`, UoW = `tests/db/test_unit_of_work.py`, DB = `tests/db/test_user_repository.py`, `tests/db/test_profile_repository.py` and `tests/db/test_app_with_database.py`, Req = `tests/test_uc01_*`, `tests/test_uc02_*`, `tests/test_uc03_*`, `tests/test_nfr.py`.

| Requirement | Rule | Tests | Code | Result |
|---|---|---|---|---|
| UC-01 steps 1–4 | Register: unverified student account, 6-digit code e-mailed after the commit | Acc `test_register_stores_a_normalized_unverified_student`, `test_code_has_six_digits_and_expires_after_15_minutes`; Req `test_registration_with_university_email_sends_verification_code`; Schema `test_new_user_is_an_unverified_student` | `AuthService.register`, `_new_code`, `UserRepository.add` / `save_code` | ✅ |
| UC-01 alt. 2a, BR-01 | Only the exact university domains | Acc `test_only_the_exact_university_domains_are_accepted`, `test_malformed_email_is_rejected`; Req `test_non_university_email_is_rejected` | `register` | ✅ |
| UC-01 step 1 (input) | Full name and password lengths; nothing stored or sent on a refusal | Acc `test_password_length_is_checked`, `test_full_name_is_required_and_limited`, `test_rejected_input_stores_nothing_and_sends_nothing` | `register` | ✅ |
| UC-01 alt. 3a | One account per e-mail, without regard to case | Acc `test_duplicate_in_other_case_is_rejected_and_rolled_back`; Req `test_duplicate_email_is_rejected`; Schema `test_email_is_unique_without_regard_to_case`; DB `test_same_email_in_other_case_is_a_duplicate`, `test_find_by_email_ignores_case_and_spaces` | `register`, `SqlUserRepository.add`, index `ux_user_email_lower` | ✅ |
| UC-01 steps 5–6 | The correct code verifies the account | Acc `test_verify_accepts_the_email_in_any_case_and_marks_the_account`, `test_verifying_twice_says_the_account_is_already_verified`; Req `test_correct_code_verifies_account`; DB `test_mark_code_used_and_mark_verified`, `test_register_verify_and_login_with_postgresql` | `AuthService.verify_email`, `mark_code_used`, `mark_verified` | ✅ |
| UC-01 alt. 5a | Wrong or expired code is refused; a new code can be requested and replaces the old one | Acc `test_code_does_not_work_after_15_minutes`, `test_code_works_just_before_it_expires`, `test_unknown_email_gets_the_same_error_as_a_wrong_code`, `test_new_code_replaces_the_old_one`, `test_new_code_is_not_sent_to_unknown_or_verified_addresses`; Req `test_wrong_verification_code_is_rejected`; DB `test_latest_code_is_the_last_one_saved_in_naive_utc` | `verify_email`, `resend_code`, `VerificationCode.is_valid`, `get_latest_code` | ✅ |
| UC-02 steps 1–4 | A verified user logs in and gets a session | Acc `test_login_accepts_the_email_in_any_case`; Req `test_verified_user_logs_in_and_gets_session`; DB `test_register_verify_and_login_with_postgresql` | `AuthService.login`, `get_user_by_token` | ✅ |
| UC-02 alt. 2a | "Invalid e-mail or password" without saying which part is wrong | Acc `test_unknown_email_and_wrong_password_give_the_same_message`, `test_empty_password_is_a_failed_login`; Req `test_wrong_password_is_rejected` | `login` | ✅ |
| UC-02 alt. 3a, BR-03 | Only verified accounts log in; the account is named only after a correct password | Acc `test_unverified_user_with_wrong_password_is_not_told_that_the_account_exists`; Req `test_unverified_user_cannot_log_in` | `login` (`EmailNotVerifiedError`) | ✅ |
| UC-02 step 4 (session) | The session token is signed, cannot be changed, expires after 24 h and survives a restart with the same key | Acc `test_changed_or_made_up_tokens_are_rejected`, `test_token_of_another_secret_key_is_rejected`, `test_token_expires_after_the_session_lifetime`, `test_token_survives_a_restart_with_the_same_secret_key`; Wire `test_from_env_signs_tokens_with_secret_key_so_they_survive_a_restart` | `get_user_by_token`, `_sign` (HMAC-SHA256) | ✅ |
| BR-02, NFR-03 | Passwords and codes are stored only as salted argon2id hashes | Acc `test_password_and_code_are_stored_only_as_argon2_hashes`; Req `test_nfr03_password_is_never_stored_in_plain_text`, `test_nfr03_same_password_gives_different_stored_values`; DB `test_password_hash_is_stored_but_not_returned`, `test_password_hash_is_read_by_id` | `Argon2PasswordHasher`, `register`, `SqlUserRepository` | ✅ |
| NFR-04 (roles) | `get_user` / `require_role` used by every service | Roles `test_get_user_returns_the_user_and_rejects_an_unknown_id`, `test_require_role_returns_the_user_with_that_role`, `test_require_role_refuses_every_other_role`, `test_require_role_names_the_needed_role`, `test_require_role_rejects_an_unknown_user`, `test_facility_service_uses_the_real_role_check`; DB `test_require_role_with_sql_repository` | `AuthService.get_user`, `require_role` | ✅ |
| UC-03 steps 1–5 | Students save interests and availability; the new profile replaces the old one | Prof `test_new_student_has_an_empty_profile`, `test_saving_replaces_the_old_profile`, `test_profile_of_one_student_does_not_change_another`, `test_returned_profile_is_a_copy`; Req `test_student_saves_interests_and_availability`; DB `test_save_and_get_in_naive_utc`, `test_save_replaces_the_rows_and_can_keep_an_interest`, `test_profile_service_with_postgresql`, `test_sign_up_log_in_and_save_profile_across_requests` | `ProfileService.update_profile` / `get_profile`, `ProfileRepository.save` / `get` | ✅ |
| UC-03 alt. 5a | At least one interest | Prof `test_at_least_one_interest_is_needed`; Req `test_profile_requires_at_least_one_interest` | `_clean_interests` | ✅ |
| UC-03 alt. 5b | A slot must end after it starts; slots sorted, repeats dropped | Prof `test_slot_must_end_after_it_starts`, `test_slots_are_returned_by_start_time_and_repeats_are_dropped` | `_check_slots` | ✅ |
| BR-14 | Interests trimmed, lower-cased (also Turkish İ), kept once, at most 60 characters | Prof `test_interests_are_trimmed_lower_cased_and_kept_once`, `test_turkish_capital_i_becomes_a_plain_i`, `test_interest_can_be_60_characters_long_but_not_more`; Schema `test_interests_are_stored_trimmed_and_in_lower_case` | `_clean_interests`, check `ck_profile_interest_interest_normalized` | ✅ |
| UC-03, NFR-04 | Only students change a profile; unknown user → not found | Prof `test_only_students_can_change_a_profile`, `test_unknown_user_has_no_profile` | `update_profile`, `get_profile` | ✅ |
| Design report 7.1 | One `UnitOfWork` per change; a refused change leaves nothing behind | Prof `test_save_runs_in_one_transaction`, `test_invalid_change_keeps_the_saved_profile`; Acc `test_duplicate_in_other_case_is_rejected_and_rolled_back`; UoW `test_commit_stores_the_rows`, `test_rollback_stores_nothing`, `test_begin_after_a_read_goes_on_in_the_same_transaction`, `test_after_a_constraint_error_rollback_makes_the_session_usable_again`, `test_in_memory_unit_of_work_records_the_calls` | `SqlUnitOfWork`, `InMemoryUnitOfWork` | ✅ |
| Design report 3.5, 7.1 | One session per request, closed after it | UoW `test_each_request_thread_gets_its_own_session`; Wire `test_with_database_the_sql_classes_share_one_session_and_one_unit_of_work`, `test_end_request_removes_the_session_of_the_request`, `test_database_session_is_closed_after_every_request` | `create_app`, `CampusEventApp.end_request` | ✅ |
| Design report §6 (schema) | Eight tables, indexes, migration matches `tables.py`, can be undone | Schema `test_migration_creates_the_eight_tables_and_btree_gist`, `test_tables_py_matches_the_migrations`, `test_migration_can_be_undone_and_done_again`, `test_indexes_of_the_design_report_exist` | `migrations/versions/20261118_0001_initial_schema.py`, `tables.py` | ✅ |
| Design report §6 (constraints), CR-01 | Roles, event status and reason (BR-15, BR-17), capacity and times (BR-04), no overlapping active events (BR-06, BR-16) or blocks (BR-10), join once (BR-07) | Schema `test_role_must_be_student_facility_staff_or_admin`, `test_new_event_is_pending_without_review`, `test_rejected_event_needs_a_reason`, `test_pending_event_cannot_be_rejected_without_a_reason`, `test_wrong_event_values_are_refused`, `test_event_must_end_after_it_starts`, `test_event_needs_an_existing_facility`, `test_active_events_cannot_overlap_in_one_facility`, `test_inactive_events_free_the_slot`, `test_back_to_back_events_and_other_facilities_are_allowed`, `test_cancelled_event_cannot_come_back_into_a_taken_slot`, `test_user_joins_an_event_only_once`, `test_facility_name_is_unique_and_capacity_at_least_two`, `test_blocks_of_one_facility_cannot_overlap`, `test_deleting_a_user_deletes_their_profile_rows` | Constraints in the migration | ✅ |
| Team time rule (#16) | Naive UTC in services and the database | Schema `test_times_are_stored_in_utc`; DB `test_latest_code_is_the_last_one_saved_in_naive_utc`, `test_save_and_get_in_naive_utc` | `_to_db` / `_from_db` | ✅ |
| Design report 3.2 (e-mail) | Codes are sent through the mail server; mail problems are shown, not a crash | Wire `test_verification_code_is_sent_with_starttls_and_login`, `test_port_465_uses_tls_from_the_start`, `test_event_decision_mail_has_the_reason`, `test_mail_server_problems_become_email_delivery_error`, `test_mail_server_problem_is_shown_on_the_sign_up_page` | `SmtpEmailSender`, `EmailDeliveryError` | ✅ |
| Deployment settings | `DATABASE_URL`, `SECRET_KEY`, `SMTP_*` read in one place; tests never write to a real database | Wire `test_without_database_everything_is_in_memory`, `test_from_env_without_settings_keeps_data_and_mails_in_memory`, `test_from_env_uses_database_url_and_smtp_settings`, `test_without_services_the_app_is_built_from_the_environment` | `create_app_from_env` | ✅ |

**Requirements coverage:** 24 of 24 rows have passing tests (100 %). All 12 requirement tests of UC-01, UC-02, UC-03 and NFR-03 pass with #23 and #24.

## Code coverage
Measured on 20.11.2026 with coverage.py, statements **and** branches, all suites of this section (140 tests: 78 unit, 52 database, 10 requirement tests of UC-01 to UC-03) on PostgreSQL 16.16. The 2 NFR-03 requirement tests in `tests/test_nfr.py` were not part of this coverage run; they were run separately in the same session and passed (see below), so the section's 12 requirement tests are 10 + 2. The run was on GitHub Actions with a PostgreSQL 16 service container, on a temporary branch with `main` + #23 + #24 (with the İ fix) + #25; all 140 tests passed.

| File | Statements | Missed | Branches | Partial | Coverage |
|---|---|---|---|---|---|
| `src/campusevent/app.py` | 52 | 0 | 8 | 0 | **100 %** |
| `src/campusevent/auth.py` | 157 | 6 | 42 | 2 | **96 %** |
| `src/campusevent/security.py` | 17 | 0 | 0 | 0 | **100 %** |
| `src/campusevent/profiles.py` | 50 | 5 | 18 | 2 | **90 %** |
| `src/campusevent/notifications.py` | 51 | 3 | 8 | 1 | **93 %** |
| `src/campusevent/repositories/user_repository.py` | 104 | 2 | 6 | 2 | **96 %** |
| `src/campusevent/repositories/profile_repository.py` | 32 | 0 | 2 | 0 | **100 %** |
| `src/campusevent/repositories/unit_of_work.py` | 28 | 0 | 2 | 0 | **100 %** |
| `src/campusevent/repositories/db.py` | 22 | 4 | 6 | 0 | **79 %** |
| **Total** | 513 | 20 | 92 | 7 | **95 %** |

**Not covered:**
- `auth.py`: the check for a role that is not a `Role` value (callers always pass a `Role`); the rollback when the repository fails while a new code is stored; a valid token of an account that was deleted after the log in; the branch that reuses the cached dummy hash.
- `profiles.py`: the rollback when the repository fails during a save, an interest that is not text and a slot that is not a `TimeSlot`. The page never sends these; Emir checked the non-text case by hand in the review of #24. Tests for them are a small follow-up.
- `notifications.py`: the e-mail for an approved event and the in-memory `send_event_decision` (event part, task 3.4; the mail for a rejected event is tested).
- `user_repository.py`: the duplicate check of the in-memory repository (the service checks first) and passing on an `IntegrityError` of another constraint.
- `repositories/db.py`: `get_database_url`, which only Alembic and `scripts/seed_db.py` use.

**Without a database (like CI):** 87 %. The SQL repositories are then not run (`user_repository.py` 67 %, `profile_repository.py` 79 %, `unit_of_work.py` 77 %); the services and the wiring stay the same.

**Other results of the same run:** all 59 `tests/db` tests and the 2 NFR-03 tests passed; the whole suite gave 303 passed, 36 failed (all `NotImplementedError` from `EventService`, tasks 3.4 / 3.6); `ruff check .` clean.

### How to measure
With `main` + #23 + #24 + #25 and `TEST_DATABASE_URL` set (locally in `.env`):
```
pip install coverage
python -m coverage run --branch --source=src/campusevent -m pytest tests/test_auth_accounts.py tests/test_auth_roles.py tests/test_profiles.py tests/test_wiring.py tests/web/test_web_wiring.py tests/db/test_schema.py tests/db/test_unit_of_work.py tests/db/test_user_repository.py tests/db/test_profile_repository.py tests/db/test_app_with_database.py tests/test_uc01_register_and_verify.py tests/test_uc02_login.py tests/test_uc03_manage_profile.py
python -m coverage report -m --include="*/campusevent/auth.py,*/campusevent/profiles.py,*/campusevent/security.py,*/campusevent/notifications.py,*/campusevent/app.py,*/repositories/user_repository.py,*/repositories/profile_repository.py,*/repositories/unit_of_work.py,*/repositories/db.py"
python -m pytest tests/test_nfr.py -k nfr03
```
The last command runs the 2 NFR-03 tests on their own; they are not in the coverage figures above.

Do not pass a dotted module name to pytest-cov (`pytest --cov=campusevent.auth`): Harun found that this makes the database tests fail inside SQLAlchemy (see the [facilities coverage file](facilities.md#how-to-measure)). `coverage run` as above works, and so does plain `python -m pytest --cov` with the settings in `pyproject.toml`, which CI uses since #36 (see the [coverage README](README.md)).
