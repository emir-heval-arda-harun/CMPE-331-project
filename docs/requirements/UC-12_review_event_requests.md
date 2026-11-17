# UC-12: Review Event Requests

| Field | Value |
|---|---|
| **ID** | UC-12 |
| **Primary actor** | Admin |
| **Secondary actors** | E-mail Service |
| **Priority** | High |
| **Test** | [tests/test_uc12_review_event_requests.py](../../tests/test_uc12_review_event_requests.py) |

## Description
Every event created by a student (UC-04) is first an **event request** with status **Pending**. An admin checks the request and either approves it, so that it becomes visible and joinable, or rejects it with a reason. This keeps inappropriate or rule-breaking events off the platform. The workflow follows common campus event platforms (see [CR-01](../change_requests/CR-01_admin_event_approval.md)).

## Preconditions
- The user is logged in with the **Admin** role (assigned like the Facility Staff role; see assumption A-04).
- At least one event request is **Pending**.

## Trigger
The admin opens **Event Requests**.

## Main Success Scenario
1. The system lists all pending requests, ordered by start time (title, category, description, facility, time, capacity, organizer name).
2. The admin opens a request and selects **Approve**.
3. The system sets the status to **Open** and stores who reviewed it and when.
4. The event appears in the event list (UC-05) and can be joined (UC-06).
5. The system e-mails the decision to the organizer.

## Alternative Flows
- **2a. The admin selects Reject:**
  1. The admin enters a reason (required).
  2. The system sets the status to **Rejected**, stores the reason, the reviewer and the time, and frees the facility slot (UC-07).
  3. The system e-mails the decision and the reason to the organizer.
  4. The organizer may correct the event and submit a new request (UC-04).
- **2a1. Reason is empty:** the system rejects the input.
- **2b. The request is no longer pending** (already reviewed, withdrawn by the organizer, or expired): the system refuses the action.
- **2c. The user is not an admin:** the system refuses the request.
- **Expiry (system):** a request that is still pending at its start time is set to **Rejected** automatically (reason "Not reviewed before the start time", no reviewer) and its facility slot is freed.

## Organizer view
The organizer sees all own requests with their status (Pending, Open/Full, Rejected with reason, Cancelled) on **My Activities**. A pending request can be withdrawn with **Cancel** (UC-11).

## Postconditions
- Approved: the event is **Open**, listed and joinable.
- Rejected: the event is **Rejected**, not listed, and its facility slot is free.

## Business Rules
- BR-15: Every new event starts as **Pending**. Pending events are not listed (UC-05) and cannot be joined (UC-06).
- BR-16: A pending request holds its facility slot, so two requests can never be approved for the same slot (UC-07).
- BR-17: Only an admin approves or rejects requests; a rejection always has a reason; only pending requests can be reviewed.
- BR-18: A request that is not reviewed before its start time is rejected automatically.
