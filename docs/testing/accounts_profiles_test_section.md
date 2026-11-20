# Software Testing Report – Accounts, profiles and database section (tasks 3.1 and 3.2)

**Author:** Heval Hüseyin Demir · **Status:** section for the team's Software Testing Report (task 4.1: pull request to Yeşim by 25.11.2026, PDF on Learn by 29.11.2026, see #26) · **Date of the results:** 20.11.2026

It covers UC-01 *Register and verify e-mail*, UC-02 *Log in* and UC-03 *Manage profile*: the database layer (task 3.1, PR #12: schema, Alembic migration, `UnitOfWork`), the account and profile services (task 3.2: PR #17 roles, PR #23 accounts, PR #24 profiles) and the wiring of the SQL classes and the mail server (PR #25). The results below are for `main` together with PRs #23, #24 and #25. The web pages of these use cases are in the [Web UI section](web_ui_test_section.md); the facility part is in the [facilities section](facility_test_section.md).

The parts the instructor asked for on 17.11 are in their own files:
- **Traceability matrix with code and requirements coverage:** [`docs/tests/coverage/accounts-profiles.md`](../tests/coverage/accounts-profiles.md)
- **Non-functional tests and their results:** [`docs/tests/non-func-tests/accounts-profiles.md`](../tests/non-func-tests/accounts-profiles.md)

## 1. Scope and approach

| Level | What is tested | Test doubles | Files | Run |
|---|---|---|---|---|
| Unit | `AuthService` (register, verify, new code, log in, session token, roles), `ProfileService`, `create_app` wiring, `SmtpEmailSender` | `InMemoryUserRepository`, `InMemoryProfileRepository`, `InMemoryUnitOfWork`; a recording e-mail sender; a fake clock for code and token expiry; a fake SMTP server; argon2id with small cost settings so the suite stays fast (still salted hashes) | [`tests/test_auth_accounts.py`](../../tests/test_auth_accounts.py), [`tests/test_auth_roles.py`](../../tests/test_auth_roles.py), [`tests/test_profiles.py`](../../tests/test_profiles.py), [`tests/test_wiring.py`](../../tests/test_wiring.py), [`tests/web/test_web_wiring.py`](../../tests/web/test_web_wiring.py) | `python -m pytest tests/test_auth_accounts.py tests/test_auth_roles.py tests/test_profiles.py tests/test_wiring.py tests/web/test_web_wiring.py` |
| Database | The schema and its constraints, the migration, `SqlUnitOfWork`, `SqlUserRepository`, `SqlProfileRepository`, and the services on a **real PostgreSQL 16** database, also across several web requests | none | [`tests/db/test_schema.py`](../../tests/db/test_schema.py), [`tests/db/test_unit_of_work.py`](../../tests/db/test_unit_of_work.py), [`tests/db/test_user_repository.py`](../../tests/db/test_user_repository.py), [`tests/db/test_profile_repository.py`](../../tests/db/test_profile_repository.py), [`tests/db/test_app_with_database.py`](../../tests/db/test_app_with_database.py) | `python -m pytest tests/db` (needs `TEST_DATABASE_URL`, see [database README](../database/README.md)) |
| Requirement | The team's acceptance tests for UC-01, UC-02, UC-03 and NFR-03 through `create_app()` | none (real services, in-memory storage) | [`tests/test_uc01_register_and_verify.py`](../../tests/test_uc01_register_and_verify.py), [`tests/test_uc02_login.py`](../../tests/test_uc02_login.py), [`tests/test_uc03_manage_profile.py`](../../tests/test_uc03_manage_profile.py), [`tests/test_nfr.py`](../../tests/test_nfr.py) | `python -m pytest tests/test_uc01_register_and_verify.py tests/test_uc02_login.py tests/test_uc03_manage_profile.py tests/test_nfr.py -k "uc0 or nfr03"` |

**Why in-memory repositories in the unit tests:** the services only talk to the repository and `UnitOfWork` interfaces of class diagram 4.2, so the same rules can be tested fast and without a database. The SQL versions of the same interfaces are tested separately on PostgreSQL, and `tests/db/test_app_with_database.py` runs the real app with the SQL classes from sign-up to saving a profile.

**Tools:** pytest, Flask test client, SQLAlchemy 2.1, psycopg 3, Alembic, argon2-cffi, PostgreSQL 16.16 (local, Windows, Python 3.14), coverage.py (branch coverage), ruff. CI (GitHub Actions) runs ruff and pytest on every push and pull request; it has no database, so `tests/db` is skipped there and was run locally.

## 2. Results

| Suite | Tests | Passed | Failed | Where |
|---|---|---|---|---|
| Unit, accounts (`test_auth_accounts.py`) | 35 | 35 | 0 | local and CI |
| Unit, roles (`test_auth_roles.py`) | 12 | 12 | 0 | local and CI |
| Unit, profiles (`test_profiles.py`) | 17 | 17 | 0 | CI (the 17th, the Turkish İ test, was added after the local run) |
| Unit, wiring and mail (`test_wiring.py`, `web/test_web_wiring.py`) | 14 | 14 | 0 | local and CI |
| Database, this section (`tests/db` without the facility file) | 52 | 52 | 0 | local PostgreSQL 16.16 (skipped in CI) |
| Requirement tests UC-01, UC-02, UC-03, NFR-03 | 12 | 12 | 0 | local and CI, with #23 and #24 |

The whole `tests/db` folder (59 tests, including the 7 facility tests of that day) passed on the local PostgreSQL. The whole suite gave **302 passed, 36 failed**; all 36 failures are `NotImplementedError` from `EventService` (tasks 3.4 / 3.6), the same as in CI. `ruff check .` is clean.

**Code coverage:** see the [coverage file](../tests/coverage/accounts-profiles.md#code-coverage).

## 3. Traceability
The matrix (requirement → tests → code, with the result of each requirement) is in [`docs/tests/coverage/accounts-profiles.md`](../tests/coverage/accounts-profiles.md#traceability-matrix). Every step and alternative flow of UC-01, UC-02 and UC-03, BR-01, BR-02, BR-03 and BR-14, and the database rules of the design report have at least one passing test.

## 4. Test design
- **Equivalence classes and boundary values.** E-mail: exact university domains only (`ayse@bilgiedu.net.evil.com`, `ayse@mail.bilgiedu.net`, `ayse@gmail.com` refused), malformed addresses (empty, no `@`, a space, 254+ characters). Password: empty, 7 characters (refused), 129 characters (refused). Full name: empty, only spaces, 101 characters (refused). Interest: 60 characters (accepted), 61 (refused). Event capacity in the database: 1 (refused).
- **Time boundaries.** The verification code works just before 15 minutes and not after (`test_code_works_just_before_it_expires`, `test_code_does_not_work_after_15_minutes`). The session token stops working after 24 hours. Time slots must end after they start. Times are stored as naive UTC and read back unchanged (team time rule, #16).
- **Normalization.** E-mail is trimmed and lower-cased before it is stored, compared or used to log in; the database also refuses the same e-mail in another case (`ux_user_email_lower`). Interests are trimmed, inner spaces joined, lower-cased and kept once (BR-14), including the Turkish capital İ.
- **Negative tests with "nothing changed" checks.** Every refused register or profile change checks that nothing was stored, no e-mail was sent and the `UnitOfWork` rolled back (`test_rejected_input_stores_nothing_and_sends_nothing`, `test_invalid_change_keeps_the_saved_profile`). In the database, each constraint is tested with a row that breaks it and the exact constraint name in the error.
- **Security-oriented tests.** An unknown e-mail and a wrong password give the same message; an unverified user with a wrong password is not told that the account exists; a changed, made-up or other-key token is refused; passwords and codes are stored only as argon2id hashes, and the same password gives two different stored values.
- **Integration inside this section.** The SQL repositories are used together with the real services (`test_register_verify_and_login_with_postgresql`, `test_profile_service_with_postgresql`), and the whole app is driven through the web pages with PostgreSQL behind it (`test_sign_up_log_in_and_save_profile_across_requests`).
- **Migration tests.** The migration creates the eight tables, `tables.py` matches it (Alembic autogenerate compare), and it can be undone and done again.

## 5. Defects found while testing

| # | Found by | Defect | Fix |
|---|---|---|---|
| 1 | Review of #24 by Emir | `str.lower()` turns the Turkish `"İ"` into `"i"` plus a combining dot, so `"İngilizce"` and `"ingilizce"` were stored as two interests (against BR-14), and the stored text showed a double dot in some fonts | `_clean_interests` maps `"İ"` to `"i"` before lower-casing; new test `test_turkish_capital_i_becomes_a_plain_i` (commit c7de164 in #24) |
| 2 | Preparing the deployment (PR #25) | `create_app` always used the in-memory repositories, so the deployed app stored nothing in PostgreSQL and sent no e-mails | PR #25: `create_app(database_url=...)` uses the SQL classes with one session and one `UnitOfWork` per request; `SmtpEmailSender`; tests in `test_wiring.py` and `test_app_with_database.py` |
| 3 | Review of #25 by Onur | Render free web services block outgoing traffic on ports 25, 465 and 587, so the Gmail-on-587 example would not send codes on Render | Brevo on port 2525 with STARTTLS, which `SmtpEmailSender` already supports; documented by Onur in task 4.4 |
| 4 | Setting up the local test database | The PostgreSQL installer fails on Windows with the Turkish locale (`locale name "Turkish_Türkiye.1254" contains non-ASCII characters`) | Setup problem, not code: choose locale *English, United States*; written in the [database README](../database/README.md) |

## 6. Limits and what integration testing (task 4.2) must check
- **Event part:** 36 requirement tests still stop at `EventService` (`NotImplementedError`). When task 3.4 is done, `SqlEventRepository` must be created in the `if database_url:` block of `create_app` with the same session, and the whole suite must be run on PostgreSQL.
- **Order of interests:** the SQL repository returns interests in alphabetical order (the table has no position column); the in-memory one keeps the order the student typed. Pages must not depend on the order.
- **Wrong code attempts:** there is no limit on wrong verification codes yet (6 digits, valid 15 minutes). Accepted for the demo; open as an issue for later (Harun's review of #23).
- **CI has no database:** `tests/db` runs only on a computer with `TEST_DATABASE_URL`. A PostgreSQL service in CI would run it on every pull request (suggestion for task 3.7).
- **On Render (task 4.4):** run `alembic upgrade head` (and `scripts/seed_db.py` for the demo users), set `SECRET_KEY` and the `SMTP_*` settings, and check once that a real verification code arrives and that the site is served only over HTTPS (NFR-03).
