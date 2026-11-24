@'

\# Events Coverage



Full-suite project coverage is tracked in \[docs/tests/coverage/README.md](README.md) (97%). When running only the Events unit/UC tests, module-level coverage is:



| File / Component | Coverage | Notes |

|---|---|---|

| src/campusevent/events.py | 96% (235 stmts, 11 miss, 60 branch, 2 partial) | Core Events service logic |

| src/campusevent/repositories/event\_repository.py (SqlEventRepository) | Covered via tests/db/test\_event\_repository.py in CI | Skipped locally without TEST\_DATABASE\_URL; runs in CI with PostgreSQL |



> Note: Running only the Events tests shows 44% over the subset of files touched by those tests; see \[docs/tests/coverage/README.md](README.md) for the full-suite 97% total.



\## Requirement -> Test -> Code Mapping

\- UC-04 (test\_uc04\_create\_event.py, test\_event\_service.py) -> EventService.create\_event

\- UC-05 (test\_uc05\_browse\_and\_filter\_events.py, test\_event\_service.py) -> EventService.search\_events

\- UC-06 (test\_uc06\_join\_event.py, test\_event\_service.py) -> EventService.join\_event

\- UC-09 (test\_uc09\_activity\_history.py, test\_event\_service.py) -> EventService.complete\_event, EventService.get\_activity\_history

\- UC-10 (test\_uc10\_leave\_event.py, test\_event\_service.py) -> EventService.leave\_event

\- UC-11 (test\_uc11\_cancel\_event.py, test\_event\_service.py) -> EventService.cancel\_event

\- UC-12 (test\_uc12\_review\_event\_requests.py, test\_event\_service.py) -> EventService.list\_pending\_events, approve\_event, reject\_event, expire\_pending\_requests, list\_my\_requests



\## Uncovered Lines in src/campusevent/events.py

\- Line 37: Real system clock fallback when an explicit clock is not injected.

\- Line 213 \& Lines 221-223: Rollback / error-handling paths after a failure during event or participation updates.

\- Line 326 \& Lines 330-332: Rollback / guard paths after an error during request review or expiration handling.

\- Lines 351-352: Race / conflict path when another request updates the same slot or record concurrently.

'@ | Set-Content -Encoding UTF8 docs\\tests\\coverage\\events.md

