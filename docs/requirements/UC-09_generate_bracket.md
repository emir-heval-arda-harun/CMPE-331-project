# UC-09: Generate Tournament Bracket

| Field | Value |
|---|---|
| **ID** | UC-09 |
| **Primary actor** | Club Representative |
| **Secondary actors** | System (bracket generator) |
| **Priority** | Medium |
| **Test** | [tests/test_uc09_generate_bracket.py](../../tests/test_uc09_generate_bracket.py) |

## Description
The system automatically creates a single-elimination bracket for a tournament.

## Preconditions
- The tournament exists (UC-08) and has at least two teams.

## Trigger
The representative selects **Generate Bracket**.

## Main Success Scenario
1. The system calculates the number of rounds (log₂ of the next power of two ≥ team count).
2. The system pairs the teams for the first round.
3. The system creates empty matches for the later rounds.
4. The system shows the bracket.

## Alternative Flows
- **2a. Team count is not a power of two:** some teams get a **bye** and automatically advance to round 2.

## Postconditions
- Every team appears exactly once in round 1 (as a player or with a bye).
