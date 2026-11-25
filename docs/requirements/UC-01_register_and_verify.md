# UC-01: Register with University E-mail and Verify Account

| Field | Value |
|---|---|
| **ID** | UC-01 |
| **Primary actor** | Student (unregistered) |
| **Secondary actors** | E-mail service |
| **Priority** | High |
| **Test** | [tests/test_uc01_register_and_verify.py](../../tests/test_uc01_register_and_verify.py) |

## Description
A student creates a CampusEvent account using a university e-mail address. Because the system does not integrate with the university SIS, the e-mail domain is the only proof of being a member of the university.

## Preconditions
- The user does not already have an account with the same e-mail address.

## Trigger
The user selects **Sign up** on the landing page.

## Main Success Scenario
1. The user enters full name, university e-mail address and password.
2. The system checks that the e-mail domain is an accepted university domain (`bilgiedu.net`, `bilgi.edu.tr`).
3. The system creates an **unverified** account.
4. The system sends a one-time verification code to the e-mail address.
5. The user enters the verification code.
6. The system marks the account as **verified** and lets the user continue to profile setup (UC-03).

## Alternative Flows
- **1a. Password too short, too long or too easy to guess:** the system refuses a password shorter than 8 or longer than 128 characters, a very common password (for example `password123`) and a password of one repeated character, and asks for another one (penetration test P7, #55).
- **2a. E-mail is not a university address:** the system rejects the registration and shows "Please use your university e-mail address."
- **3a. E-mail already registered:** the system rejects the registration and offers the login page.
- **5a. Wrong or expired code:** the system shows an error; the user may retry or request a new code. An unknown address and an address that is already verified get the same answer, so this step does not tell which addresses have accounts (P6, #55).
- **5b. Too many wrong codes:** after 5 wrong tries the code stops working, with the same error as 5a; the user requests a new code. A new code can be requested at most once a minute per address (P2, #30, #55).

## Postconditions
- A verified account exists and the user can log in (UC-02).

## Business Rules
- BR-01: Only university e-mail domains are accepted.
- BR-02: Passwords are never stored in plain text.
