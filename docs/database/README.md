# CampusEvent – Database

Owner: Heval Hüseyin Demir (task 3.1 DB Integration). Design: [Software Design Report §6 Data Design](../software_design_report.md#6-data-design), [E-R diagram](../requirement_analysis_report.md#31-e-r-diagram), [CR-01](../change_requests/CR-01_admin_event_approval.md).

PostgreSQL 16, SQLAlchemy 2 (ORM), psycopg 3 (driver), Alembic (migrations).

## What is where
| Path | Content |
|---|---|
| [`src/campusevent/repositories/db.py`](../../src/campusevent/repositories/db.py) | Connection: engine and sessions from `DATABASE_URL` (layer 3) |
| [`src/campusevent/repositories/tables.py`](../../src/campusevent/repositories/tables.py) | SQLAlchemy mappings of the 8 tables (`UserRow`, `EventRow`, ...) with all constraints |
| [`src/campusevent/repositories/unit_of_work.py`](../../src/campusevent/repositories/unit_of_work.py) | `UnitOfWork` interface, `SqlUnitOfWork` (production) and `InMemoryUnitOfWork` (tests) |
| [`alembic.ini`](../../alembic.ini), [`migrations/`](../../migrations/) | Alembic configuration and the migrations (`versions/`) |
| [`scripts/seed_db.py`](../../scripts/seed_db.py) | Demo data: 5 students, 1 facility staff member, 1 admin, 4 facilities, events in every status |
| [`tests/db/`](../../tests/db/) | Tests of the constraints against a real database (skipped without `TEST_DATABASE_URL`) |

The services never import these modules directly: the `Sql*Repository` classes of tasks 3.2–3.4 use them and return the domain objects of `models.py`.

## Set up the database on your computer
The commands are for Windows PowerShell; on macOS/Linux use `python3` and `source .venv/bin/activate`.

**1. Install PostgreSQL 16.** Remember the password of the `postgres` superuser you choose. If another PostgreSQL already uses port 5432, take 5433 and use that port below.
```powershell
winget install --id PostgreSQL.PostgreSQL.16 -e --interactive     # Windows
brew install postgresql@16; brew services start postgresql@16     # macOS
```
> **Windows in Turkish:** the installer stops with *"Failed to initialise the database cluster with initdb"* and the log (`%TEMP%\install-postgresql.log`) says `locale name "Turkish_Türkiye.1254" contains non-ASCII characters`. In the installer, choose **Locale: English, United States** instead of *[Default locale]* (Render uses an English locale too; Turkish text is still stored correctly because the encoding is UTF-8). If a failed install is left behind, remove it first with `winget uninstall --id PostgreSQL.PostgreSQL.16 -e`. Without the installer screens:
> ```powershell
> winget install --id PostgreSQL.PostgreSQL.16 -e --override "--mode unattended --superpassword CHOOSE-ONE --serverport 5432 --locale en-US --disable-components stackbuilder"
> ```

**2. Create a user and two databases** (one for development, one that the tests empty and rebuild):
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -p 5432
```
```sql
CREATE ROLE campusevent LOGIN PASSWORD 'choose-a-password';
CREATE DATABASE campusevent_dev OWNER campusevent;
CREATE DATABASE campusevent_test OWNER campusevent;
\q
```
Use only letters and digits in this password, so it can be written in a URL as it is.

**3. Put the connection strings in your local `.env`** (copy `.env.example`; `.env` is in `.gitignore` and is never committed):
```
DATABASE_URL=postgresql://campusevent:choose-a-password@localhost:5432/campusevent_dev
TEST_DATABASE_URL=postgresql://campusevent:choose-a-password@localhost:5432/campusevent_test
```

**4. Install the Python packages** into a virtual environment:
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
```
(If you activate it with `.venv\Scripts\Activate.ps1` and PowerShell says scripts are disabled, just keep writing `.venv\Scripts\python` in front of the commands.)

**5. Create the tables and load the demo data:**
```powershell
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python scripts\seed_db.py
```
`seed_db.py` prints the demo accounts and their password (`CAMPUSEVENT_DEMO_PASSWORD` in `.env`, or a random one). `--reset` deletes all rows first and loads the demo data again.

**6. Run the database tests:**
```powershell
.venv\Scripts\python -m pytest tests\db
```

## Look at the tables
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U campusevent -h localhost -p 5432 -d campusevent_dev
```
```sql
\dt                         -- list the tables
\d event                    -- columns, indexes and constraints of a table
SELECT id, title, status, start_time FROM event ORDER BY start_time;
SELECT id, email, role FROM "user";   -- user is a reserved word: always write "user" in quotes
```
DBeaver or DataGrip work too (host `localhost`, port, database `campusevent_dev`, user `campusevent`).

## Rules the database enforces
These are the last line of defence (Software Design Report §7.1); the services still check the rules first and raise domain errors with user-friendly messages.

| Rule | Constraint |
|---|---|
| One account per e-mail, case-insensitive (UC-01) | `ux_user_email_lower` (unique index on `lower(email)`) |
| Role is student, facility_staff or admin (CR-01) | `ck_user_role_valid` |
| New event is pending; status is one of the six states (BR-15) | default `'pending'`, `ck_event_status_valid` |
| Rejected event has a reason (BR-17, also the automatic rejection of BR-18) | `ck_event_rejected_has_reason` |
| No two active events (pending, open, full) in one facility at the same time (BR-06, BR-16) | `ex_event_facility_no_overlap` (EXCLUDE with `btree_gist`) |
| Blocks of one facility do not overlap (BR-10) | `ex_facility_block_no_overlap` |
| Capacity at least 2; end after start (BR-04, UC-03, UC-08) | `ck_*_capacity_min`, `ck_*_end_after_start` |
| Categories and interests are trimmed and lower case (BR-14) | `ck_event_category_normalized`, `ck_profile_interest_interest_normalized` |
| A user joins an event once (BR-07) | primary key of `event_participant` |

Time ranges are half-open `[start, end)`: an event ending at 18:00 and one starting at 18:00 do not overlap, like `TimeSlot.overlaps`. All times are `timestamptz` and the connection works in UTC.

**Rules that stay in the code** (a constraint can only see one row or one table):
- an event must not overlap a **facility block** → `FacilityService.check_bookable()` with the facility row locked (`SELECT … FOR UPDATE`);
- event capacity ≤ facility capacity, and participants ≤ event capacity (lock the event row before joining);
- the facility manager is facility staff, the reviewer is an admin, the e-mail domain is a university domain (BR-01).

## Writing a `Sql*Repository` (tasks 3.2–3.4)
Every SQL repository gets the **same scoped session** as `SqlUnitOfWork`, so all its calls between `uow.begin()` and `uow.commit()` are one transaction (Software Design Report 4.3, 7.1). It maps rows to the domain objects of `models.py`; the services never see a `*Row`.
```python
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, scoped_session

from campusevent.exceptions import FacilityConflictError, NotFoundError
from campusevent.models import Facility
from campusevent.repositories.tables import FacilityRow


class SqlFacilityRepository:
    def __init__(self, session: scoped_session[Session]) -> None:
        self.session = session

    def get_for_update(self, facility_id: int) -> Facility:
        row = self.session.get(FacilityRow, facility_id, with_for_update=True)  # SELECT ... FOR UPDATE
        if row is None:
            raise NotFoundError(f"Facility {facility_id} does not exist")
        return Facility(id=row.id, name=row.name, capacity=row.capacity)
```
- **Database errors → domain errors.** Call `self.session.flush()` right after `add()`, so a constraint error comes out inside the repository, and translate it by the constraint name (the names are in the table above), e.g. `ex_event_facility_no_overlap` → `FacilityConflictError`, `ux_user_email_lower` → `DuplicateEmailError`:
  ```python
  try:
      self.session.add(row)
      self.session.flush()
  except IntegrityError as error:
      if error.orig.diag.constraint_name == "ex_event_facility_no_overlap":
          raise FacilityConflictError("The facility is already booked at this time") from error
      raise
  ```
- **Times (team rule, agreed in #14).**
  - **Services and the domain use naive UTC.** That covers models, services, the requirement tests (`tests/helpers.slot`) and every `Sql*Repository` method.
  - **Repositories convert at the database.** They store `timestamptz` in UTC and turn every value they read back into naive UTC with `value.astimezone(timezone.utc).replace(tzinfo=None)`. See `_to_db` / `_from_db` in `facility_repository.py`.
  - **Only the web UI uses Istanbul time.** It converts form input with `common.to_utc` before a service call, and service output with `common.to_campus` before a page shows it.
  - **A `day` argument (`get_schedule`, `active_on`, `blocks_on`, …) means a UTC day.** The web UI asks for both UTC days of an Istanbul day.
- **Wiring** (composition root `app.py`, done in task 3.3): `create_app(database_url=...)` makes the engine and the scoped session once, and passes that session to `SqlUnitOfWork` and every `Sql*Repository`; the web app calls `CampusEventApp.end_request()` (`session.remove()`) after each request (`teardown_appcontext`). Only `create_app_from_env()` (used by `create_web_app()` in production) reads `DATABASE_URL`, so the requirement tests keep using the in-memory versions and `InMemoryUnitOfWork` even if your `.env` has a `DATABASE_URL`. **When you add a `Sql*Repository`** (for example `SqlEventRepository`, task 3.6), create it in the `if database_url:` block of `create_app` with the same `session` and pass it to its service.

## Changing the schema
Never change a table by hand and never edit a migration that is already on `main`. Instead:
1. Change the class in `tables.py`.
2. `.venv\Scripts\python -m alembic revision --autogenerate -m "short description"` writes a new file in `migrations/versions/`. Read it: autogenerate does not notice changed CHECK or EXCLUDE constraints, so add those by hand.
3. `.venv\Scripts\python -m alembic upgrade head`, then `pytest tests\db` (`test_tables_py_matches_the_migrations` fails if `tables.py` and the migrations differ).
4. Commit `tables.py` and the migration together in one pull request.

`alembic downgrade -1` undoes the last migration, `alembic current` shows the version of your database.

## Render (deployment, task 4.4)
- The managed PostgreSQL 16 database is defined in `render.yaml` (owner: Onur, see [docs/devops](../devops/README.md)); it gives the web service `DATABASE_URL` (`fromDatabase` → `connectionString`). `db.py` turns the `postgresql://` address into `postgresql+psycopg://` so SQLAlchemy uses psycopg 3.
- A new database is empty: run `alembic upgrade head` and then `scripts/seed_db.py` once. The free database is deleted after 30 days; after creating a new one, run the same two commands again.
- To run them from your own computer, put the *External Database URL* from the Render dashboard into `DATABASE_URL` for that one command only, not into a committed file.
- Suggestion for task 4.4: new migrations can run on every deploy by starting the web service with `alembic upgrade head && gunicorn ...` (useful if the plan has no pre-deploy command). `alembic upgrade head` does nothing when the database is already up to date.
