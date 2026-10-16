# Project Charter: CampusEvent

## 1. Project Purpose and Objectives
The primary objective of this project is to develop a campus event platform designed for university students to easily organize, join, and track events of any kind (for example sports matches, study groups, board game nights, club meetings, or workshops). The system aims to eliminate the friction in finding people to take part in an activity, facilitate campus facility reservations without conflicts, and foster an active community through shared scheduling and event discovery.


## 2. Stakeholders & Roles
* **Product Owner:** Emre arda kum
* **Software Engineering Team:** 
    * {Heval hüseyin demir} : Project Manager & Database Designer
    * {Emre arda kum} : Backend Developer 
    * {Emir gül} : AI Engineer
    * {Harun gündaş} : Backend Developer
    * {Onur alioğlu} : DevOps Engineer
* **GH Repo/Project URL:** https://github.com/emir-heval-arda-harun/CMPE-331-project
* **Potential users:**
    * University students looking to organize, join, and track campus events.
    * Campus facility management personnel overseeing hall, field, court and room reservations.


## 3. Project Scope
### Project domain
Higher Education & Campus Life / Social Community Platform. 
This project operates at the intersection of university campus life and event management. It focuses on enhancing student well-being and social connectivity by providing a centralized digital ecosystem for organizing and joining events of any category (sports, study, hobbies, clubs) within higher education institutions.

### In-Scope 
*  User Authentication & Profile Management
  * Customizable user profiles displaying interests (free-text event categories) and availability.
* **Event Creation & Participation Management:** 
  * Interfaces for students to create, browse, join, leave, and cancel events of any kind, with a free-text category and a participant capacity.
  * Filtering options based on category, date, time, and keyword.
* **Facility Coordination:**
  * Predefined campus facilities with capacities and schedules, so that users can plan events without location conflicts.
  * Facility staff can define facilities and block unavailable time periods.
* **Activity History:**
  * Students can see the events they have taken part in.

### Out-of-Scope 
* Financial Transactions & Payment Gateway Integration (No credit card or paid field booking features)
* Real-time GPS Tracking of Participants (Only predefined campus facility locations will be used)
* Direct University SIS/Banner Database Integration (Authentication relies on email domain verification rather than internal school APIs)
* Live Audio/Video Streaming or In-App Calling (Communication is restricted to text-based chat)
* Native Mobile App Development for iOS/Android (The application will be developed as a responsive web platform; standalone app stores deployment is out-of-scope)


## 4. Technology Stack
### Backend Stack
* Python
* Java

### Frontend Stack
* HTML
* CSS
* JavaScript

### AI Stack & Usage Strategy
* **GeminiPRO (Feature Integration):** 
  * *Application:* Integrated into the system to process user data and power the core matchmaking algorithm, ensuring balanced skill levels among players.
* **ChatGPT (Research & Planning):** 
  * *Application:* Utilized as a supplementary research assistant during the requirements phase to explore database schema best practices and conceptualize user workflows.
* **Claude (Troubleshooting & Optimization):** 
  * *Application:* Used strictly as an analytical tool to troubleshoot complex backend bugs and review the time complexity of the tournament bracket generation algorithms.


## 5. Project Milestones
| Deliverable                       | Deadline          |
|---                                |---                |
| Project Charter                   | 02.10.2026 23:59  |
| Requirements Definition Report    | 11.10.2026 23:59  |
| Requirement Analysis Report       | 18.10.2026 23:59  |
| Software Design Report            | 15.11.2026 23:59  |
| Software Testing Report           | 22.11.2026 23:59  |
| Codebase                          | 30.11.2026 23:59  |
| Presentation                      | TBA (see sched.)  |
	
	
	
	
	
	
	
	
