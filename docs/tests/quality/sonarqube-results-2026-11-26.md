# SonarQube results of 26.11.2026 (dated copy)

**Saved by:** Heval Hüseyin Demir · **Saved on:** 26.11.2026 · Part of the [SonarQube report](README.md).

The SonarQube Cloud dashboard always shows the latest analysis and changes after every push. This file keeps the results of one analysis, so the report can be checked later. The data was read on 26.11.2026 from the public Web API of SonarQube Cloud (`api/measures/component`, `api/issues/search`, `api/hotspots/search`, `api/qualitygates/project_status`, `api/project_analyses/search`) for the project `emir-heval-arda-harun_CMPE-331-project`.

## Analysis
| Field | Value |
|---|---|
| Branch | `main` |
| Commit | `22825b5` (merge of #59) |
| Analysis time | 26.11.2026 15:38 UTC (18:38 Istanbul) |
| Kind | Automatic analysis (AutoScan), quality gate "Sonar way" |
| Quality gate | **Passed** |
| Previous analyses | 25.11.2026 `e03749e`, 24.11.2026 `7de0cd3` (results of 24.11 in the [report](README.md)) |

## Measures
| Measure | Value |
|---|---|
| Lines of code | 10,347 (14,020 lines) |
| Bugs | 9 (Reliability rating **C**) |
| Vulnerabilities | 1 (Security rating **C**) |
| Code smells | 26 (Maintainability rating **A**) |
| Security hotspots | 0 |
| Duplicated lines | 1.2 % |
| Coverage | not reported: AutoScan does not import our coverage report; the coverage of CI is in [part 7](../coverage/README.md) |

All 36 open issues are in two places outside the application code: the October UI mockups in `docs/analysis/ui/` (35) and `pyproject.toml` (1). **The Python code (`src/`, `tests/`) and the Jinja templates have no open issue.**

| Group in the [plan](README.md) | Rule | Count | Status on 26.11.2026 |
|---|---|---|---|
| S2 | `text:S8565` no lock file | 1 | **Accepted** on 26.11.2026 after this copy was saved: the lock file `requirements-lock.txt` exists since #54, but the rule only recognises `uv.lock`, `poetry.lock`, `pdm.lock`, `pylock.toml` or a fully pinned `requirements.txt` |
| B1 | `Web:S5254` `<html>` without `lang` | 9 | Fixed in #39 (`lang="en"` in the mockups); gone from `main` after the merge |
| C1 | `Web:S6853` form label without a linked control | 26 | **Accepted** on 26.11.2026 after this copy was saved: mockups, not part of the app; the real forms link every label (`for`/`id`) |
| **Total** | | **36** | |

## All open issues
| # | Group | Rule | Type | Impact | File and line | Message | Issue key |
|---|---|---|---|---|---|---|---|
| 1 | S2 | `text:S8565` | vulnerability | security medium | `pyproject.toml` | No lock file (uv.lock, poetry.lock, pdm.lock, pylock.toml or a fully pinned requirements.txt) | `AaIFP85GBLOuwLylVy7r` |
| 2 | B1 | `Web:S5254` | bug | reliability medium | `docs/analysis/ui/01_sign_up.html`:1 | `<html>` without `lang` | `AaIFP85ABLOuwLylVy7N` |
| 3 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/01_sign_up.html`:22 | Form label without a linked control | `AaIFP84_BLOuwLylVy7K` |
| 4 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/01_sign_up.html`:22 | Form label without a linked control | `AaIFP84_BLOuwLylVy7L` |
| 5 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/01_sign_up.html`:23 | Form label without a linked control | `AaIFP84_BLOuwLylVy7M` |
| 6 | B1 | `Web:S5254` | bug | reliability medium | `docs/analysis/ui/02_log_in.html`:1 | `<html>` without `lang` | `AaIFP85BBLOuwLylVy7W` |
| 7 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/02_log_in.html`:21 | Form label without a linked control | `AaIFP85BBLOuwLylVy7U` |
| 8 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/02_log_in.html`:22 | Form label without a linked control | `AaIFP85BBLOuwLylVy7V` |
| 9 | B1 | `Web:S5254` | bug | reliability medium | `docs/analysis/ui/03_my_profile.html`:1 | `<html>` without `lang` | `AaIFP84pBLOuwLylVy7J` |
| 10 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/03_my_profile.html`:24 | Form label without a linked control | `AaIFP84pBLOuwLylVy7I` |
| 11 | B1 | `Web:S5254` | bug | reliability medium | `docs/analysis/ui/04_find_event.html`:1 | `<html>` without `lang` | `AaIFP85DBLOuwLylVy7d` |
| 12 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/04_find_event.html`:22 | Form label without a linked control | `AaIFP85DBLOuwLylVy7Z` |
| 13 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/04_find_event.html`:22 | Form label without a linked control | `AaIFP85DBLOuwLylVy7a` |
| 14 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/04_find_event.html`:22 | Form label without a linked control | `AaIFP85DBLOuwLylVy7b` |
| 15 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/04_find_event.html`:23 | Form label without a linked control | `AaIFP85DBLOuwLylVy7c` |
| 16 | B1 | `Web:S5254` | bug | reliability medium | `docs/analysis/ui/05_event_details.html`:1 | `<html>` without `lang` | `AaIFP85BBLOuwLylVy7X` |
| 17 | B1 | `Web:S5254` | bug | reliability medium | `docs/analysis/ui/06_create_event.html`:1 | `<html>` without `lang` | `AaIFP85DBLOuwLylVy7m` |
| 18 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/06_create_event.html`:22 | Form label without a linked control | `AaIFP85DBLOuwLylVy7e` |
| 19 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/06_create_event.html`:22 | Form label without a linked control | `AaIFP85DBLOuwLylVy7f` |
| 20 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/06_create_event.html`:23 | Form label without a linked control | `AaIFP85DBLOuwLylVy7g` |
| 21 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/06_create_event.html`:24 | Form label without a linked control | `AaIFP85DBLOuwLylVy7h` |
| 22 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/06_create_event.html`:25 | Form label without a linked control | `AaIFP85DBLOuwLylVy7i` |
| 23 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/06_create_event.html`:25 | Form label without a linked control | `AaIFP85DBLOuwLylVy7j` |
| 24 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/06_create_event.html`:25 | Form label without a linked control | `AaIFP85DBLOuwLylVy7k` |
| 25 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/06_create_event.html`:26 | Form label without a linked control | `AaIFP85DBLOuwLylVy7l` |
| 26 | B1 | `Web:S5254` | bug | reliability medium | `docs/analysis/ui/07_facility_management.html`:1 | `<html>` without `lang` | `AaIFP85ABLOuwLylVy7T` |
| 27 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/07_facility_management.html`:23 | Form label without a linked control | `AaIFP85ABLOuwLylVy7O` |
| 28 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/07_facility_management.html`:23 | Form label without a linked control | `AaIFP85ABLOuwLylVy7P` |
| 29 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/07_facility_management.html`:24 | Form label without a linked control | `AaIFP85ABLOuwLylVy7Q` |
| 30 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/07_facility_management.html`:24 | Form label without a linked control | `AaIFP85ABLOuwLylVy7R` |
| 31 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/07_facility_management.html`:25 | Form label without a linked control | `AaIFP85ABLOuwLylVy7S` |
| 32 | B1 | `Web:S5254` | bug | reliability medium | `docs/analysis/ui/08_my_activities.html`:1 | `<html>` without `lang` | `AaIFP85CBLOuwLylVy7Y` |
| 33 | B1 | `Web:S5254` | bug | reliability medium | `docs/analysis/ui/09_find_event_mobile.html`:1 | `<html>` without `lang` | `AaIFP85EBLOuwLylVy7q` |
| 34 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/09_find_event_mobile.html`:21 | Form label without a linked control | `AaIFP85EBLOuwLylVy7n` |
| 35 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/09_find_event_mobile.html`:21 | Form label without a linked control | `AaIFP85EBLOuwLylVy7o` |
| 36 | C1 | `Web:S6853` | code smell | reliability medium | `docs/analysis/ui/09_find_event_mobile.html`:21 | Form label without a linked control | `AaIFP85EBLOuwLylVy7p` |
