# UC-15: Cancel Match

| Field | Value |
|---|---|
| **ID** | UC-15 |
| **Primary actor** | Student (organizer) |
| **Priority** | Medium |
| **Test** | [tests/test_uc15_cancel_match.py](../../tests/test_uc15_cancel_match.py) |

## Description
The organizer cancels a match that will not take place. The facility slot becomes free again.

## Preconditions
- The student is logged in and is the organizer of the match.
- The match is **Open** or **Full** and has not started.

## Trigger
The organizer selects **Cancel Match** on the match details page.

## Main Success Scenario
1. The system checks that the user is the organizer of the match.
2. The system sets the match status to **Cancelled**.
3. The system releases the facility slot (UC-11).
4. The system removes the match from the match list (UC-05) and from the upcoming activities of all participants.

## Alternative Flows
- **1a. User is not the organizer:** the system refuses the request.
- **1b. Match is already completed or cancelled:** the system refuses the request.

## Postconditions
- The match has status **Cancelled**; its facility slot can be booked again.

## Business Rules
- BR-15: A cancelled match never appears in the activity history (UC-13).
