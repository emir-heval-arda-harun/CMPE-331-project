# CampusEvent – Requirement Analysis Report

**Course:** CMPE 331 – Software Engineering
**Group:** 14
**Team:** Heval Hüseyin Demir, Emre Arda Kum, Emir Gül, Harun Gündaş, Onur Alioğlu
**Repository:** https://github.com/emir-heval-arda-harun/CMPE-331-project
**Version:** 1.0 – 12.10.2026 (deadline 18.10.2026 23:59)

---

## 1. Introduction

### 1.1 Purpose
The [Requirements Specification](requirements_specification.md) states **what** CampusEvent must do in 13 use cases (UC-01 to UC-13). This report **analyzes** those requirements. It builds the conceptual and data models, shows how the system behaves in the important scenarios, collects the business rules, and lists the gaps and risks found in the requirements. The Software Design Report will take these results as its input.

### 1.2 Method
Each use case was read together with the domain classes in [`src/campusevent/models.py`](../src/campusevent/models.py). From them we derived:

1. a conceptual class model (section 2),
2. a data model with an E-R diagram and data dictionary (section 3),
3. sequence and state diagrams for the critical behavior (section 4),
4. a consolidated list of business rules (section 5),
5. open issues and risks with decisions (sections 6 and 7).

Items marked **(proposed)** are not in the Requirements Specification yet. They are analysis proposals that will be added to the use cases during design.

### 1.3 Inputs
| Document | Location |
|---|---|
| Project Charter | [CHARTER.MD](CHARTER.MD) |
| Requirements Specification | [requirements_specification.md](requirements_specification.md) |
| Use cases UC-01 … UC-13 | [requirements/](requirements/README.md) |
| Domain classes | [`src/campusevent/models.py`](../src/campusevent/models.py) |

---

## 2. Conceptual Model

### 2.1 Actors and use-case relations
| Actor | Use cases |
|---|---|
| Student | UC-01, 02, 03, 04, 05, 06, 07 (as organizer), 11, 13 |
| Club Representative | UC-02, 08, 09, 10 |
| Facility Staff | UC-02, 12 |
| Gemini Pro (external) | UC-07 |
| E-mail service (external) | UC-01 |

Relations between use cases: UC-04 **includes** UC-11 (facility check). UC-06 **extends** UC-05 (join from the match list). UC-09 needs the tournament from UC-08, and UC-10 needs the bracket from UC-09.

### 2.2 Domain class model
The model below comes from `models.py` and is extended with the relations the use cases imply.

```mermaid
classDiagram
    class User {
        +int id
        +string email
        +string fullName
        +Role role
        +bool isVerified
    }
    class Profile {
        +int userId
        +map sports
    }
    class TimeSlot {
        +datetime start
        +datetime end
        +overlaps(other) bool
    }
    class Facility {
        +int id
        +string name
        +list sports
    }
    class FacilityBlock {
        +string reason
    }
    class Match {
        +int id
        +string sport
        +int capacity
        +SkillLevel skillLevel
        +MatchStatus status
    }
    class Tournament {
        +int id
        +string name
        +string sport
        +string champion
    }
    class BracketMatch {
        +int id
        +int roundNumber
        +int scoreA
        +int scoreB
        +string winner
    }
    class ActivityRecord {
        +int matchId
        +string sport
    }
    class Role {
        <<enumeration>>
        STUDENT
        CLUB_REPRESENTATIVE
        FACILITY_STAFF
    }
    class SkillLevel {
        <<enumeration>>
        BEGINNER
        INTERMEDIATE
        ADVANCED
    }
    class MatchStatus {
        <<enumeration>>
        OPEN
        FULL
        COMPLETED
        CANCELLED
    }

    User "1" --> "0..1" Profile : has
    User --> Role
    Profile --> SkillLevel : skill per sport
    Profile "1" o-- "*" TimeSlot : availability
    User "1" --> "*" Match : organizes
    Match "*" --> "*" User : participants
    Match --> TimeSlot
    Match "*" --> "1" Facility : played at
    Match --> MatchStatus
    Facility "1" o-- "*" FacilityBlock : blocked periods
    FacilityBlock --> TimeSlot
    User "1" --> "*" Tournament : organizes
    Tournament "1" *-- "*" BracketMatch : bracket
    User "1" --> "*" ActivityRecord : history
```

