# CampusEvent – Requirements Specification Report

**Course:** CMPE 331 – Software Engineering
**Group:** 14
**Team:** Heval Hüseyin Demir, Emre Arda Kum, Emir Gül, Harun Gündaş, Onur Alioğlu
**Repository:** https://github.com/emir-heval-arda-harun/CMPE-331-project
**Date:** 07.10.2026

---

## 1. Introduction

### 1.1 Purpose
This document defines the requirements of **CampusEvent**, a social sports-matching platform for university students. It is the reference for the design, implementation and testing phases of the project.

### 1.2 Scope
CampusEvent lets students organize, find and join amateur sports matches on campus, balances teams using AI, supports club tournaments with automatic brackets, and prevents facility booking conflicts.

**In scope:** user authentication and profiles, match creation and joining, filtering, AI team balancing, tournaments and brackets, facility schedules, activity history.

**Out of scope** (from the [Project Charter](CHARTER.MD)): payments, real-time GPS tracking, SIS/Banner integration, live audio/video and in-app chat, native mobile apps.

### 1.3 Definitions
| Term | Meaning |
|---|---|
| Match | An amateur sports activity at a campus facility, created by a student |
| Organizer | The student who created a match |
| Skill level | Beginner / Intermediate / Advanced, declared per sport |
| Bracket | The single-elimination tree of a tournament |
| Bye | A free pass to the next round when the team count is not a power of two |
| Facility block | A period when a facility is closed to student matches |

### 1.4 References
- [Project Charter](CHARTER.MD)
- [Project plan: Gantt and PERT charts](plan/README.md)
- [Use case documents](requirements/README.md)

---

## 2. Overall Description

### 2.1 Product Perspective
CampusEvent is a new, standalone, responsive web application. It uses Gemini Pro as an external AI service for skill rating and an e-mail service for account verification. It does **not** connect to university information systems.

### 2.2 User Classes
| Actor | Description |
|---|---|
| **Student** | Main user. Creates, finds and joins matches, manages a profile. |
| **Club Representative** | A student with a club role. Organizes tournaments. |
| **Facility Staff** | Campus sports personnel. Define facilities and block unavailable times. |
| **Gemini Pro (external)** | AI service that rates players' skill for team balancing. |
| **E-mail Service (external)** | Sends verification codes. |

### 2.3 Operating Environment
- Modern desktop and mobile web browsers (responsive web, no native app).
- Backend in Python (the charter also lists Java); frontend in HTML, CSS and JavaScript.

### 2.4 Constraints
- Users are identified only by university e-mail domain (no SIS integration).
- Only predefined campus facilities are used; no GPS.
- No payment features.

### 2.5 Assumptions and Dependencies
- Students have an active university e-mail address.
- Facility staff keep facility schedules up to date.
- The Gemini Pro API is reachable; if not, the system falls back to self-declared skill levels (UC-07).

---

## 3. Project Plan

The planning documents are in [`docs/plan/`](plan/README.md).

### 3.1 Gantt Chart
![Gantt chart](plan/gantt_chart.png)

### 3.2 PERT Chart
Critical path: 1.0 → 2.0 → 3.1 → 4.2 → 5.0 → 6.3 → 7.0 → 8.0 (**56 days**).

![PERT chart](plan/pert_chart.png)

### 3.3 Milestones
| Deliverable | Deadline |
|---|---|
| Project Charter | 02.10.2026 |
| Requirements Definition Report | 11.10.2026 |
| Requirement Analysis Report | 18.10.2026 |
| Software Design Report | 15.11.2026 |
| Software Testing Report | 22.11.2026 |
| Codebase | 30.11.2026 |

---

## 4. Functional Requirements (Use Cases)

The functional requirements are written in **use case format**. Each use case is in its own file under [`docs/requirements/`](requirements/README.md).

### 4.1 Use Case Diagram
![Use case diagram](requirements/diagrams/use_case_diagram.png)

### 4.2 Use Case Summary
| ID | Use Case | Primary Actor | Priority | Summary |
|---|---|---|---|---|
| [UC-01](requirements/UC-01_register_and_verify.md) | Register & verify e-mail | Student | High | Sign up with a university e-mail; account activated with an e-mailed code. |
| [UC-02](requirements/UC-02_login.md) | Log in | All users | High | Verified users log in with e-mail and password. |
| [UC-03](requirements/UC-03_manage_profile.md) | Manage profile | Student | High | Preferred sports, skill level per sport, availability. |
| [UC-04](requirements/UC-04_create_match.md) | Create match | Student | High | Sport, facility, time, capacity, skill level; facility must be free. |
| [UC-05](requirements/UC-05_browse_and_filter_matches.md) | Browse & filter matches | Student | High | Filter by date, time, sport, skill level. |
| [UC-06](requirements/UC-06_join_match.md) | Join match | Student | High | Join if free places exist; match becomes Full at capacity. |
| [UC-07](requirements/UC-07_ai_team_balancing.md) | AI team balancing | Organizer, Gemini Pro | Medium | AI rates players; teams get similar total skill; fallback without AI. |
| [UC-08](requirements/UC-08_create_tournament.md) | Create tournament | Club Representative | Medium | Name, sport, teams; only club representatives. |
| [UC-09](requirements/UC-09_generate_bracket.md) | Generate bracket | Club Representative | Medium | Automatic single-elimination bracket with byes. |
| [UC-10](requirements/UC-10_record_score.md) | Record score & advance | Club Representative | Medium | Enter scores, winner advances, final sets the champion. |
| [UC-11](requirements/UC-11_facility_availability.md) | Facility schedule & conflicts | Student | High | Show busy slots; prevent overlapping bookings. |
| [UC-12](requirements/UC-12_manage_facility_schedule.md) | Manage facility schedule | Facility Staff | Medium | Add facilities and blocked periods. |
| [UC-13](requirements/UC-13_activity_history.md) | Track activity history | Student | Low | List completed matches the student played in. |

