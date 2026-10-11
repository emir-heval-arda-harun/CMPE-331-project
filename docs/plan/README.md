# CampusEvent – Project Plan Documents

| Document | File |
|---|---|
| Project Charter | [../CHARTER.MD](../CHARTER.MD) |
| Work Breakdown Structure (WBS) | [WBS_Diagram.pdf](WBS_Diagram.pdf) · [PNG](WBS_Diagram.png) · [source](wbs_diagram.mmd) |
| Gantt chart | [gantt_chart.pdf](gantt_chart.pdf) · [PNG](gantt_chart.png) · [source](gantt_chart.mmd) |
| PERT chart | [pert_chart.pdf](pert_chart.pdf) · [PNG](pert_chart.png) · [source](pert_chart.mmd) |

The WBS, the Gantt chart and the PERT chart show the same 21 tasks, owners and dates. The charts are drawn with Mermaid from the `.mmd` source files. To change a chart, edit its `.mmd` file and render it again.

## Work Breakdown Structure (WBS)
The project is split into four work packages: 1.0 Planning & Analysis, 2.0 Software Design, 3.0 Implementation and 4.0 Testing & Delivery. Every use case (UC-01 to UC-13) is covered by a backend task and a web UI task in 3.0.

![WBS diagram](WBS_Diagram.png)

## Task List
Dates are 2026. Days are calendar days. Slack is the number of days a task can be late without delaying the final delivery.

| ID | Task | Owner | Start | End | Days | Slack | Critical |
|---|---|---|---|---|---|---|---|
| 1.1 | Project Charter | Heval & E.Arda | 20 Sep | 02 Oct | 12 | 0 | **yes** |
| 1.2 | Requirements Definition | Harun & Emir | 02 Oct | 11 Oct | 9 | 0 | **yes** |
| 1.3 | Requirement Analysis | Heval & Onur | 11 Oct | 18 Oct | 7 | 0 | **yes** |
| 2.1 | Cloud Infra Plan | Onur | 18 Oct | 11 Nov | 24 | 2 |  |
| 2.2 | API & ER Diagrams | Heval & Harun | 18 Oct | 12 Nov | 25 | 1 |  |
| 2.3 | UI/UX & AI Logic | E.Arda & Emir | 18 Oct | 13 Nov | 26 | 0 | **yes** |
| 2.4 | Software Design Report | All | 13 Nov | 16 Nov | 3 | 0 | **yes** |
| 3.1 | DB Integration | Heval | 16 Nov | 19 Nov | 3 | 0 | **yes** |
| 3.2 | AI Matchmaking (UC-07) | Emir | 16 Nov | 21 Nov | 5 | 1 |  |
| 3.3 | Backend - Accounts & Profiles (UC-01 to 03) | Heval | 19 Nov | 22 Nov | 3 | 0 | **yes** |
| 3.4 | Backend - Tournaments (UC-08 to 10) | Harun | 19 Nov | 22 Nov | 3 | 1 |  |
| 3.5 | Backend - Facilities (UC-11, 12) | E.Arda | 19 Nov | 22 Nov | 3 | 1 |  |
| 3.6 | Backend - Matches (UC-04 to 06, 13) | E.Arda | 22 Nov | 25 Nov | 3 | 2 |  |
| 3.7 | Web UI - Accounts, Profiles & Matches (UC-01 to 06, 13) | Emir | 22 Nov | 27 Nov | 5 | 0 | **yes** |
| 3.8 | Web UI - Facilities & Tournaments (UC-08 to 12) | Harun | 22 Nov | 26 Nov | 4 | 1 |  |
| 3.9 | CI/CD Pipeline Setup | Onur | 16 Nov | 20 Nov | 4 | 7 |  |
| 4.1 | Software Testing Report | All | 22 Nov | 23 Nov | 1 | 7 |  |
| 4.2 | Integration Testing & Bug Fixing | All | 27 Nov | 29 Nov | 2 | 1 |  |
| 4.3 | Documentation & Presentation Prep | All | 27 Nov | 29 Nov | 2 | 1 |  |
| 4.4 | Deployment | Onur | 27 Nov | 30 Nov | 3 | 0 | **yes** |
| 4.5 | Final Codebase Delivery | All | 30 Nov | 30 Nov | 0 | 0 | **yes** |

## Gantt Chart
Red bars are on the critical path.

![Gantt chart](gantt_chart.png)

## PERT Chart
Each task shows its duration (Dur), earliest start and finish (ES, EF), latest start and finish (LS, LF) and slack, counted in days from 20 September. Highlighted (orange) tasks have zero slack and form the critical path:

1.1 Project Charter → 1.2 Requirements Definition → 1.3 Requirement Analysis → 2.3 UI/UX & AI Logic → 2.4 Software Design Report → 3.1 DB Integration → 3.3 Backend: Accounts & Profiles → 3.7 Web UI: Accounts, Profiles & Matches → 4.4 Deployment → 4.5 Final Codebase Delivery

12 + 9 + 7 + 26 + 3 + 3 + 3 + 5 + 3 = **71 days** (20 Sep to 30 Nov)

Any delay on these tasks delays the final delivery. The other tasks have between 1 and 7 days of slack.

![PERT chart](pert_chart.png)