### 2.3 Glossary of analysis terms
| Term | Meaning |
|---|---|
| Busy slot | A time slot of a facility that is blocked by staff or already used by a match |
| Free place | `capacity` minus the number of participants of a match |
| Round | A level of the single-elimination bracket; round 1 is the first |
| Bye | A free pass to round 2 for a team without an opponent in round 1 |
| Team rating | The sum of the numeric skill ratings of the players in a team |

---

## 3. Data Analysis

### 3.1 E-R diagram
The class model keeps sports and teams as plain strings. For a database this is not enough: sports must be shared by profiles, facilities, matches and tournaments, and tournament teams need their own identity so that bracket games can reference them. The E-R diagram therefore adds `SPORT`, `TEAM` and link tables **(proposed)**.

```mermaid
erDiagram
    USER ||--o{ VERIFICATION_CODE : receives
    USER ||--o{ PROFILE_SPORT : declares
    SPORT ||--o{ PROFILE_SPORT : "rated in"
    USER ||--o{ AVAILABILITY_SLOT : offers
    USER ||--o{ MATCH : organizes
    USER ||--o{ MATCH_PARTICIPANT : joins
    MATCH ||--o{ MATCH_PARTICIPANT : has
    SPORT ||--o{ MATCH : "played in"
    FACILITY ||--o{ MATCH : hosts
    FACILITY ||--o{ FACILITY_SPORT : supports
    SPORT ||--o{ FACILITY_SPORT : "supported by"
    FACILITY ||--o{ FACILITY_BLOCK : "closed by"
    USER ||--o{ TOURNAMENT : organizes
    SPORT ||--o{ TOURNAMENT : "played in"
    TOURNAMENT ||--o{ TEAM : registers
    TOURNAMENT ||--o{ BRACKET_MATCH : contains
    TEAM ||--o{ BRACKET_MATCH : plays

    USER {
        int id PK
        string email UK
        string full_name
        string password_hash
        string role
        bool is_verified
    }
    VERIFICATION_CODE {
        int id PK
        int user_id FK
        string code_hash
        datetime expires_at
        bool used
    }
    SPORT {
        int id PK
        string name UK
    }
    PROFILE_SPORT {
        int user_id PK
        int sport_id PK
        int skill_level
    }
    AVAILABILITY_SLOT {
        int id PK
        int user_id FK
        datetime start_time
        datetime end_time
    }
    FACILITY {
        int id PK
        string name UK
    }
    FACILITY_SPORT {
        int facility_id PK
        int sport_id PK
    }
    FACILITY_BLOCK {
        int id PK
        int facility_id FK
        datetime start_time
        datetime end_time
        string reason
    }
    MATCH {
        int id PK
        int organizer_id FK
        int sport_id FK
        int facility_id FK
        datetime start_time
        datetime end_time
        int capacity
        int skill_level
        string status
    }
    MATCH_PARTICIPANT {
        int match_id PK
        int user_id PK
        int team_no
        datetime joined_at
    }
    TOURNAMENT {
        int id PK
        int organizer_id FK
        int sport_id FK
        string name
        int champion_team_id FK
    }
    TEAM {
        int id PK
        int tournament_id FK
        string name
    }
    BRACKET_MATCH {
        int id PK
        int tournament_id FK
        int round_number
        int position
        int team_a_id FK
        int team_b_id FK
        int score_a
        int score_b
        int winner_team_id FK
        int next_match_id FK
    }
```

