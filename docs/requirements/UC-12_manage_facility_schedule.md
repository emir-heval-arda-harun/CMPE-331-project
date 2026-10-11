# UC-12: Manage Facility Schedule

| Field | Value |
|---|---|
| **ID** | UC-12 |
| **Primary actor** | Facility Staff |
| **Priority** | Medium |
| **Test** | [tests/test_uc12_manage_facility_schedule.py](../../tests/test_uc12_manage_facility_schedule.py) |

## Description
Campus sports facility personnel define facilities and the times they are not available for student matches (classes, maintenance, official events).

## Preconditions
- The user is logged in with the **Facility Staff** role.

## Trigger
The staff member opens **Facility Management**.

## Main Success Scenario
1. The staff member adds a facility with its name and supported sports.
2. The staff member adds a blocked time slot with a reason.
3. The system stores the block and shows it in the facility schedule (UC-11).

## Alternative Flows
- **1a. User is not facility staff:** the system refuses the request.

## Postconditions
- Students cannot create matches in blocked slots.
