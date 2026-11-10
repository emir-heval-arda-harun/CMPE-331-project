# CampusEvent – Software Design Report

**Course:** CMPE 331 – Software Engineering **Group:** 14 **Team:** Heval Hüseyin Demir, Emre Arda Kum, Emir Gül, Harun Gündaş, Onur Alioğlu **Repository:** https://github.com/emir-heval-arda-harun/CMPE-331-project **Date:** 10.11.2026

---

## 1. Introduction

### 1.1 Purpose
This report describes **how** CampusEvent will be built. It turns the 11 use cases of the [Requirements Specification](requirements_specification.md) and the models of the [Requirement Analysis Report](requirement_analysis_report.md) into an architecture, a class design and object interactions, and it explains the design decisions taken for the non-functional requirements (NFR-01 to NFR-07).

### 1.2 Scope of the design
CampusEvent is a responsive web application where students organize, find and join events of any kind at campus facilities, and facility staff manage facilities and their schedules. The design covers the web application, its database, the e-mail integration, the test setup and the deployment.

### 1.3 Design artifacts
All models are stored as Mermaid sources with PNG and SVG exports under [`docs/design/`](design/README.md):

| Folder | Content |
|---|---|
| [`design/arch/`](design/arch/) | Layered architecture diagram, deployment diagram |
| [`design/class/`](design/class/) | Domain class diagram, service and data access class diagram |
| [`design/sequence/`](design/sequence/) | Six design-level sequence diagrams covering 9 of 11 use cases |

### 1.4 Inputs
| Document | Location |
|---|---|
| Project Charter | [CHARTER.MD](CHARTER.MD) |
| Requirements Specification | [requirements_specification.md](requirements_specification.md) |
| Requirement Analysis Report | [requirement_analysis_report.md](requirement_analysis_report.md) |
| Use cases UC-01 … UC-11 | [requirements/](requirements/README.md) |
| Code skeleton and tests | [`src/campusevent/`](../src/campusevent/), [`tests/`](../tests/) |

---

## 2. Technology Decisions

| Concern | Decision | Reason |
|---|---|---|
| Backend language | **Python 3.12 only** | The skeleton and the 39 requirement tests are already in Python; one language keeps the five-person team on one code base. This closes finding F-06 of the analysis (the charter also listed Java). |
| Web framework | **Flask 3** with Blueprints and Jinja2 templates | Small, well documented, server-side rendering fits a form-based application and needs no separate frontend build. |
| Frontend | HTML, CSS, a small amount of JavaScript, **Bootstrap 5** | Matches the charter's frontend stack; Bootstrap's grid gives the responsive layout of NFR-01 without custom media queries. |
| Database | **PostgreSQL 16** with **SQLAlchemy 2** (ORM) and **Alembic** (migrations) | Transactions with row locks for booking and capacity rules; the E-R model of the analysis maps directly to tables. |
| Password hashing | **argon2-cffi** | Salted, memory-hard hashes for NFR-03. |
| Forms and CSRF | **Flask-WTF** | Server-side validation and CSRF tokens on every POST form. |
| E-mail | SMTP provider (e.g. Brevo free tier) behind the `EmailSender` interface | The services do not depend on a provider; tests use `InMemoryEmailSender`. |
| Tests | **pytest** (+ `pytest-cov`) | Already used for the requirement tests (NFR-06). |
| Code quality | **ruff** (lint and format) | One fast tool, runs locally and in CI. |
| CI/CD | **GitHub Actions** | Runs lint and tests on every pull request; deploys `main`. |
| Hosting | **Render** web service (gunicorn) + Render managed PostgreSQL | Free tier for a student project, automatic HTTPS certificate, secrets as environment variables. |

These choices can still be changed by the team before implementation starts on 16.11.2026; the layered design keeps such changes local (for example another host or e-mail provider only changes the infrastructure layer).

---

## 3. Architecture

### 3.1 Architectural style
CampusEvent uses a **layered architecture** (presentation → application → domain → data access → infrastructure). Each layer only calls the layer below it. This gives three benefits that matter for this project:

1. **Testability.** The services (application layer) do not know Flask or SQL. The requirement tests call them directly with in-memory repositories, so all 39 tests run in seconds without a database or browser.
2. **Parallel work.** Each team member owns one vertical slice (accounts, events, facilities, web UI, deployment) but works against stable service and repository interfaces.
3. **Replaceable infrastructure.** The database, the e-mail provider and the password hasher are behind interfaces (`*Repository`, `EmailSender`, `PasswordHasher`).

