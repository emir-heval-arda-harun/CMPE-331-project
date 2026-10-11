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
- **3a. Account not verified:** the system refuses the login and offers to resend the verification code.

## Postconditions
- The user has an active session; each later request is linked to this user and role.
