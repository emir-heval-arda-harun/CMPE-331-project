# UC-04: Create Match

| Field | Value |
|---|---|
| **ID** | UC-04 |
| **Primary actor** | Student (organizer) |
| **Priority** | High |
| **Includes** | UC-11 (facility availability check) |
| **Test** | [tests/test_uc04_create_match.py](../../tests/test_uc04_create_match.py) |

## Description
A student organizes an amateur match at a campus facility so that other students can join.

## Preconditions
- The student is logged in.
- At least one facility is defined (UC-12).

## Trigger
The student selects **Create Match**.

## Main Success Scenario
1. The student selects the sport.
2. The system lists facilities that support this sport.
3. The student selects a facility, date, start and end time.
4. The student enters the number of players (capacity) and the required skill level.
5. The system checks that the facility is free in that time slot (UC-11).
6. The system creates the match with status **Open** and adds the organizer as the first participant.
7. The match becomes visible in the match list (UC-05).

## Alternative Flows
- **2a. No facility supports the sport:** the system informs the student; the match cannot be created.
- **4a. Capacity is less than 2:** the system rejects the input.
- **4b. Facility does not support the selected sport:** the system rejects the input.
- **5a. Facility is busy:** the system rejects the request and suggests free slots of the same day.

## Postconditions
- A new open match exists and is linked to the facility schedule.
