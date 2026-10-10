# UC-03: Manage Profile

| Field | Value |
|---|---|
| **ID** | UC-03 |
| **Primary actor** | Student |
| **Priority** | High |
| **Test** | [tests/test_uc03_manage_profile.py](../../tests/test_uc03_manage_profile.py) |

## Description
The student records preferred sports, a self-declared skill level per sport, and weekly availability. This data is used for filtering (UC-05) and AI team balancing (UC-07).

## Preconditions
- The student is logged in (UC-02).

## Trigger
The student opens **My Profile**.

## Main Success Scenario
1. The system shows the current profile.
2. The student selects one or more sports.
3. For each sport, the student chooses a skill level (Beginner, Intermediate, Advanced).
4. The student adds availability time slots.
5. The student saves the profile.
6. The system validates and stores the profile and shows it on the student's public page.

## Alternative Flows
- **6a. No sport selected:** the system rejects the change: "Select at least one sport."
- **6b. Invalid time slot (end before start):** the system rejects the slot.

## Postconditions
- The profile is updated and used by other features.