### 3.2 Data dictionary (main constraints)
| Entity | Constraint | Source |
|---|---|---|
| USER | `email` unique; domain must be `bilgiedu.net` or `bilgi.edu.tr`; `password_hash` is never plain text | UC-01, BR-01, BR-02 |
| USER | `role` is one of student, club_representative, facility_staff | `Role` enum |
| PROFILE_SPORT | One row per user and sport; `skill_level` is 1 to 3; a profile needs at least one row | UC-03 |
| AVAILABILITY_SLOT | `end_time` is after `start_time` | UC-03 alt. 6b |
| FACILITY_SPORT | A facility supports at least one sport | UC-12 |
| FACILITY_BLOCK | `end_time` is after `start_time`; blocks of one facility must not overlap each other | UC-11, 12 |
| MATCH | `capacity` is at least 2; the facility must support the sport; the time slot must not overlap any block or other match of the same facility | UC-04, UC-11 |
| MATCH | `status` is one of open, full, completed, cancelled | `MatchStatus` enum |
| MATCH_PARTICIPANT | A user can join a match only once (composite key); number of rows is at most `capacity` | UC-06 |
| MATCH_PARTICIPANT | `team_no` is set by UC-07; team sizes differ by at most 1 | UC-07 |
| TOURNAMENT | At least 2 teams before a bracket can be generated | UC-08, UC-09 |
| TEAM | Team name unique inside a tournament | UC-08 alt. 3a |
| BRACKET_MATCH | `round_number` and `position` unique per tournament; `score_a` and `score_b` must differ; `winner_team_id` is one of the two teams | UC-09, UC-10 |

### 3.3 Design notes for the database
- **Integrity of facility use.** The rule "no two activities share a facility at the same time" cannot be guaranteed by application code alone, because two students can book at the same moment. The database should enforce it (for example with a transaction and a row lock on the facility, or an exclusion constraint on the time range if the chosen database supports it).
- **Capacity.** Joining a match must count participants and insert the new row in one transaction. Otherwise two simultaneous joins can exceed `capacity`.
- **Bracket tree.** `next_match_id` links a game to the game where its winner continues. Advancing a winner (UC-10 step 3) is then one update, and the final game has `next_match_id` empty.
- **Normal form.** All tables are in 3NF: link tables hold only key attributes and facts about the pair, and sports are stored once.
- **Time zone.** All times are stored in UTC and shown in Europe/Istanbul **(proposed)**.

---

## 4. Behavior Analysis

### 4.1 Sequence: register and verify (UC-01)
```mermaid
sequenceDiagram
    actor S as Student
    participant W as Web app
    participant A as Auth service
    participant D as Database
    participant M as E-mail service

    S->>W: Enter name, e-mail, password
    W->>A: register(name, email, password)
    A->>A: Check university domain (BR-01)
    A->>D: Find user by e-mail
    D-->>A: none
    A->>D: Save unverified user with password hash
    A->>M: Send one-time code
    A-->>W: Registration pending
    S->>W: Enter code
    W->>A: verify(email, code)
    A->>D: Check code and expiry
    A->>D: Set is_verified = true
    A-->>W: Account verified
    W-->>S: Continue to profile setup (UC-03)
```

### 4.2 Sequence: create a match with conflict check (UC-04 and UC-11)
```mermaid
sequenceDiagram
    actor S as Student
    participant W as Web app
    participant MS as Match service
    participant FS as Facility service
    participant D as Database

    S->>W: Sport, facility, date, time, capacity, skill level
    W->>MS: createMatch(request)
    MS->>MS: Validate capacity at least 2
    MS->>FS: isAvailable(facility, slot)
    FS->>D: Read blocks and matches of the facility
    D-->>FS: busy slots
    alt Slot overlaps a busy slot
        FS-->>MS: conflict
        MS-->>W: Rejected, free slots of the day suggested
        W-->>S: Show conflict and free slots
    else Slot is free
        FS-->>MS: available
        MS->>D: Insert match with status open
        MS->>D: Insert organizer as first participant
        MS-->>W: Match created
        W-->>S: Show match in the list
    end
```
Analysis note: the availability check and the insert must run in **one transaction**; otherwise two students can both pass the check for the same slot.

### 4.3 Sequence: AI team balancing with fallback (UC-07)
```mermaid
sequenceDiagram
    actor O as Organizer
    participant MM as Matchmaking service
    participant D as Database
    participant G as Gemini Pro

    O->>MM: balanceTeams(match)
    MM->>D: Read participant profiles
    MM->>MM: Remove name and e-mail (BR-03)
    MM->>G: Rate players
    alt AI answers in time
        G-->>MM: Numeric rating per player
    else AI unavailable or timeout
        MM->>MM: Use declared skill levels 1 to 3
    end
    MM->>MM: Distribute players so team ratings are close
    MM->>D: Save team_no for every participant
    MM-->>O: Teams shown to all participants
```
Analysis note: NFR-03 allows 10 seconds including the AI call. The timeout for the AI call must therefore be shorter (about 5 seconds is proposed) so that the fallback still fits in the limit.

