# UC-11: Cancel Event

| Field | Value |
|---|---|
| **ID** | UC-11 |
| **Primary actor** | Student (organizer) |
| **Priority** | Medium |
| **Test** | [tests/test_uc11_cancel_event.py](../../tests/test_uc11_cancel_event.py) |

## Description
The organizer cancels an event that will not take place. The facility slot becomes free again.

## Preconditions
- The student is logged in and is the organizer of the event.
- The event is **Open** or **Full** and has not started.

## Trigger
The organizer selects **Cancel Event** on the event details page.

## Main Success Scenario
1. The system checks that the user is the organizer of the event.
2. The system sets the event status to **Cancelled**.
3. The system releases the facility slot (UC-07).
4. The system removes the event from the event list (UC-05) and from the upcoming activities of all participants.

## Alternative Flows
- **1a. User is not the organizer:** the system refuses the request.
- **1b. Event is already completed or cancelled:** the system refuses the request.

## Postconditions
- The event has status **Cancelled**; its facility slot can be booked again.

## Business Rules
- BR-13: Only the organizer can cancel an event; a cancelled event never appears in the activity history and does not occupy its facility slot.
