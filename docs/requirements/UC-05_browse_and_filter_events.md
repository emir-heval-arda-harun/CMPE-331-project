# UC-05: Browse and Filter Events

| Field | Value |
|---|---|
| **ID** | UC-05 |
| **Primary actor** | Student |
| **Priority** | High |
| **Test** | [tests/test_uc05_browse_and_filter_events.py](../../tests/test_uc05_browse_and_filter_events.py) |

## Description
A student looks for events to join, using filters for category, date, time and a keyword in the title.

## Preconditions
- The student is logged in.

## Trigger
The student opens **Find an Event**.

## Main Success Scenario
1. The system lists upcoming open events, ordered by start time.
2. The student applies one or more filters: category, date, time range, keyword.
3. The system shows only the events that satisfy **all** selected filters.
4. The student opens an event to see its details (title, description, facility, time, participants, free places).

## Alternative Flows
- **3a. No event satisfies the filters:** the system shows an empty list and suggests creating an event (UC-04).

## Postconditions
- None (read-only use case).

## Business Rules
- BR-14: Categories are free text; they are trimmed and compared without regard to upper or lower case.
