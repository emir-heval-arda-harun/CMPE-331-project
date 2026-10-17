# UC-06: Join Event

| Field | Value |
|---|---|
| **ID** | UC-06 |
| **Primary actor** | Student |
| **Priority** | High |
| **Extends** | UC-05 |
| **Test** | [tests/test_uc06_join_event.py](../../tests/test_uc06_join_event.py) |

## Description
A student joins an open event that has free places.

## Preconditions
- The student is logged in.
- The event is open.

## Trigger
The student selects **Join** on the event details page.

## Main Success Scenario
1. The system checks that the event still has a free place.
2. The system checks that the student is not already a participant.
3. The system adds the student to the participant list.
4. If the capacity is reached, the system changes the event status to **Full**.
5. The system confirms the join to the student.

## Alternative Flows
- **1a. Event is full:** the system refuses and shows "This event is full."
- **2a. Student already joined:** the system refuses and shows "You have already joined this event."

## Postconditions
- The student is a participant; the event appears in the student's upcoming activities.

## Business Rules
- BR-07: A student can join an event only once and the participants never exceed the capacity.
- BR-08: An event becomes **Full** when the capacity is reached and **Open** again when a participant leaves (UC-10).
