# UC-08: Manage Facility Schedule

| Field | Value |
|---|---|
| **ID** | UC-08 |
| **Primary actor** | Facility Staff |
| **Priority** | Medium |
| **Test** | [tests/test_uc08_manage_facility_schedule.py](../../tests/test_uc08_manage_facility_schedule.py) |

## Description
Campus facility personnel define facilities (halls, courts, pitches, meeting rooms) with their capacity and the times they are not available for student events (classes, maintenance, official events).

## Preconditions
- The user is logged in with the **Facility Staff** role (roles are assigned by an administrator or loaded as seed data; see assumption A-04 in the Requirements Specification).

## Trigger
The staff member opens **Facility Management**.

## Main Success Scenario
1. The staff member adds a facility with its name and capacity.
2. The staff member adds a blocked time slot with a reason.
3. The system stores the block and shows it in the facility schedule (UC-07).

## Alternative Flows
- **1a. User is not facility staff:** the system refuses the request.
- **1b. Capacity is less than 2:** the system rejects the input.
- **2a. Block overlaps an existing block of the same facility:** the system rejects the input.

## Postconditions
- Students cannot create events in blocked slots.

## Business Rules
- BR-09: Only facility staff manage facilities and blocks.
- BR-10: Blocks of one facility must not overlap each other.
