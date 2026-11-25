# AI mistakes caught

Part of the instructor's review (#34, E. Serious AI mistakes caught). The team uses Claude Code to draft code, tests, reviews and report text (see the README, section *AI tools*, and `CLAUDE.md`). Every AI-written change is read and run by a team member and reviewed by a teammate before it is merged (case 8 is the one time this did not happen). This file lists the cases where a team member found a real mistake made by the assistant, with the evidence.

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
| 7 | 17.11.2026 | #7, `scripts/run_demo.py` | Demo password and session key written in the code of the public repository | Emir, own question before the merge | A pattern that puts real secrets on GitHub once real accounts exist | `d7da9f3`, before the merge |
| 8 | 18.11.2026 | #7 | Merged the pull request into `main` without an approving review | Emir, the next morning | `main` holds code nobody else has read; the team rule is broken | Review asked afterwards, approved the same day |
| 9 | 18.11.2026 | #14, web UI | Times sent to the services in Istanbul time, not in UTC; calendar file without a time zone | Emir, own questions while checking | Every event and booking 3 hours off with the real services, with no error | `e2eae80`, `0cb56bb`, `3c434da` |
| 10 | 19.11.2026 | #21, UI/UX document | Wrote "every field has a visible label"; one field on Create Event had no label at all | Emir, checking the test report | A screen reader cannot name the field (WCAG 1.3.1, 3.3.2); a false claim in a delivered document | #32 (`c66359c`) + a test for every form field |
| 11 | 21.11.2026 | #33 / #38, `EventService` | `ValidationError` used instead of `PermissionDeniedError`, `EventFullError`, and `AlreadyJoinedError` | Harun & Emir, review of #33 | Wrong HTTP status codes (400 instead of 403/409); four requirement tests failed | `PermissionDeniedError` in #33; `1703b5f` and `12f519d` in #38 |
| 12 | 21.11.2026 | #33 / #38, `EventService` | Past start times accepted; no completion/expiry settlement or past-time check on approval | Emir, review of #33 | Past events could be created, approved, listed, and joined; history and expiry stayed stuck | `1703b5f` and `12f519d` in #38 |
| 13 | 21.11.2026 | #33 / #38, `EventService` | `get_event` method missing from `EventService` | Emir, review of #33 | Event detail, join, leave, cancel, and calendar actions returned 500 | `12f519d` in #38 |
| 14 | 21–24.11.2026 | #52 / #58, `SqlEventRepository` | N+1 queries loading participants per event row | Emir, PostgreSQL testing (#52) | Whole pages took 2.1–3.2 s (3,000–4,500 SQL statements), exceeding NFR-02 | `selectinload` in #58 (0.22–0.35 s, 14–25 statements) |

Cases 1 to 3, 9, and 11 to 14 would have reached users or the demo (and case 10 users of screen readers). Cases 4 to 6 are about planning and the reports. Cases 7 and 8 are about how the repository is used.

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

