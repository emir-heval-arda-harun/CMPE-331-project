# UC-05: Browse and Filter Matches

| Field | Value |
|---|---|
| **ID** | UC-05 |
| **Primary actor** | Student |
| **Priority** | High |
| **Test** | [tests/test_uc05_browse_and_filter_matches.py](../../tests/test_uc05_browse_and_filter_matches.py) |

## Description
A student looks for matches to join, using filters for date, time, sport type and required skill level.

## Preconditions
- The student is logged in.

## Trigger
The student opens **Find a Match**.

## Main Success Scenario
1. The system lists upcoming open matches, ordered by start time.
2. The student applies one or more filters: sport, date, time range, skill level.
3. The system shows only the matches that satisfy **all** selected filters.
4. The student opens a match to see its details (facility, time, participants, free places).

## Alternative Flows
- **3a. No match satisfies the filters:** the system shows an empty list and suggests creating a match (UC-04).

## Postconditions
- None (read-only use case).
