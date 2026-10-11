# Project Charter: CampusEvent

## 1. Project Purpose and Objectives
The primary objective of this project is to develop a social sports-matching platform designed for university students to easily organize, join, and track amateur campus sports activities. The system aims to eliminate the friction in finding teammates or opponents, facilitate campus sports facility reservations, and foster an active community through automated scheduling and skill-based matchmaking.


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
    * University students looking to organize, join, and track amateur campus sports activities.
    * Campus sports facility management personnel overseeing field and court reservations.


## 3. Project Scope
### Project domain
Higher Education & Recreational Sports / Social Community Platform. 
This project operates at the intersection of university campus life and amateur sports management. It focuses on enhancing student well-being and social connectivity by providing a centralized digital ecosystem for recreational activities, skill-based sports matchmaking, and community-driven event organization within higher education institutions.

### In-Scope 
*  User Authentication & Profile Management
  * Customizable user profiles displaying preferred sports, personal skill levels, and availability.
* **Activity & Match Creation Management:** 
  * Interfaces for students to create, browse, and join amateur sports matches 
  * Filtering options based on date, time, sport type, and required skill level.
* **Campus Tournament & Bracket System:** 
  * Tools for student clubs to organize structured campus-wide tournaments.
  * Automated bracket generation, score tracking, and team advancement management.
* **Facility Coordination:**
  * Integration of predefined campus sports facility schedules to help users plan matches without location conflicts.

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
	
	
	
	
	
	
	
	
