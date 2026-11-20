# CMPE-331-project – CampusEvent

A campus event platform for university students to organize, join and track events of any kind (sports, study groups, game nights, club meetings and more).

## Documents
- [Project Charter](docs/CHARTER.MD)
- [Project plan (WBS, Gantt & PERT)](docs/plan/README.md)
- [Use cases](docs/requirements/README.md)
- [Requirements Specification Report](docs/requirements_specification.md)
- [Software Design Report](docs/software_design_report.md) and [design models](docs/design/README.md)
- [UI/UX Design](docs/ui_ux_design.md): users, navigation, user flows, screens, design system, accessibility
- [Database: setup, migrations, demo data](docs/database/README.md)
- [Change requests](docs/change_requests/): [CR-01 Admin approval of event requests](docs/change_requests/CR-01_admin_event_approval.md)
- [Requirement Analysis Report](docs/requirement_analysis_report.md), [analysis models, BPD, DFD](docs/analysis/README.md) and [UI mockups](docs/analysis/ui/README.md)

## Running the requirement tests
```bash
pip install -r requirements-dev.txt
python -m pytest
```
The code under `src/` is only a skeleton, so all tests currently fail by design.
