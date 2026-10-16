# UC-09: Track Activity History

| Field | Value |
|---|---|
| **ID** | UC-09 |
| **Primary actor** | Student |
| **Priority** | Low |
| **Test** | [tests/test_uc09_activity_history.py](../../tests/test_uc09_activity_history.py) |

## Description
A student sees the events they have taken part in.

## Preconditions
- The student is logged in.

## Trigger
The student opens **My Activities**.

## Main Success Scenario
1. The system lists the completed events in which the student was a participant, newest first.
2. Each entry shows the title, category, date, time and facility.

## Alternative Flows
- **1a. The student has no completed events:** the system shows an empty list. Upcoming and cancelled events (UC-11) are not shown in the history.

## Postconditions
- None (read-only use case).

## Business Rules
- BR-11: The history shows only completed events, newest first.
- BR-13: A cancelled event never appears in the history.
