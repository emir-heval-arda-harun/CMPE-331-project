# UC-07: View Facility Schedule and Check Conflicts

| Field | Value |
|---|---|
| **ID** | UC-07 |
| **Primary actor** | Student |
| **Secondary actors** | System |
| **Priority** | High |
| **Included by** | UC-04 |
| **Test** | [tests/test_uc07_facility_availability.py](../../tests/test_uc07_facility_availability.py) |

## Description
Students see when a campus facility is busy; the system prevents two events from using the same facility at the same time.

## Preconditions
- Facilities and their predefined schedules exist (UC-08).

## Trigger
The student opens a facility page, or an event is being created (UC-04).

## Main Success Scenario
1. The student selects a facility and a day.
2. The system shows all busy slots: staff blocks (UC-08) and scheduled events. Cancelled events (UC-11) do not occupy a slot.
3. When an event is being created, the system checks the requested slot against all busy slots.
4. If there is no overlap, the slot is reported as available.

## Alternative Flows
- **3a. Slot overlaps an existing event or block:** the system reports a conflict and the event is not created.

## Postconditions
- No two events share the same facility at the same time.

## Business Rules
- BR-06: A facility cannot be used by two active events, or by an event and a block, at the same time.
