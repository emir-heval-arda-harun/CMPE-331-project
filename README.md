# CMPE-331-project – CampusEvent

A campus event platform for university students to organize, join and track events of any kind (sports, study groups, game nights, club meetings and more).

## Documents
- [Project Charter](docs/CHARTER.MD)
- [Project plan (WBS, Gantt & PERT)](docs/plan/README.md)
- [Use cases](docs/requirements/README.md)
- [Requirements Specification Report](docs/requirements_specification.md)
- [Software Design Report](docs/software_design_report.md) and [design models](docs/design/README.md)
- [UI/UX Design](docs/ui_ux_design.md): users, navigation, user flows, screens, design system, accessibility
- [Database: setup, migrations, demo data](docs/database/README.md)
- [Change requests](docs/change_requests/): [CR-01 Admin approval of event requests](docs/change_requests/CR-01_admin_event_approval.md)
- [Requirement Analysis Report](docs/requirement_analysis_report.md), [analysis models, BPD, DFD](docs/analysis/README.md) and [UI mockups](docs/analysis/ui/README.md)

## Run it on your computer
```bash
pip install -r requirements-dev.txt
python scripts/run_demo.py        # demo with in-memory data, then open http://localhost:5055
```
With a local PostgreSQL 16 and `DATABASE_URL` in `.env` (see [`.env.example`](.env.example) and the [database README](docs/database/README.md)), the app stores its data in the database. The live version runs on Render: [CI/CD and deployment](docs/devops/README.md).

## Tests
```bash
python -m pytest                  # all tests
python -m pytest tests/db         # database tests, need TEST_DATABASE_URL (otherwise skipped)
```
- `tests/test_uc*.py` and `tests/test_nfr.py` are the **requirement tests**: one file per use case, written before the code (test first). A use case whose backend is not merged yet still fails with `NotImplementedError`; this is expected until the backend task is done (see the [plan](docs/plan/README.md)).
- `tests/test_*_service.py` and `tests/test_auth_*.py` are unit tests of the services, `tests/db` tests the SQL repositories on PostgreSQL, `tests/web` tests the pages with the Flask test client.
- GitHub Actions runs `ruff` and `pytest` on every push and pull request.
- Software Testing Report sections: [`docs/testing`](docs/testing), coverage and non-functional tests: `docs/tests`.

## How we work
- **Branches:** `main` is protected and always holds the reviewed version. Every task gets its own branch from `main`, named `<type>/<topic>-<name>` (for example `feature/facilities-harun`, `docs/testing-accounts-heval`); `type` is `feature`, `fix` or `docs`.
- **Pull requests:** every change reaches `main` through a pull request with at least one approving review from a teammate, and is merged with a merge commit. The pull request names the task (WBS id) and the use cases.
- **Versions:** `main` is the current version. The final delivery of 30 Nov 2026 is tagged `v1.0.0`; later fixes would be `v1.0.x`.

## AI tools
The team uses Claude Code (Anthropic) beyond autocomplete: for drafting code and tests from the use cases, reviewing pull requests and writing report drafts. [`CLAUDE.md`](CLAUDE.md) holds the project rules the assistant has to follow. AI work stays traceable: commits written with the assistant have a `Co-Authored-By: Claude` line, and pull request texts end with "Generated with Claude Code". A team member reads, runs and reviews every change before it is merged.