### 4.4 Sequence: record a score and advance the winner (UC-10)
```mermaid
sequenceDiagram
    actor R as Club Representative
    participant TS as Tournament service
    participant D as Database

    R->>TS: recordScore(bracketMatch, scoreA, scoreB)
    TS->>D: Load match and tournament
    TS->>TS: Check user is the tournament organizer
    TS->>TS: Check scores are different
    TS->>D: Save scores and winner
    alt Game has a next game
        TS->>D: Put winner into next game slot
    else Game was the final
        TS->>D: Set tournament champion
    end
    TS-->>R: Updated bracket
```

### 4.5 State diagrams

**Match** (UC-04, UC-06, UC-13). Transitions marked *(proposed)* have no use case yet; the use cases for them were decided in F-01.
```mermaid
stateDiagram-v2
    [*] --> Open : UC-04 match created
    Open --> Full : UC-06 capacity reached
    Full --> Open : participant leaves
    Open --> Cancelled : organizer cancels
    Full --> Cancelled : organizer cancels
    Open --> Completed : end time passed
    Full --> Completed : end time passed
    Completed --> [*]
    Cancelled --> [*]
```

**User account** (UC-01, UC-02).
```mermaid
stateDiagram-v2
    [*] --> Unverified : sign up
    Unverified --> Unverified : wrong code or new code requested
    Unverified --> Verified : correct code
    Verified --> [*]
```
Only verified accounts can log in (UC-02 step 3).

**Tournament** (UC-08, UC-09, UC-10).
```mermaid
stateDiagram-v2
    [*] --> Created : UC-08
    Created --> BracketReady : UC-09 bracket generated
    BracketReady --> InProgress : first score recorded
    InProgress --> InProgress : score recorded, winner advances
    InProgress --> Finished : final recorded, champion set
    Finished --> [*]
```

---

## 5. Business Rules

| ID | Rule | Source |
|---|---|---|
| BR-01 | Only university e-mail domains are accepted | UC-01 |
| BR-02 | Passwords are never stored in plain text | UC-01 |
| BR-03 | Only data needed for rating is sent to the AI service; no name or e-mail | UC-07 |
| BR-04 | Only verified users can log in **(derived)** | UC-02 |
| BR-05 | A match needs capacity of at least 2 **(derived)** | UC-04 |
| BR-06 | No two matches or blocks may use the same facility at the same time **(derived)** | UC-11 |
| BR-07 | A user joins a match at most once, and never above capacity **(derived)** | UC-06 |
| BR-08 | Only club representatives create tournaments and enter scores **(derived)** | UC-08, 10 |
| BR-09 | Only facility staff manage facilities and blocks **(derived)** | UC-12 |
| BR-10 | An elimination game needs a winner: equal scores are rejected **(derived)** | UC-10 |
| BR-11 | Every team appears exactly once in round 1, as a player or with a bye **(derived)** | UC-09 |
| BR-12 | Every participant belongs to exactly one team after balancing; sizes differ by at most 1 **(derived)** | UC-07 |
| BR-13 | The history shows only completed matches, newest first **(derived)** | UC-13 |

---

## 6. Analysis Findings: Gaps and Proposed Decisions

Reading the use cases against each other showed the following gaps. Each has a decision. The team accepted the proposed decisions for F-01 to F-05 on 12.10.2026; F-06 to F-10 will be decided during design.

