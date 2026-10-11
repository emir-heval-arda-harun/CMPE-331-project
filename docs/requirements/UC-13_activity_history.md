# UC-13: Track Activity History

| Field | Value |
|---|---|
| **ID** | UC-13 |
| **Primary actor** | Student |
| **Priority** | Low |
| **Test** | [tests/test_uc13_activity_history.py](../../tests/test_uc13_activity_history.py) |

## Description
A student sees the sports activities they have taken part in.

## Preconditions
- The student is logged in.

## Trigger
The student opens **My Activities**.

## Main Success Scenario
1. The system lists the completed matches in which the student was a participant, newest first.
2. Each entry shows the sport, date, time and facility.

## Alternative Flows
- **1a. The student has no completed matches:** the system shows an empty list. Upcoming matches are not shown in the history.

## Postconditions
- None (read-only use case).