![Layered architecture](design/arch/layered_architecture.png)
*Files: [png](design/arch/layered_architecture.png), [svg](design/arch/layered_architecture.svg), [source](design/arch/layered_architecture.mmd)*

### 3.2 Components
| Layer | Component | Responsibility | Use cases |
|---|---|---|---|
| Presentation | `auth_routes` | Sign up, verification, log in, log out | UC-01, UC-02 |
| Presentation | `profile_routes` | My Profile page | UC-03 |
| Presentation | `event_routes` | Find events, event details, create, join, leave, cancel, My Activities | UC-04 to UC-07, UC-09 to UC-11 |
| Presentation | `facility_routes` | Facility management (staff only) | UC-07, UC-08 |
| Presentation | Security middleware | Session handling, CSRF, `login_required`, `role_required` decorators | all |
| Application | `AuthService` | Registration, e-mail verification, login, roles | UC-01, UC-02 |
| Application | `ProfileService` | Interests and availability | UC-03 |
| Application | `EventService` | Event life cycle and search, activity history | UC-04 to UC-06, UC-09 to UC-11 |
| Application | `FacilityService` | Facilities, blocks, schedules, conflict check | UC-07, UC-08 |
| Domain | `models.py`, `exceptions.py` | Entities, value objects, enums, domain errors | all |
| Data access | `Sql*Repository` | SQLAlchemy mapping, queries, row locks | all |
| Infrastructure | PostgreSQL, `PasswordHasher`, `SmtpEmailSender` | Storage, hashing, e-mail | all |

### 3.3 Deployment
![Deployment](design/arch/deployment.png)
*Files: [png](design/arch/deployment.png), [svg](design/arch/deployment.svg), [source](design/arch/deployment.mmd)*

Every push and pull request runs `ruff` and `pytest` in GitHub Actions. Only a green build on `main` triggers the Render deploy hook. Secrets (`SECRET_KEY`, `DATABASE_URL`, `SMTP_*`) exist only as environment variables on Render and as GitHub Actions secrets; they are never committed. `.env` is listed in `.gitignore`; the repository will only contain an `.env.example` with empty values.

### 3.4 Project structure
```
src/campusevent/
    models.py, exceptions.py           domain layer
    auth.py, profiles.py,
    events.py, facilities.py           application layer (services)
    notifications.py                   EmailSender interface + implementations
    repositories/                      repository interfaces, in-memory and SQL versions
    web/                               Flask app factory, blueprints, templates, static files
    app.py                             wires services and repositories (composition root)
migrations/                            Alembic migrations
tests/                                 requirement tests (pytest)
```

---

## 4. Class Design

### 4.1 Domain classes
The domain classes are the ones already in [`models.py`](../src/campusevent/models.py). `Event` gets two helper methods (`free_places`, `is_active`) that the services use for the capacity and conflict rules. All domain errors derive from `CampusEventError`, so the presentation layer can map them to user messages in one place.

![Domain class diagram](design/class/domain_classes.png)
*Files: [png](design/class/domain_classes.png), [svg](design/class/domain_classes.svg), [source](design/class/domain_classes.mmd)*

### 4.2 Services, repositories and infrastructure
The service classes keep the public methods of the skeleton (which the tests call). Their dependencies are passed in through the constructor (dependency injection); `create_app` in `app.py` is the only place that chooses the concrete classes. The tests use in-memory repositories and `InMemoryEmailSender`; production uses the SQL repositories and `SmtpEmailSender`.

![Service and data access class diagram](design/class/service_layer.png)
*Files: [png](design/class/service_layer.png), [svg](design/class/service_layer.svg), [source](design/class/service_layer.mmd)*

### 4.3 Design principles applied
| Principle | Where |
|---|---|
| Single responsibility | One service per business area; routes only translate HTTP to service calls |
| Dependency inversion | Services depend on `UserRepository`, `EventRepository`, `EmailSender`, `PasswordHasher` interfaces, not on SQLAlchemy or SMTP |
| Information expert | `TimeSlot.overlaps` decides overlaps; `Event.free_places` decides capacity |
| Fail fast | Services validate input and raise a domain error before any data is changed |

---

## 5. Object Interactions (Sequence Diagrams)

Six design-level sequence diagrams show the messages between the real classes. Together they cover **9 of 11 use cases (82 %)**; the remaining two (UC-03 manage profile, UC-09 activity history) are simple read/update flows already shown at analysis level in the Requirement Analysis Report, section 4.6.

