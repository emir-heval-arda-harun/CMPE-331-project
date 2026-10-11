# UC-06: Join Match

| Field | Value |
|---|---|
| **ID** | UC-06 |
| **Primary actor** | Student |
| **Priority** | High |
| **Extends** | UC-05 |
| **Test** | [tests/test_uc06_join_match.py](../../tests/test_uc06_join_match.py) |

## Description
A student joins an open match that has free places.

## Preconditions
- The student is logged in.
- The match is open.

## Trigger
The student selects **Join** on the match details page.

## Main Success Scenario
1. The system checks that the match still has a free place.
2. The system checks that the student is not already a participant.
3. The system adds the student to the participant list.
4. If the capacity is reached, the system changes the match status to **Full**.
5. The system confirms the join to the student.

## Alternative Flows
- **1a. Match is full:** the system refuses and shows "This match is full."
- **2a. Student already joined:** the system refuses and shows "You have already joined this match."

## Postconditions
- The student is a participant; the match appears in the student's upcoming activities.
