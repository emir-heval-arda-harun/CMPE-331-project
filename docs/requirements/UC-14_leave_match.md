# UC-14: Leave Match

| Field | Value |
|---|---|
| **ID** | UC-14 |
| **Primary actor** | Student (participant) |
| **Priority** | Medium |
| **Test** | [tests/test_uc14_leave_match.py](../../tests/test_uc14_leave_match.py) |

## Description
A student who joined a match can leave it, so the place becomes free for another student.

## Preconditions
- The student is logged in.
- The student is a participant of an **Open** or **Full** match that has not started.

## Trigger
The student selects **Leave** on the match details page.

## Main Success Scenario
1. The system checks that the student is a participant of the match.
2. The system removes the student from the participant list (and from the team assignment, if teams were already balanced).
3. If the match was **Full**, the system changes the status back to **Open**.
4. The system confirms that the student left the match.

## Alternative Flows
- **1a. Student is not a participant:** the system refuses the request.
- **1b. Student is the organizer:** the system refuses and offers **Cancel Match** (UC-15) instead.

## Postconditions
- The student is no longer a participant; the freed place is visible in the match list (UC-05).

## Business Rules
- BR-14: An organizer cannot leave their own match; the match has to be cancelled.