| Diagram | Use cases |
|---|---|
| [Register and verify](design/sequence/uc01_register_and_verify.png) | UC-01 |
| [Log in](design/sequence/uc02_login.png) | UC-02 |
| [Create event with conflict check](design/sequence/uc04_uc07_create_event.png) | UC-04, UC-07 |
| [Browse, filter and join](design/sequence/uc05_uc06_browse_and_join.png) | UC-05, UC-06 |
| [Manage facility schedule](design/sequence/uc08_manage_facility_schedule.png) | UC-08 |
| [Leave and cancel](design/sequence/uc10_uc11_leave_and_cancel.png) | UC-10, UC-11 |

### 5.1 UC-01 Register and verify
![UC-01 sequence](design/sequence/uc01_register_and_verify.png)

### 5.2 UC-02 Log in
![UC-02 sequence](design/sequence/uc02_login.png)

### 5.3 UC-04 and UC-07 Create an event with conflict check
The facility row is locked (`SELECT … FOR UPDATE`) before the availability check, so two students cannot book the same slot at the same moment (risk R-01 of the analysis).

![UC-04 and UC-07 sequence](design/sequence/uc04_uc07_create_event.png)

### 5.4 UC-05 and UC-06 Browse, filter and join
The event row is locked while joining, so the number of participants never exceeds the capacity (BR-07).

![UC-05 and UC-06 sequence](design/sequence/uc05_uc06_browse_and_join.png)

### 5.5 UC-08 Manage facility schedule
![UC-08 sequence](design/sequence/uc08_manage_facility_schedule.png)

### 5.6 UC-10 and UC-11 Leave and cancel an event
![UC-10 and UC-11 sequence](design/sequence/uc10_uc11_leave_and_cancel.png)

---

## 6. Data Design

The tables follow the E-R diagram of the Requirement Analysis Report (section 3.1): `user`, `verification_code`, `profile_interest`, `availability_slot`, `facility`, `facility_block`, `event`, `event_participant`. Design additions:

| Table | Constraint or index | Purpose |
|---|---|---|
| `user` | `UNIQUE (lower(email))` | No duplicate accounts (UC-01) |
| `verification_code` | `code_hash`, `expires_at`, `used` | Codes are stored hashed and expire after 15 minutes |
| `event` | `CHECK (capacity >= 2)`, `CHECK (end_time > start_time)` | BR-04 |
| `event` | Index on `(category, start_time)` and on `(facility_id, start_time)` | Fast search (NFR-02) and fast conflict check (UC-07) |
| `event_participant` | Primary key `(event_id, user_id)` | A user joins an event once (BR-07) |
| `facility` | `CHECK (capacity >= 2)`, `UNIQUE (name)` | UC-08 |

Categories and interests are stored trimmed and in lower case (BR-14). All times are stored in UTC and shown in Europe/Istanbul. Schema changes are made only through Alembic migrations, which are reviewed in pull requests like any other code.

---

## 7. Design Decisions for the Non-Functional Requirements

| NFR | Requirement | Design decision | Tool | How it is checked |
|---|---|---|---|---|
| NFR-01 Usability | Responsive from 360 px to desktop | Mobile-first templates with the Bootstrap 5 grid; one column below 576 px; touch-sized buttons; same pages for all devices (no separate mobile app) | Bootstrap 5, Jinja2 base template | Manual check of every page at 360 px and desktop width in the browser developer tools; mockup 09 of the analysis is the reference |
| NFR-02 Performance | Event search < 2 s for 1,000 open events | Filtering in SQL, not in Python; indexes on `(category, start_time)` and `(facility_id, start_time)`; pagination of 20 events per page; no N+1 queries (participant counts loaded with one aggregate query) | PostgreSQL indexes, SQLAlchemy `selectinload` | `test_nfr02_search_is_fast_with_1000_open_events`; `EXPLAIN ANALYZE` on the search query before release |
| NFR-03 Security | Salted password hashes, HTTPS | Passwords hashed with argon2id (random salt per password); verification codes stored as hashes; HTTPS enforced by Render and `SESSION_COOKIE_SECURE=True`; `HttpOnly` and `SameSite=Lax` cookies; CSRF token on every form; secrets only in environment variables | argon2-cffi, Flask-WTF, Render TLS, GitHub secret scanning | `test_nfr03_*` (2 tests); HTTPS checked after deployment |
| NFR-04 Security | Role-based access | Two checks: `role_required` decorator on routes (returns 403) **and** `AuthService.require_role` inside the services, so a rule cannot be skipped by calling a service from another route; only the organizer can cancel (checked in `EventService`) | Flask decorators, domain exceptions | `test_nfr04_*` (3 tests) |
| NFR-05 Privacy | Only needed data shown, KVKK | Templates receive view models that contain no e-mail address; the participant list shows names only; availability is private (F-08); data minimization in the database (no phone, no student number) | Jinja2 view models | Manual review of event and participant pages |
| NFR-06 Maintainability | Tests for each use case, one command | Layered design with injected repositories makes services testable without a database; `python -m pytest` runs everything; CI blocks merging when tests or lint fail | pytest, ruff, GitHub Actions, branch protection on `main` | CI status on every pull request |
| NFR-07 Portability | Chrome, Firefox, Safari, Edge | Only standard HTML5, CSS and ES2020 JavaScript; Bootstrap 5 supports all four browsers; no browser plug-ins | Bootstrap 5 | Manual check of the main pages in each browser before release |

