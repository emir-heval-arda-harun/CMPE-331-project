# UC-10: Record Score and Advance Teams

| Field | Value |
|---|---|
| **ID** | UC-10 |
| **Primary actor** | Club Representative (tournament organizer) |
| **Priority** | Medium |
| **Test** | [tests/test_uc10_record_score.py](../../tests/test_uc10_record_score.py) |

## Description
After a tournament match is played, the organizer enters the score and the system moves the winner forward.

## Preconditions
- The bracket is generated (UC-09).
- Both teams of the match are known.

## Trigger
The organizer selects a bracket match and chooses **Enter Score**.

## Main Success Scenario
1. The organizer enters both scores.
2. The system stores the result and determines the winner.
3. The system places the winner into the correct slot of the next round.
4. If the match was the final, the system sets the tournament **champion**.

## Alternative Flows
- **1a. User is not the tournament organizer:** the system refuses.
- **2a. Scores are equal:** the system rejects the result, because elimination matches need a winner.

## Postconditions
- The bracket reflects the result.
