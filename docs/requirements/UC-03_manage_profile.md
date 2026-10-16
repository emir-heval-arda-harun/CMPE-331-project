# UC-03: Manage Profile

| Field | Value |
|---|---|
| **ID** | UC-03 |
| **Primary actor** | Student |
| **Priority** | High |
| **Test** | [tests/test_uc03_manage_profile.py](../../tests/test_uc03_manage_profile.py) |

## Description
The student records interests (free-text event categories such as "football", "study group" or "board games") and weekly availability. This data is shown on the student's page and is used to pre-fill the filters of UC-05.

## Preconditions
- The student is logged in (UC-02).

## Trigger
The student opens **My Profile**.

## Main Success Scenario
1. The system shows the current profile.
2. The student adds one or more interests.
3. The student adds availability time slots.
4. The student saves the profile.
5. The system validates and stores the profile.

## Alternative Flows
- **5a. No interest entered:** the system rejects the change: "Add at least one interest."
- **5b. Invalid time slot (end before start):** the system rejects the slot.

## Postconditions
- The profile is updated.

## Business Rules
- BR-14: Categories are free text; they are trimmed and compared without regard to upper or lower case.