### 7. Demo password in the code
- **What the assistant wrote:** The first demo runner (`2f16124` in #7) had the password of the demo accounts and the Flask session key written in `scripts/run_demo.py`, in a public repository.
- **Effect:** The demo accounts exist only in memory on one's own computer, so nothing could be opened with them. But the pattern was wrong: the same habit with the real database or e-mail settings would publish them on GitHub.
- **How it was caught:** Emir asked whether passwords should be in `.env` instead of the code, while #7 was still open.
- **Fix:** `d7da9f3`, still before #7 was merged: `.env` and key files in `.gitignore`, `.env.example` with names and no values, the demo password from `CAMPUSEVENT_DEMO_PASSWORD` or random at every start, a random session key. The old demo password is still in the history of `2f16124`; it opens nothing.
- **Lesson:** No secret in the code, also not a "harmless" one; only `.env.example` is committed. This rule is in `CLAUDE.md`.

### 8. Merged without a review
- **What the assistant did:** On 18.11 Emir said "merge" for #7, and the assistant merged it into `main` at once. It did not check that the team needs an approving review first.
- **Effect:** The web UI reached `main` without anyone else reading it. Nothing broke (the tests ran on `main`), but the rule that every change is reviewed was broken.
- **How it was caught:** Emir noticed it the next morning.
- **Fix:** Emir explained it on #7 and asked Heval for a review ([comment](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/7#issuecomment-6976518591)); Heval approved it the same day ([review](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/7#pullrequestreview-5959021944)).
- **Lesson:** The assistant merges only after an approving review and the explicit OK of its user, with a merge commit. `main` is protected with one approving review.

### 9. Times not in UTC
- **What the assistant wrote:** The web UI passed the times typed on the pages to the services as they were, in Istanbul time. The database guide already said that the database keeps naive UTC (`e5c6cba`). The *Add to calendar* file also had no time zone.
- **Effect:** With the test doubles all tests passed. With the real services, every event and every facility booking would have been 3 hours off, without any error message. A calendar set to another time zone would have shown the wrong hour.
- **How it was caught:** Emir asked what the downloaded calendar file contains, and later how Harun's facility backend (#13) affects the web UI; the second question made the assistant compare the pages with the database guide.
- **Fix:** In #14: `e2eae80` (time zone in the calendar file), `0cb56bb` ("Today" from the Istanbul clock, since the server on Render runs in UTC), then the team time rule (`012a0fc`) and `3c434da`, which converts only in the web layer. The tests now give the times in UTC, as the real services keep them.
- **Lesson:** Test doubles have to follow the same rules as the real services, or the tests pass for the wrong reason. The time rule (UTC in the services, Istanbul time only on the pages) is in `docs/database/README.md` and `CLAUDE.md`.

### 10. "Every field has a visible label"
- **What the assistant wrote:** Section 8 of the UI/UX document (`82b2111`, #21) said "every field has a visible label". On Create Event, the category text box had no label: without JavaScript the label *Category* named the hidden list, and the box for *Other…* had only a placeholder.
- **Effect:** A screen reader could not say what the field is for (WCAG 1.3.1, 3.3.2; NFR-01), and a delivered document said the opposite.
- **How it was caught:** While checking the web UI part of the testing report, Emir had every form field searched for a label, instead of trusting the sentence in the document. The search found this box.
- **Fix:** #32 (`c66359c`): *Category* names the visible field and the *Other…* box has its own label. `test_every_form_field_has_a_label` opens every form and checks every field; it found this box and nothing else. Section 8 now gives the exact rule. Heval reviewed it ([review](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/32#pullrequestreview-6004504201)).
- **Lesson:** A claim like "every field" is checked against every field, by a test where possible, not by re-reading the text.

### 11. Wrong error types in EventService
- **What the assistant wrote:** `join_event` raised `ValidationError` when the event was full or the student had already joined, and `cancel_event` raised it when someone other than the organizer tried to cancel.
- **Effect:** The pages turn `EventFullError` and `AlreadyJoinedError` into 409 and `PermissionDeniedError` into 403. With `ValidationError` they answered 400, and four requirement tests failed (`test_only_the_organizer_can_cancel`, `test_nfr04_only_the_organizer_can_cancel_an_event`, the full-event test, and the join-twice test).
- **How it was caught:** Harun and Emir ran the whole suite against the real services while reviewing #33 (reviews of #33 by [Harun](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/33#pullrequestreview-6007205437), [Emir 1](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/33#pullrequestreview-6007187603) and [Emir 2](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/33#pullrequestreview-6007705849)). The assistant's own unit test for joining twice expected `ValidationError` as well, so it passed.
- **Fix:** `PermissionDeniedError` for the non-organizer in #33; `EventFullError` and `AlreadyJoinedError` in #38 (commits `1703b5f` and `12f519d`).
- **Lesson:** The assistant had not been given `exceptions.py` or the design report's error list, and wrote tests that agree with its own code. Errors follow the Software Design Report; roles raise `PermissionDeniedError` (`CLAUDE.md`).

### 12. Events in the past and statuses that never change
- **What the assistant wrote:** `create_event` accepted a start time in the past; the lists and `join_event` did not look at the time. Nothing called `complete_event` or `expire_pending_requests`, and `approve_event` approved a request whose start time had passed.
- **Effect:** Emir created an event for January 2025, approved it, saw it on Find Events, and a student joined it. The history stayed empty (BR-11) and pending requests never expired (BR-18).
- **How it was caught:** Emir tried these cases on the real pages (reviews of #33 by [Harun](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/33#pullrequestreview-6007205437), [Emir 1](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/33#pullrequestreview-6007187603) and [Emir 2](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/33#pullrequestreview-6007705849)).
- **Fix:** In #38, commit `1703b5f` (test clock) and commit `12f519d` (`get_event`, past events, and settling): no events in the past, lists show upcoming events, `approve_event` refuses an expired request, and finished events and expired requests are settled before the lists are read.
- **Lesson:** Anything that depends on the date is tested with a clock that the test controls, not only with the dates that happen to be in the fixtures.

### 13. `get_event` missing
- **What the assistant did:** Implemented the methods named in the skeleton and the use cases, but not `get_event`, which Emir's pages call.
- **Effect:** Event Details, join, leave, cancel and "Add to calendar" answered 500.
- **How it was caught:** Emir ran his pages against the real `EventService`; with a stand-in `get_event` they all worked (reviews of #33 by [Harun](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/33#pullrequestreview-6007205437), [Emir 1](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/33#pullrequestreview-6007187603) and [Emir 2](https://github.com/emir-heval-arda-harun/CMPE-331-project/pull/33#pullrequestreview-6007705849)).
- **Fix:** Commit `12f519d` in #38 adds `get_event(event_id)` (`NotFoundError` for an unknown id).
- **Lesson:** The assistant is told which methods the other layers call, not only which use cases exist.

### 14. N+1 queries in `SqlEventRepository`
- **What the assistant wrote:** `_to_domain` reads `row.participants`, which loads the participants of each event with a separate `SELECT`.
- **Effect:** With 1,000 open events, Find Events took 2.1 to 3.1 s, My Activities 3.2 s and Event Requests 2.8 to 3.1 s, with about 3,000 to 4,500 SQL statements per request, over the 2 s of NFR-02. The in-memory performance tests could not show it.
- **How it was caught:** Emir measured the pages with the real services on PostgreSQL (issue #52).
- **Fix:** #58 (merged 25.11) loads the participants of a whole list with one more query (`selectinload`) in the four list methods. According to #52, whole pages (Find Events, My Activities, Event Requests) take 0.22 to 0.35 s on the server with 14 to 25 statements.
- **Lesson:** Repository methods that return lists are measured on PostgreSQL with real amounts of data, not only in memory.

Cases 11 to 14 are about the events backend (#33, #38, #52, and #58): wrong error types, time handling, a missing method, and a performance defect that only appeared on PostgreSQL.

## What we changed in the way we work
- **Peer review on every pull request** (branch protection on `main`, one approving review). All fourteen cases were caught by a person, in a review, while reading the assistant's output, by asking it a question, or by measuring, not by the assistant on its own.
- **The assistant merges nothing without an approving review** and the explicit OK of the team member who works with it (case 8). It shows a review or a comment to that person before posting it.
- **Claims are checked against the code:** every number, test name and "every …" in a report or document is compared with the code or a test, not only re-read (cases 6 and 10).
- **`CLAUDE.md`** (#35) writes down the project rules the assistant got wrong or could easily get wrong: UTC in the services, where settings are read, transactions, roles, CSRF, secrets.
- **Reviewers test like users:** real Turkish input, the real database, the live deployment, not only the assistant's tests.
- **Primary sources first:** dates come from the instructor's announcements copied into the plan, platform limits from the provider's documentation, and behaviour from the code itself.
