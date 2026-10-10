# UC-08: Create Tournament

| Field | Value |
|---|---|
| **ID** | UC-08 |
| **Primary actor** | Club Representative |
| **Priority** | Medium |
| **Test** | [tests/test_uc08_create_tournament.py](../../tests/test_uc08_create_tournament.py) |

## Description
A student club organizes a structured campus-wide tournament.

## Preconditions
- The user is logged in with the **Club Representative** role.

## Trigger
The representative selects **New Tournament**.

## Main Success Scenario
1. The representative enters the tournament name and sport.
2. The representative enters the participating team names.
3. The system validates the data.
4. The system creates the tournament and shows its page.

## Alternative Flows
- **1a. User is not a club representative:** the system hides the option / refuses the request.
- **3a. Fewer than two teams or duplicate team names:** the system rejects the input.

## Postconditions
- A tournament exists and is ready for bracket generation (UC-09).
