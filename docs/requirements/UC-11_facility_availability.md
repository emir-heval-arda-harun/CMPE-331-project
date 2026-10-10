# UC-11: View Facility Schedule and Check Conflicts

| Field | Value |
|---|---|
| **ID** | UC-11 |
| **Primary actor** | Student |
| **Secondary actors** | System |
| **Priority** | High |
| **Included by** | UC-04 |
| **Test** | [tests/test_uc11_facility_availability.py](../../tests/test_uc11_facility_availability.py) |

## Description
Students see when a campus facility is busy; the system prevents two activities from using the same facility at the same time.

## Preconditions
- Facilities and their predefined schedules exist (UC-12).

## Trigger
The student opens a facility page, or a match is being created (UC-04).

## Main Success Scenario
1. The student selects a facility and a day.
2. The system shows all busy slots: staff blocks (UC-12) and scheduled matches.
3. When a match is being created, the system checks the requested slot against all busy slots.
4. If there is no overlap, the slot is reported as available.

## Alternative Flows
- **3a. Slot overlaps an existing match or block:** the system reports a conflict and the match is not created.

## Postconditions
- No two activities share the same facility at the same time.
