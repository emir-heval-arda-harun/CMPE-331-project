# Application
**Name:** CampusEvent
**Description:** A responsive web application where university students organize, find and join events of any kind (sports, study groups, game nights, club meetings, workshops) at campus facilities. Facility staff manage facilities and their schedules.
**Actors:** Student, Facility Staff
**Style:** Clean and modern, light background, dark blue top navigation bar, blue primary buttons, rounded cards; mobile friendly (360 px and wider).

---

# Screen: Sign Up
## Purpose
A new student creates an account with a university e-mail address and verifies it (UC-01).
## Layout
Single Column
## Components
- Header: CampusEvent logo
- Textbox: Full name
- Textbox: University e-mail
- Textbox: Password (masked)
- Button: Sign up
- Textbox: Verification code (6 digits)
- Button: Verify
- Button: Send a new code
- Label: Error message
## Actions
- Sign up: creates an unverified account and sends a code by e-mail.
- Verify: activates the account when the code is correct.
- Send a new code: sends another code.
## Navigation
- After a successful verification go to Log In.
- Link "Already have an account?" goes to Log In.
## User Flow
1. The student enters name, university e-mail and password and selects Sign up.
2. The system sends a code; the code box appears.
3. The student enters the code and selects Verify.
4. The student is sent to Log In.
## Notes
- A non-university e-mail domain shows "Please use your university e-mail address."
- A wrong or expired code shows an error and allows requesting a new code.

# Screen: Log In
## Purpose
A registered user logs in (UC-02).
## Layout
Single Column
## Components
- Textbox: E-mail
- Textbox: Password (masked)
- Button: Log in
- Label: Error message
- Button: Resend verification code (only for unverified accounts)
## Actions
- Log in: checks e-mail and password.
## Navigation
- Success: Student goes to Find Events; Facility Staff goes to Facility Management.
- Link "No account yet?" goes to Sign Up.
## User Flow
1. The user enters e-mail and password.
2. The user selects Log in.
3. The system opens the start page of the user's role.
## Notes
- Wrong data shows "Invalid e-mail or password" without saying which part is wrong.
- Unverified accounts cannot log in and are offered a new code.

# Screen: My Profile
## Purpose
The student records interests (free-text categories) and availability (UC-03).
## Layout
Two Columns
## Components
- Header: Top navigation (Find Events, Create Event, My Activities, Facilities, user menu)
- Card: Interests
- Textbox: New interest (free text)
- Button: Add interest
- Card: Weekly availability
- Table: Day, From, To, Remove
- Button: Add time slot
- Button: Save profile
## Actions
- Add interest / remove interest.
- Add time slot / remove time slot.
- Save profile: validates and stores the profile.
## Navigation
- After saving, stay on My Profile and show a confirmation.
## User Flow
1. The student opens My Profile from the user menu.
2. The student adds interests and availability.
3. The student selects Save profile.
## Notes
- At least one interest is required.
- A slot whose end time is before the start time is rejected.
- Categories are free text, trimmed and compared without regard to upper or lower case.

# Screen: Find Events
## Purpose
The student searches upcoming open events and joins one (UC-05, UC-06).
## Layout
Single Column
## Components
- Header: Top navigation
- Card: Filters
- Search Box: Keyword
- Textbox: Category
- Date Picker: Date
- Textbox: Time range
- Button: Apply filters
- Card: Event list item (start time, title, facility, organizer, participants, category tag, status tag)
- Button: Join (on every open event)
## Actions
- Apply filters: shows only events that satisfy all filters.
- Join: joins the event if a place is free.
- Select an event card: opens Event Details.
## Navigation
- Event card goes to Event Details.
- Empty result: link "Create an event" goes to Create Event.
## User Flow
1. The student opens Find Events and sees upcoming open events, soonest first.
2. The student sets filters and selects Apply filters.
3. The student opens an event or selects Join.
## Notes
- Full events show a "Full" tag and a disabled button.
- On a phone (390 px) the filters are stacked and each event card wraps below its time.

# Screen: Event Details
## Purpose
Shows one event and lets the student join, leave or (as organizer) cancel it (UC-06, UC-10, UC-11).
## Layout
Two Columns
## Components
- Header: Top navigation
- Label: Title, category tag and status tag
- Label: Date, time, facility, number of participants
- Panel: Description
- Table: Participants (name, role)
- Panel: Actions
- Button: Join event
- Button: Leave event
- Button: Cancel event
## Actions
- Join event: adds the student when a place is free.
- Leave event: removes the student from the participants.
- Cancel event: sets the event to Cancelled and frees the facility slot (asks for confirmation).
## Navigation
- Back to Find Events.
- After cancelling, go to My Activities.
## User Flow
1. The student opens an event from Find Events.
2. The student selects Join or Leave.
3. The organizer may select Cancel event and confirm.
## Notes
- Non-participants see Join; participants see Leave; only the organizer sees Cancel.
- The organizer cannot leave the event; the event has to be cancelled.
- E-mail addresses of other students are never shown.

# Screen: Create Event
## Purpose
The student organizes a new event at a campus facility (UC-04, UC-07).
## Layout
Two Columns
## Components
- Header: Top navigation
- Textbox: Title
- Textbox: Category (free text)
- Textbox: Description
- Dropdown: Facility (shows its capacity)
- Date Picker: Date
- Textbox: Start time
- Textbox: End time
- Textbox: Participants (capacity)
- Button: Create event
- Card: Facility schedule of the week (free, busy and blocked slots)
## Actions
- Create event: checks the input and the facility availability, then creates the event as Open.
## Navigation
- After creation go to Event Details of the new event.
## User Flow
1. The student fills in title, category and details.
2. The student selects a facility, date and time; the schedule shows free and busy slots.
3. The student enters the capacity and selects Create event.
## Notes
- Capacity must be at least 2 and not larger than the capacity of the facility.
- If the slot is busy, the system shows "This slot is busy" and suggests free slots of the day.
- The organizer is added as the first participant.

# Screen: Facility Management
## Purpose
Facility staff add facilities with a capacity and block unavailable periods (UC-08, UC-07).
## Layout
Two Columns
## Components
- Header: Top navigation
- Table: Facilities (name, capacity)
- Textbox: New facility name
- Textbox: Capacity
- Button: Add facility
- Dropdown: Facility
- Textbox: From – to
- Textbox: Reason
- Button: Block time
## Actions
- Add facility: stores a facility with its capacity.
- Block time: stores a blocked period that students cannot book.
## Navigation
- Only visible to Facility Staff.
## User Flow
1. The staff member adds a facility with its capacity.
2. The staff member selects a facility, a period and a reason and selects Block time.
## Notes
- Capacity must be at least 2.
- Blocks of the same facility must not overlap.
- Students are refused access to this screen.

# Screen: My Activities
## Purpose
The student sees the events they have taken part in (UC-09).
## Layout
Single Column
## Components
- Header: Top navigation
- Table: Date, Time, Event, Category, Facility
## Actions
- Select a row: opens Event Details.
## Navigation
- Back to Find Events.
## User Flow
1. The student opens My Activities.
2. The system lists completed events, newest first.
## Notes
- Only completed events are listed; upcoming and cancelled events are not.
- Empty state: "No completed events yet."
