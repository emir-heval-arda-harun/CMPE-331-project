# Requirement Analysis Models

All analysis models of the [Requirement Analysis Report](../requirement_analysis_report.md). Diagrams are kept as image (`.png`, `.svg`) and as source (`.mmd` Mermaid, or the small Python script that draws them).

## Data models (`data/`)
| Model | Files | Report section |
|---|---|---|
| Domain class model | [png](data/domain_class_model.png), [mmd](data/domain_class_model.mmd) | 2.2 |
| Preliminary E-R diagram | [png](data/er_diagram.png), [mmd](data/er_diagram.mmd) | 3.1 |

The data dictionary and database design notes are in sections 3.2 and 3.3 of the report.

## Business process and data flow models (`process/`)
| Model | Files | Report section |
|---|---|---|
| BPD 1: account registration and profile setup | [png](process/bpd_account_onboarding.png), [svg](process/bpd_account_onboarding.svg) | 2.4 |
| BPD 2: organizing and playing a match | [png](process/bpd_match_lifecycle.png), [svg](process/bpd_match_lifecycle.svg) | 2.4 |
| BPD 3: running a tournament | [png](process/bpd_tournament.png), [svg](process/bpd_tournament.svg) | 2.4 |
| BPD 4: facility schedule and conflict check | [png](process/bpd_facility_management.png), [svg](process/bpd_facility_management.svg) | 2.4 |
| DFD level 0 (context) | [png](process/dfd_level0_context.png), [mmd](process/dfd_level0_context.mmd) | 2.5 |
| DFD level 1 | [png](process/dfd_level1.png), [svg](process/dfd_level1.svg) | 2.5 |

The BPDs are drawn by [`make_bpd.py`](process/make_bpd.py) and the level 1 DFD by [`make_dfd.py`](process/make_dfd.py).

## Behavioral models (`behavior/`)
| Use cases | Model | Files | Report section |
|---|---|---|---|
| UC-01 | Sequence: register and verify | [png](behavior/sequence_uc01_register_verify.png), [mmd](behavior/sequence_uc01_register_verify.mmd) | 4.1 |
| UC-02 | Sequence: log in | [png](behavior/sequence_uc02_login.png), [mmd](behavior/sequence_uc02_login.mmd) | 4.6 |
| UC-03 | Sequence: manage profile | [png](behavior/sequence_uc03_manage_profile.png), [mmd](behavior/sequence_uc03_manage_profile.mmd) | 4.6 |
| UC-04, UC-11 | Sequence: create a match with conflict check | [png](behavior/sequence_uc04_uc11_create_match.png), [mmd](behavior/sequence_uc04_uc11_create_match.mmd) | 4.2 |
| UC-05, UC-06 | Sequence: browse, filter and join | [png](behavior/sequence_uc05_uc06_browse_and_join.png), [mmd](behavior/sequence_uc05_uc06_browse_and_join.mmd) | 4.6 |
| UC-07 | Sequence: AI team balancing with fallback | [png](behavior/sequence_uc07_team_balancing.png), [mmd](behavior/sequence_uc07_team_balancing.mmd) | 4.3 |
| UC-08, UC-09 | Sequence: create tournament and generate bracket | [png](behavior/sequence_uc08_uc09_tournament_and_bracket.png), [mmd](behavior/sequence_uc08_uc09_tournament_and_bracket.mmd) | 4.6 |
| UC-10 | Sequence: record a score and advance the winner | [png](behavior/sequence_uc10_record_score.png), [mmd](behavior/sequence_uc10_record_score.mmd) | 4.4 |
| UC-12 | Sequence: manage facility schedule | [png](behavior/sequence_uc12_manage_facility_schedule.png), [mmd](behavior/sequence_uc12_manage_facility_schedule.mmd) | 4.6 |
| UC-13 | Sequence: track activity history | [png](behavior/sequence_uc13_activity_history.png), [mmd](behavior/sequence_uc13_activity_history.mmd) | 4.6 |
| UC-14, UC-15 | Sequence: leave and cancel a match | [png](behavior/sequence_uc14_uc15_leave_and_cancel.png), [mmd](behavior/sequence_uc14_uc15_leave_and_cancel.mmd) | 4.6 |
| UC-04, 06, 13, 14, 15 | State: match | [png](behavior/state_match.png), [mmd](behavior/state_match.mmd) | 4.5 |
| UC-01, UC-02 | State: user account | [png](behavior/state_user_account.png), [mmd](behavior/state_user_account.mmd) | 4.5 |
| UC-08, 09, 10 | State: tournament | [png](behavior/state_tournament.png), [mmd](behavior/state_tournament.mmd) | 4.5 |

Every use case (UC-01 to UC-15) is covered by at least one behavioral model.

## UI mockups (`ui/`)
Low-fidelity mockups of the main screens, see [`ui/README.md`](ui/README.md).
