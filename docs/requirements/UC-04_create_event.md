# UC-04: Create Event

| Field | Value |
|---|---|
| **ID** | UC-04 |
| **Primary actor** | Student (organizer) |
| **Priority** | High |
| **Includes** | UC-07 (facility availability check) |
| **Test** | [tests/test_uc04_create_event.py](../../tests/test_uc04_create_event.py) |

## Description
A student organizes an event at a campus facility so that other students can join. An event can be of any kind: a football match, a study group, a board game night, a club meeting, a photo walk, and so on. The category is free text.

## Preconditions
- The student is logged in.
- At least one facility is defined (UC-08).

## Trigger
The student selects **Create Event**.

## Main Success Scenario
1. The student enters the title, the category and an optional description.
2. The student selects a facility, date, start and end time.
3. The student enters the number of participants (capacity).
4. The system checks that the facility is free in that time slot (UC-07).
5. The system creates the event with status **Open** and adds the organizer as the first participant.
6. The event becomes visible in the event list (UC-05).

## Alternative Flows
- **1a. Title or category is empty:** the system rejects the input.
- **3a. Capacity is less than 2:** the system rejects the input.
- **3b. Capacity is larger than the capacity of the facility:** the system rejects the input and shows the facility capacity.
- **4a. Facility is busy:** the system rejects the request and suggests free slots of the same day.

## Postconditions
- A new open event exists and is linked to the facility schedule.

## Business Rules
- BR-04: Capacity is at least 2 (the organizer counts) and at most the capacity of the facility.
- BR-05: The organizer is the first participant.
- BR-14: Categories are free text; they are trimmed and compared without regard to upper or lower case.
