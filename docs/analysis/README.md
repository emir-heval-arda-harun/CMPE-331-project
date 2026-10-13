# Requirement Analysis Models

All analysis models of the [Requirement Analysis Report](../requirement_analysis_report.md). Each diagram is kept as Mermaid source (`.mmd`) and as an image (`.png`, `.svg`).

## Data models (`data/`)
| Model | Files | Report section |
|---|---|---|
| Domain class model | [png](data/domain_class_model.png), [mmd](data/domain_class_model.mmd) | 2.2 |
| Preliminary E-R diagram | [png](data/er_diagram.png), [mmd](data/er_diagram.mmd) | 3.1 |

The data dictionary and database design notes are in sections 3.2 and 3.3 of the report.

## Behavioral models (`behavior/`)
| Model | Use cases | Files | Report section |
|---|---|---|---|
| Sequence: register and verify | UC-01 | [png](behavior/sequence_uc01_register_verify.png), [mmd](behavior/sequence_uc01_register_verify.mmd) | 4.1 |
| Sequence: create a match with conflict check | UC-04, UC-11 | [png](behavior/sequence_uc04_uc11_create_match.png), [mmd](behavior/sequence_uc04_uc11_create_match.mmd) | 4.2 |
| Sequence: AI team balancing with fallback | UC-07 | [png](behavior/sequence_uc07_team_balancing.png), [mmd](behavior/sequence_uc07_team_balancing.mmd) | 4.3 |
| Sequence: record a score and advance the winner | UC-10 | [png](behavior/sequence_uc10_record_score.png), [mmd](behavior/sequence_uc10_record_score.mmd) | 4.4 |
| State: match | UC-04, UC-06, UC-13 | [png](behavior/state_match.png), [mmd](behavior/state_match.mmd) | 4.5 |
| State: user account | UC-01, UC-02 | [png](behavior/state_user_account.png), [mmd](behavior/state_user_account.mmd) | 4.5 |
| State: tournament | UC-08, UC-09, UC-10 | [png](behavior/state_tournament.png), [mmd](behavior/state_tournament.mmd) | 4.5 |

The remaining use cases (UC-02, 03, 05, 06, 12, 13) are simple one-step flows and are covered by the state diagrams above and their use case documents in [`docs/requirements`](../requirements/README.md).
