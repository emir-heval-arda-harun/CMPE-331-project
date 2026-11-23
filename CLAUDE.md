# CLAUDE.md – project rules for AI assistants

CampusEvent, CMPE 331 team project: a Flask web app where students create, find and join campus events, facility staff manage facilities and admins approve event requests. Read [README.md](README.md) first; the requirements are in `docs/requirements`, the design in `docs/software_design_report.md`.

## Commands
```bash
pip install -r requirements-dev.txt
python -m pytest                     # all tests; requirement tests of unfinished use cases fail with NotImplementedError
python -m pytest tests/db            # needs TEST_DATABASE_URL (local PostgreSQL 16), otherwise skipped
ruff check .                         # must be clean, CI runs it
python scripts/run_demo.py           # demo with in-memory data on http://localhost:5055
python -m pytest --cov               # coverage with branches; settings in pyproject.toml (pytest-cov, #36)
```
Measure the whole package (`--cov` alone, as CI does) or a path (`--cov=src/campusevent`). Do **not** pass a dotted module such as `--cov=campusevent.facilities`: then the database tests fail inside SQLAlchemy with `TypeError: 'InternalTraversal' object is not callable`.

## Architecture (Software Design Report, section 3)
- Layers: web (`src/campusevent/web`) → services (`auth.py`, `profiles.py`, `events.py`, `facilities.py`) → repositories (`src/campusevent/repositories`) → PostgreSQL. A layer calls only the layer directly below it.
- Services depend on `Protocol` interfaces (`*Repository`, `UnitOfWork`, `PasswordHasher`, `EmailSender`), never on Flask, SQLAlchemy or SMTP.
- Only `create_app` in `app.py` picks the `Sql*` classes (when a database URL is given); without one the services use their `InMemory*` defaults.
- Transactions: the service calls `uow.begin()`, `commit()` or `rollback()`. A repository never commits or rolls back by itself; it translates known constraint errors into domain errors and re-raises the rest.
- Facility booking: call `FacilityService.check_bookable` **after** `uow.begin()`, so the facility row lock is part of the same transaction.
- Follow "Writing a Sql*Repository" in `docs/database/README.md` for new SQL repositories.

## Rules that are easy to get wrong
- **Time:** services and the database use naive UTC; only the web layer converts to and from Istanbul time.
- **Roles:** wrong role or not the owner → `PermissionDeniedError` (NFR-04); wrong input → `ValidationError`.
- **Forms:** every POST form has the CSRF token (`{{ csrf() }}` from `_macros.html`). Web tests turn CSRF off with `WTF_CSRF_ENABLED: False`.
- **Privacy:** pages never show another user's e-mail address (NFR-05).
- **Secrets:** never commit `.env`, passwords, keys or database URLs. Only `.env.example` with empty values is in the repository.
- **Tests:** every new rule gets a test that names its use case or business rule (UC-xx, BR-xx, NFR-xx). Write or update the test before the code where possible, and keep the requirement tests unchanged unless the requirement changes.

## Workflow
- Branch from `main` as `<type>/<topic>-<name>` (`feature`, `fix`, `docs`). Never push to `main`; open a pull request, at least one teammate approves, merge with a merge commit.
- Commits made with the assistant end with `Co-Authored-By: Claude …`; pull request texts end with the "Generated with Claude Code" line. For a commit uploaded through the GitHub web page, say in the pull request which part the assistant made.
- Documentation and code comments are in plain English; reports are Markdown files under `docs/`, diagrams Mermaid or PlantUML.
- A team member reads and runs every AI-written change before asking for review. If the assistant was wrong in a way that mattered, note it in the pull request so it can go into the AI section of the reports.
