# UC-02: Log In

| Field | Value |
|---|---|
| **ID** | UC-02 |
| **Primary actor** | Student, Club Representative, Facility Staff |
| **Priority** | High |
| **Test** | [tests/test_uc02_login.py](../../tests/test_uc02_login.py) |

## Description
A registered user signs in to access the platform.

## Preconditions
- The user has an account (UC-01).

## Trigger
The user selects **Log in**.

## Main Success Scenario
1. The user enters e-mail address and password.
2. The system checks the credentials.
3. The system checks that the account is verified.
4. The system creates a session and shows the user's home page.

## Alternative Flows
- **2a. Wrong e-mail or password:** the system shows "Invalid e-mail or password" without telling which one is wrong.
- **2b. Too many wrong passwords:** after 5 wrong passwords in a row, logging in to that account pauses for 1 minute; every further wrong password doubles the pause, up to 15 minutes. During a pause even the right password is refused, with the same answer as 2a, so the pause does not tell that the address has an account. The right password after a pause sets the count back to 0 (penetration test P1, #55).
- **3a. Account not verified:** the system refuses the login and offers to resend the verification code.

## Postconditions
- The user has an active session; each later request is linked to this user and role.
- Logging out ends this session, every copy of its cookie and the account's other sessions (penetration test P3, #55).

## Business Rules
- BR-03: Only verified accounts can log in.