---

## 5. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Usability | The web interface is responsive and usable on screens from 360 px (phone) to desktop width. |
| NFR-02 | Performance | Match search (UC-05) returns results in under 2 seconds for up to 1,000 open matches. |
| NFR-03 | Performance | Team balancing (UC-07) completes in under 10 seconds, including the AI call. |
| NFR-04 | Security | Passwords are stored only as salted hashes; all traffic uses HTTPS. |
| NFR-05 | Security | Role-based access: only club representatives manage tournaments, only facility staff manage facilities. |
| NFR-06 | Privacy | Only data needed for rating (sports, skill levels, match history) is sent to the AI service; no names or e-mail addresses. Personal data is processed in line with KVKK. |
| NFR-07 | Reliability | If the AI service is unavailable, team balancing still works using declared skill levels. |
| NFR-08 | Maintainability | Each use case has automated tests; the test suite runs with a single command (`python -m pytest`). |
| NFR-09 | Portability | The system runs on current versions of Chrome, Firefox, Safari and Edge. |

---

## 6. Requirement Tests

Every use case has a test file under [`tests/`](../tests). The tests describe the expected behaviour of the main flow and the important alternative flows.

The code under [`src/campusevent/`](../src/campusevent) is only **boilerplate**: domain models, service classes and method signatures. Every service method raises `NotImplementedError`, so **all tests currently fail by design**. They will pass as the features are implemented in the development phase.

**How to run:**
```bash
pip install -r requirements-dev.txt
python -m pytest
```

**Current result:** 36 tests, 36 failed (expected).

---

## 7. Traceability Matrix

| Use Case | Test File | # Tests | Source Module |
|---|---|---|---|
| UC-01 | [test_uc01_register_and_verify.py](../tests/test_uc01_register_and_verify.py) | 5 | [auth.py](../src/campusevent/auth.py) |
| UC-02 | [test_uc02_login.py](../tests/test_uc02_login.py) | 3 | [auth.py](../src/campusevent/auth.py) |
| UC-03 | [test_uc03_manage_profile.py](../tests/test_uc03_manage_profile.py) | 2 | [profiles.py](../src/campusevent/profiles.py) |
| UC-04 | [test_uc04_create_match.py](../tests/test_uc04_create_match.py) | 3 | [matches.py](../src/campusevent/matches.py) |
| UC-05 | [test_uc05_browse_and_filter_matches.py](../tests/test_uc05_browse_and_filter_matches.py) | 3 | [matches.py](../src/campusevent/matches.py) |
| UC-06 | [test_uc06_join_match.py](../tests/test_uc06_join_match.py) | 3 | [matches.py](../src/campusevent/matches.py) |
| UC-07 | [test_uc07_ai_team_balancing.py](../tests/test_uc07_ai_team_balancing.py) | 2 | [matchmaking.py](../src/campusevent/matchmaking.py) |
| UC-08 | [test_uc08_create_tournament.py](../tests/test_uc08_create_tournament.py) | 3 | [tournaments.py](../src/campusevent/tournaments.py) |
| UC-09 | [test_uc09_generate_bracket.py](../tests/test_uc09_generate_bracket.py) | 2 | [tournaments.py](../src/campusevent/tournaments.py) |
| UC-10 | [test_uc10_record_score.py](../tests/test_uc10_record_score.py) | 4 | [tournaments.py](../src/campusevent/tournaments.py) |
| UC-11 | [test_uc11_facility_availability.py](../tests/test_uc11_facility_availability.py) | 2 | [facilities.py](../src/campusevent/facilities.py) |
| UC-12 | [test_uc12_manage_facility_schedule.py](../tests/test_uc12_manage_facility_schedule.py) | 2 | [facilities.py](../src/campusevent/facilities.py) |
| UC-13 | [test_uc13_activity_history.py](../tests/test_uc13_activity_history.py) | 2 | [matches.py](../src/campusevent/matches.py) |

---

## 8. Repository Artifacts

| Artifact | Location |
|---|---|
| Project Charter | [`docs/CHARTER.MD`](CHARTER.MD) |
| Plan documents (Gantt, PERT) | [`docs/plan/`](plan/README.md) |
| Use cases and diagram | [`docs/requirements/`](requirements/README.md) |
| Requirement tests | [`tests/`](../tests) |
| Boilerplate source code | [`src/campusevent/`](../src/campusevent) |
| This report | [`docs/requirements_specification.md`](requirements_specification.md) |