### 7.1 Concurrency (supports NFR-02 and the business rules)
Booking a facility (UC-04) and joining an event (UC-06) are the two places where simultaneous requests can break a rule. Both run in one database transaction with a row lock (`SELECT … FOR UPDATE`) on the facility or the event. The database constraints of section 6 are the last line of defence if application code has a bug.

### 7.2 Error handling
Services raise domain exceptions (`ValidationError`, `FacilityConflictError`, `EventFullError`, …). One Flask error handler maps them to the user messages written in the use cases and to HTTP status codes (400, 403, 404, 409). Unexpected errors are logged and the user sees a generic error page without technical details.

---

## 8. Decisions on Open Findings of the Analysis

| Finding | Decision in design |
|---|---|
| F-04 Free-text categories fragment the list | Categories are normalized (trim, lower case); the Create Event form suggests existing categories with an HTML `datalist` |
| F-05 Password reset is missing | Out of scope for the codebase deadline; documented as a future use case |
| F-06 Python and Java in the charter | Python only (section 2); the charter's technology stack was updated accordingly |
| F-07 Chat wording in the charter | Chat is out of scope; the charter's out-of-scope list was corrected |
| F-08 Public profile | Public profile shows name and interests only; availability stays private |
| F-09 Upcoming events | My Activities page gets an "Upcoming" tab next to "History" (same service, filter by status) |

---

## 9. Traceability: Use Case to Design Elements

| Use case | Route | Service method | Repository | Sequence |
|---|---|---|---|---|
| UC-01 | `auth_routes` `/signup`, `/verify` | `AuthService.register`, `verify_email` | `UserRepository` | 5.1 |
| UC-02 | `auth_routes` `/login` | `AuthService.login` | `UserRepository` | 5.2 |
| UC-03 | `profile_routes` `/profile` | `ProfileService.update_profile`, `get_profile` | `ProfileRepository` | analysis 4.6 |
| UC-04 | `event_routes` `/events` (POST) | `EventService.create_event` | `EventRepository`, `FacilityRepository` | 5.3 |
| UC-05 | `event_routes` `/events` (GET) | `EventService.search_events` | `EventRepository` | 5.4 |
| UC-06 | `event_routes` `/events/{id}/join` | `EventService.join_event` | `EventRepository` | 5.4 |
| UC-07 | `facility_routes`, used by UC-04 | `FacilityService.is_available`, `get_schedule` | `FacilityRepository`, `EventRepository` | 5.3 |
| UC-08 | `facility_routes` `/facilities` | `FacilityService.add_facility`, `add_block` | `FacilityRepository` | 5.5 |
| UC-09 | `event_routes` `/activities` | `EventService.get_activity_history` | `EventRepository` | analysis 4.6 |
| UC-10 | `event_routes` `/events/{id}/leave` | `EventService.leave_event` | `EventRepository` | 5.6 |
| UC-11 | `event_routes` `/events/{id}/cancel` | `EventService.cancel_event` | `EventRepository` | 5.6 |

---

## 10. Implementation Plan
The implementation follows the [project plan](plan/README.md): DB integration (3.1) starts on 16.11.2026, followed by the backend slices (3.2 accounts and profiles, 3.3 facilities, 3.4 events), the web UI (3.5, 3.6) and the CI/CD pipeline (3.7), which can start in parallel. High priority use cases (UC-01 to UC-07) are implemented first. A use case is done when its requirement tests pass in CI.
