# CampusEvent – Database

Owner: Heval Hüseyin Demir (task 3.1 DB Integration). Design: [Software Design Report §6 Data Design](../software_design_report.md#6-data-design), [E-R diagram](../requirement_analysis_report.md#31-e-r-diagram), [CR-01](../change_requests/CR-01_admin_event_approval.md).

PostgreSQL 16, SQLAlchemy 2 (ORM), psycopg 3 (driver), Alembic (migrations).

## What is where
| Path | Content |
|---|---|
| [`src/campusevent/repositories/db.py`](../../src/campusevent/repositories/db.py) | Connection: engine and sessions from `DATABASE_URL` (layer 3) |
| [`src/campusevent/repositories/tables.py`](../../src/campusevent/repositories/tables.py) | SQLAlchemy mappings of the 8 tables (`UserRow`, `EventRow`, ...) with all constraints |
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

## Changing the schema
Never change a table by hand and never edit a migration that is already on `main`. Instead:
1. Change the class in `tables.py`.
2. `.venv\Scripts\python -m alembic revision --autogenerate -m "short description"` writes a new file in `migrations/versions/`. Read it: autogenerate does not notice changed CHECK or EXCLUDE constraints, so add those by hand.
3. `.venv\Scripts\python -m alembic upgrade head`, then `pytest tests\db` (`test_tables_py_matches_the_migrations` fails if `tables.py` and the migrations differ).
4. Commit `tables.py` and the migration together in one pull request.

`alembic downgrade -1` undoes the last migration, `alembic current` shows the version of your database.

## Render (deployment, task 4.4)
- `render.yaml` sets `DATABASE_URL` from the managed PostgreSQL 16 database. `db.py` turns the `postgresql://` address into `postgresql+psycopg://` so SQLAlchemy uses psycopg 3.
- A new database is empty: run `alembic upgrade head` and then `scripts/seed_db.py` once. The free database is deleted after 30 days; after creating a new one, run the same two commands again.
- To run them from your own computer, put the *External Database URL* from the Render dashboard into `DATABASE_URL` for that one command only, not into a committed file.
