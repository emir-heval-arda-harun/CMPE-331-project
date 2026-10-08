# UC-07: AI Skill-Based Team Balancing

| Field | Value |
|---|---|
| **ID** | UC-07 |
| **Primary actor** | Match organizer (Student) |
| **Secondary actors** | AI service (Gemini Pro) |
| **Priority** | Medium |
| **Test** | [tests/test_uc07_ai_team_balancing.py](../../tests/test_uc07_ai_team_balancing.py) |

## Description
When enough players have joined, the system splits them into teams with similar overall skill so that matches are fair and enjoyable.

## Preconditions
- The match has at least as many participants as teams × 2.
- Participants have profiles with skill levels (UC-03).

## Trigger
The organizer selects **Balance Teams**, or the match becomes full.

## Main Success Scenario
1. The system collects the profiles of all participants.
2. The system sends the profile data to the AI service.
3. The AI service returns a numeric skill rating for every player.
4. The system distributes players to teams so that total team ratings are as close as possible.
5. The system shows the teams to all participants.

## Alternative Flows
- **2a. AI service is unavailable or times out:** the system uses the self-declared skill levels from the profiles instead and continues from step 4.

## Postconditions
- Every participant is assigned to exactly one team.
- Teams have equal size (± 1 player).

## Business Rules
- BR-03: Only profile data needed for rating (sports, skill levels, match history) is sent to the AI service; no e-mail or name.
