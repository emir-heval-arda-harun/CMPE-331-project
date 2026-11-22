# AI mistakes caught

Part of the instructor's review (#34, E. Serious AI mistakes caught). The team uses Claude Code to draft code, tests, reviews and report text (see the README, section *AI tools*, and `CLAUDE.md`). Every AI-written change is read and run by a team member and reviewed by a teammate before it is merged. This file lists the cases where that review found a real mistake made by the assistant, with the evidence.

Each entry gives: what the assistant got wrong, who caught it and how, why it mattered, the fix, and what we changed so it does not happen again.

**To add a case:** when the assistant was wrong in a way that mattered, say so in the pull request (as `CLAUDE.md` asks), then add a row here with the links.

## Summary

| # | Date | Where | Mistake | Caught by | Impact if missed | Fix |
|---|---|---|---|---|---|---|
| 1 | 20.11.2026 | #24, `profiles.py` | Turkish capital `İ` lower-cased to `i` plus a combining dot | Emir, code review | Most Turkish interests stored wrong; duplicate interests (BR-14 broken) | `c7de164` + test |
| 2 | 20.11.2026 | #25, `docs/devops/README.md` | Gmail on port 587 suggested for Render, where the free plan blocks SMTP ports | Onur, code review | Verification e-mails never sent on the live site; nobody could sign up | Live site without SMTP (#35); Gmail example replaced in this PR |
| 3 | 21.11.2026 | #35, `README.md` | README said the app reads `DATABASE_URL` from `.env`; it reads only the environment | Emir, code review | Following the README, the app runs on in-memory data and loses everything at restart | `4a0d17e` |
| 4 | 20.11.2026 | Planning (#26) | The assistant gave 22.11 as the test report deadline, from the charter; the instructor had moved it to 25.11 / 29.11 | Heval, while planning | Wrong deadline in the plan for the whole team | #26 |
| 5 | 20.11.2026 | #23–#25 | Task number 3.3 instead of 3.2 in titles and commits, from an outdated plan | Heval, while reading the PRs | Pull requests not traceable to the right WBS task | PR titles corrected |
| 6 | 20.11.2026 | #29, test report | Coverage file said 10 requirement tests where the section said 12 | Harun, report review | Numbers in the report do not add up | `38379ec` |

Cases 1 to 3 would have reached users or the demo. Cases 4 to 6 are about planning and the reports.

## Details

### 1. Turkish capital İ in interests (BR-14)
- **What the assistant wrote:** `ProfileService._clean_interests` normalised interests with `.lower()`. In Python, `"İ".lower()` gives `"i̇"` (`i` plus a combining dot), not a plain `"i"`.
- **Effect:** `"İngilizce kulübü"` was stored as `"i̇ngilizce kulübü"`, shown with a double dot in some fonts, and `"İngilizce kulübü"` and `"ingilizce kulübü"` were saved as two interests. BR-14 says they are one. Since most users type Turkish, this would happen often.
- **How it was caught:** Emir tried edge cases by hand while reviewing #24 ([review](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/24#pullrequestreview-5996561600)). The assistant's own tests passed, because none of them used Turkish letters.
- **Fix:** `c7de164` maps `"İ"` to `"i"` before `.lower()`. The new test `test_turkish_capital_i_becomes_a_plain_i` checks it.
- **Lesson:** Unit tests written by the same assistant that wrote the code share its blind spots. Reviewers now try inputs from our real users (Turkish text, Istanbul time), not only the cases in the tests. The defect is also listed in the testing report (#29, defects table).

### 2. SMTP on Render's free plan
- **What the assistant wrote:** In #25 the deployment notes suggested sending the verification e-mails through Gmail on port 587.
- **Effect:** Render's free web services block outgoing traffic on ports 25, 465 and 587. On the live site, no verification code would arrive, so new users could never finish signing up (UC-01).
- **How it was caught:** Onur checked the Render changelog while reviewing #25 ([review](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/25#pullrequestreview-5995644703)).
- **Fix:** Onur proposed a relay on port 2525 (Brevo), which `SmtpEmailSender` already supports. For the demo, the live deployment runs without SMTP on purpose. The demo users of `scripts/seed_db.py` are already verified, and #35 documents this together with the free-plan limits. The Gmail example was still in `docs/devops/README.md` on `main`; this pull request replaces it with the port limit.
- **Lesson:** Platform limits are not in the code. The assistant cannot see them unless someone checks the provider's current documentation.

### 3. How to run the app with PostgreSQL
- **What the assistant wrote:** The first version of the README in #35 said that with `DATABASE_URL` in `.env`, "the app stores its data in the database". It also gave `scripts/run_demo.py` as the only start command.
- **Effect:** `create_app_from_env()` reads `DATABASE_URL` only from the environment. Only Alembic, `seed_db.py`, `run_demo.py` and the database tests read `.env`, and `run_demo.py` always uses in-memory data. Anyone following the README, including the instructor, would have run the app without the database and without noticing it. Logging in locally also needs `SESSION_COOKIE_SECURE=0`, which was missing.
- **How it was caught:** Emir compared the README with `app.py` and `repositories/db.py` while reviewing #35 ([review](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/35#pullrequestreview-6008128648)).
- **Fix:** In `4a0d17e` Harun wrote the real steps and ran them against his local PostgreSQL. The `/login` page answered 200 with no "DATABASE_URL is not set" warning.
- **Lesson:** Documentation is checked against the code like code is. Every command in a README is run once before review.

### 4. Wrong deadline from an outdated source
- **What the assistant did:** While planning on 20.11, it said the Software Testing Report was due on 22.11, the date in the charter and the plan.
- **Effect:** The instructor's announcement of 17.11 had moved it to a pull request reviewed by Yeşim by 25.11 and the PDF by 29.11, with new required folders (`docs/tests/coverage`, `non-func-tests`, `quality`). The assistant could not find this announcement in the sources it can read.
- **How it was caught:** Heval remembered the announcement and pasted it again.
- **Fix:** #26 updates the plan, Gantt and PERT charts, the charter and the requirements specification.
- **Lesson:** Course announcements that only exist on Learn have to be copied into the repository (the plan) so that people and the assistant work from the same dates.

### 5. Outdated task numbers
- **What the assistant did:** It labelled the accounts and profiles work as task 3.3 in the pull request titles and in commits (for example `ce7d97f` in #24 and `5f1aa59` in #25). It took the number from an old note written before the plan was renumbered in October, when the project changed from sports matching to CampusEvent.
- **How it was caught:** Heval noticed it while reading the pull requests. The assistant then checked the plan and the git history.
- **Fix:** The PR titles and task references now say 3.2. The merged commit messages keep the old number; this file records that they mean 3.2.
- **Lesson:** The assistant checks the current plan in the repository, not notes from earlier sessions.

### 6. Requirement test count in the testing report
- **What the assistant wrote:** The accounts section of the testing report said 12 requirement tests. The coverage file counted 140 tests as 78 + 52 + 10, because the coverage command did not include `tests/test_nfr.py`.
- **How it was caught:** Harun added up the numbers while reviewing #29 ([review](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/29#pullrequestreview-5999608721)).
- **Fix:** `38379ec` says 12 = 10 UC + 2 NFR-03 in both files and adds the NFR-03 command to "How to measure".
- **Lesson:** Numbers in the report come from one run, and the report says which command produced them.

## What we changed in the way we work
- **Peer review on every pull request** (branch protection on `main`, one approving review). All six cases were caught in a review or while reading the assistant's output, not by the assistant itself.
- **`CLAUDE.md`** (#35) writes down the project rules the assistant got wrong or could easily get wrong: UTC in the services, where settings are read, transactions, roles, CSRF, secrets.
- **Reviewers test like users:** real Turkish input, the real database, the live deployment, not only the assistant's tests.
- **Primary sources first:** dates come from the instructor's announcements copied into the plan, platform limits from the provider's documentation, and behaviour from the code itself.