| # | Finding | Why it matters | Decision |
|---|---|---|---|
| F-01 | `MatchStatus` has Completed and Cancelled, but no use case completes, cancels or leaves a match | UC-13 lists completed matches, so something must set that status | Add small use cases: leave match, cancel match. Mark a match Completed automatically when its end time has passed |
| F-02 | UC-07 needs "teams × 2" players, but no use case defines the number of teams of a match | The balancing algorithm needs the team count | Add `team_count` (default 2) to the match in UC-04 |
| F-03 | Nothing says how a user becomes a Club Representative or Facility Staff | Roles protect UC-08 to UC-12, so they must come from somewhere | Roles are assigned by an administrator or loaded as seed data for the demo; document this as an assumption |
| F-04 | Tournament teams are plain names with no users, and bracket games have no facility or time | The charter lists facility coordination, but tournament games ignore it | For the MVP keep teams as names, and add an optional facility slot to a bracket game so UC-11 also protects tournament games |
| F-05 | The AI returns a rating, but no place stores it | Ratings would be recomputed on every balancing and cannot be checked later | Store the last rating per user and sport in `PROFILE_SPORT` (optional column) |
| F-06 | Password reset is missing | A forgotten password locks the account | Add as a Low priority use case, or declare it out of scope |
| F-07 | Charter lists Python and Java as backend, the specification and code use Python only | Two languages would split the team's effort | Confirm Python as the single backend language and update the charter |
| F-08 | The charter's out-of-scope list says communication is "text-based chat", the specification says in-app chat is out of scope | The two documents contradict each other | Treat chat as out of scope and correct the charter wording |
| F-09 | UC-03 shows the profile on a "public page" | The page can expose availability and skill of students | Show only name, sports and skill level publicly; keep availability private |
| F-10 | UC-13 only shows completed matches | Students cannot see their upcoming matches in one place (UC-06 postcondition promises this) | Extend UC-13 with an "Upcoming" tab |

---

## 7. Risk Analysis

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | Gemini Pro is slow, unavailable or its quota runs out | Medium | Medium | Fallback to declared skill levels (UC-07 alt. 2a), a short timeout, caching of ratings (F-05) |
| R-02 | Double booking or overfull matches caused by simultaneous requests | Medium | High | Transactions and database constraints (section 3.3) and tests with parallel requests |
| R-03 | Verification e-mails land in spam or are delayed | Medium | Medium | Resend option (UC-01 alt. 5a), short test with both university domains, clear message to the user |
| R-04 | The critical path (71 days, see the [PERT chart](plan/README.md#pert-chart)) has no slack: a delay in Accounts & Profiles, the Web UI or Deployment delays the codebase deadline of 30.11.2026 | Medium | High | Build High priority use cases first (UC-01 to 06, 11), then Medium ones; Low priority UC-13 last |
| R-05 | Unresolved gaps (section 6) change the design late | Medium | Medium | F-01 to F-05 are decided (section 6); F-06 to F-10 are decided before the Software Design Report on 15.11.2026 |
| R-06 | Personal data of students is exposed or processed unlawfully (KVKK) | Low | High | BR-03, hashed passwords, HTTPS, public profile limited to non-sensitive fields (F-09) |

---

## 8. Traceability

| Use case | Analysis artifacts |
|---|---|
| UC-01 | Sequence 4.1, account state 4.5, entities USER and VERIFICATION_CODE, BR-01, BR-02, R-03 |
| UC-02 | Account state 4.5, BR-04 |
| UC-03 | Entities PROFILE_SPORT and AVAILABILITY_SLOT, F-09 |
| UC-04 | Sequence 4.2, entity MATCH, BR-05, BR-06, F-02 |
| UC-05 | Entity MATCH (filter columns: sport, start time, skill level) |
| UC-06 | Match state 4.5, entity MATCH_PARTICIPANT, BR-07, R-02 |
| UC-07 | Sequence 4.3, `team_no`, BR-03, BR-12, F-02, F-05, R-01 |
| UC-08 | Tournament state 4.5, entities TOURNAMENT and TEAM, BR-08, F-04 |
| UC-09 | Entity BRACKET_MATCH, tournament state 4.5, BR-11 |
| UC-10 | Sequence 4.4, entity BRACKET_MATCH (`next_match_id`), BR-10 |
| UC-11 | Sequence 4.2, entities FACILITY_BLOCK and MATCH, BR-06, R-02 |
| UC-12 | Entities FACILITY, FACILITY_SPORT and FACILITY_BLOCK, BR-09, F-03 |
| UC-13 | Match state 4.5, BR-13, F-01, F-10 |

---

## 9. Conclusion

The 13 use cases form a consistent base for design. The analysis added a database-ready data model, four sequence diagrams for the critical flows, state diagrams for matches, accounts and tournaments, 13 business rules, 10 findings and 6 risks. Findings F-01 to F-05 were decided by the team because they change use cases and data structures; the rest will be decided during design.
