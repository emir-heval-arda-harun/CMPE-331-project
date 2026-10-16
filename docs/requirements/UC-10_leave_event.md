# UC-10: Leave Event

| Field | Value |
|---|---|
| **ID** | UC-10 |
| **Primary actor** | Student (participant) |
| **Priority** | Medium |
| **Test** | [tests/test_uc10_leave_event.py](../../tests/test_uc10_leave_event.py) |

## Description
A student who joined an event can leave it, so the place becomes free for another student.

## Preconditions
- The student is logged in.
- The student is a participant of an **Open** or **Full** event that has not started.

## Trigger
The student selects **Leave** on the event details page.

## Main Success Scenario
1. The system checks that the student is a participant of the event.
2. The system removes the student from the participant list.
3. If the event was **Full**, the system changes the status back to **Open**.
4. The system confirms that the student left the event.

## Alternative Flows
- **1a. Student is not a participant:** the system refuses the request.
- **1b. Student is the organizer:** the system refuses and offers **Cancel Event** (UC-11) instead.

## Postconditions
- The student is no longer a participant; the freed place is visible in the event list (UC-05).

## Business Rules
- BR-08: An event becomes **Open** again when a participant leaves a full event.
- BR-12: An organizer cannot leave their own event; the event has to be cancelled.
