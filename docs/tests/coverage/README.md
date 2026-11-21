# Code Coverage

Owner: Onur Alioğlu (CI/CD). Part of the Software Testing Report (task 4.1) and review item D "Code coverage" (#34).

## How it is measured
- Tool: [pytest-cov](https://pytest-cov.readthedocs.io/) (coverage.py). The settings are in `pyproject.toml` under `[tool.coverage.*]`: only the application package `campusevent` is measured, with **branch coverage**, so both sides of an `if` count.
- **CI runs it on every push and every pull request** (`.github/workflows/ci.yml`, job *Tests (pytest)*):
  - CI starts a throwaway **PostgreSQL 16** service and sets `TEST_DATABASE_URL`, so the database tests in `tests/db` run too. Without a database they would be skipped, and the repository code would look less tested than it is.
  - The coverage table is shown on the run page (*Summary*, "Code coverage").
  - The build artifact `test-and-coverage-reports` holds `coverage.xml` (for tools such as SonarQube), the HTML report `htmlcov/` (open `htmlcov/index.html`; covered and missed lines are coloured) and the JUnit file `pytest-report.xml`.

## Run it locally
```bash
pip install -r requirements-dev.txt
python -m pytest --cov --cov-report=term --cov-report=html
```
Set `TEST_DATABASE_URL` in your `.env` to include the database tests (see `docs/database/README.md`). The HTML report is written to `htmlcov/`. It is in `.gitignore`, so it is never committed.

## Results (21.11.2026, `main` + this pull request)
Measured with the same command as CI, on a local PostgreSQL 16: **327 passed, 36 failed**. All 36 failures are `NotImplementedError` from `EventService`, because task 3.4 is not merged yet.

| Area | Line + branch coverage per file |
|---|---|
| Services | `auth.py` 96%, `profiles.py` 90%, `facilities.py` 100%, `events.py` 67% |
| Data access (`repositories/`) | `db.py` 79%, all others 96–100% |
| Web UI (`web/`) | 92–100% |
| **Total** (1567 statements, 238 branches) | **97%** |

Without the database (`tests/db` skipped), the total is **91%**. The repositories drop to 58–79% in that case, which is why CI runs a PostgreSQL service.

**How to read the numbers:**
- `events.py` (67%) is a skeleton: its methods only raise `NotImplementedError`. Its coverage will change when task 3.4 is merged, and CI will show the new value automatically.
- Coverage only shows which code ran during the tests. It does not show that the results were checked. That is what the requirement tests are for: each test file is named after its use case (`tests/test_uc01_...` to `test_uc12_...`).
- The traceability matrix (requirement → test → code) for the Testing Report builds on these per-file numbers.
