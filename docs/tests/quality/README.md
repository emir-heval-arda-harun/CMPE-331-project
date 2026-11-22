# Code quality: SonarQube analysis

Part of the Software Testing Report (task 4.1) and of the instructor's review (#34, D. SonarQube). The test results and coverage are in [`docs/tests/coverage`](../coverage), the non-functional tests in [`docs/tests/non-func-tests`](../non-func-tests).

## Setup
- **Tool:** SonarQube Cloud (sonarcloud.io), Free plan, organization `emir-heval-arda-harun`, project `emir-heval-arda-harun_CMPE-331-project`.
- **Dashboard:** https://sonarcloud.io/project/overview?id=emir-heval-arda-harun_CMPE-331-project (public, no log in needed).
- **How it runs:** *Automatic Analysis*. The SonarQube Cloud GitHub App is installed on this repository only. It analyses `main` after every push and every pull request after each push, and writes the result on the pull request. There is no token and no extra CI job.
- **Scope:** all files in the repository: Python (`src`, `tests`, `scripts`, `migrations`), Jinja/HTML templates, CSS, the GitHub Actions workflow, `pyproject.toml`, and the HTML mockups in `docs/analysis/ui`.
- **Not in this analysis:** code coverage. Automatic Analysis cannot import a coverage report. Our coverage is measured with coverage.py, see the coverage files.
- Set up on 23.11.2026 by Heval.

## Results: first analysis of `main` (23.11.2026, 00:53, commit `c98923c`)

| Measure | Result | Rating |
|---|---|---|
| Lines of code | 8,069 | |
| Bugs | 9 | Reliability **C** |
| Vulnerabilities | 7 | Security **C** |
| Security hotspots | 0 | Security review **A** |
| Code smells | 29 | Maintainability **A** |
| Duplicated lines | 1.5 % | |

**By severity:** 0 blocker, 0 critical, 43 major, 2 minor. With SonarQube's newer software-quality impacts: 0 high, 43 medium, 2 low.

**Python code:** 0 bugs, 0 vulnerabilities, 0 code smells in `src`, `tests`, `scripts` and `migrations`. Every finding is in a configuration file, a template or a mockup.

The ratings are C only because of the 9 mockup bugs and the medium security findings in the CI workflow (see below). Neither is in the code that runs on the server.

## Findings and plan

There are no high or critical findings. The plan below still covers every finding, starting with the security ones.

| Id | Finding (SonarQube rule) | Where | Count | Severity / impact | Owner | Plan | Status |
|---|---|---|---|---|---|---|---|
| S1 | `pip install` without `--only-binary :all:` (githubactions:S8541) and without locked versions (githubactions:S8544) | `.github/workflows/ci.yml` lines 31 and 44 | 4 | Major / security medium | Onur | Pin the versions: generate `requirements-lock.txt` with hashes (`pip-compile --generate-hashes`) and install it in CI with `--require-hashes --only-binary :all:`. All our packages have wheels for Python 3.12 (`psycopg[binary]`, `argon2-cffi`). Pin `ruff` to one version. `pip-audit` from #36 checks the same packages for known CVEs. | Open, before the final delivery (30.11) |
| S2 | No lock file (text:S8565) | `pyproject.toml` | 1 | Major / security medium | Onur | Same fix as S1: the lock file closes this finding. | Open, with S1 |
| S3 | Script and stylesheet from a CDN without `integrity` and `crossorigin` (Web:S5725) | `src/campusevent/web/templates/base.html` lines 8 and 295 (Bootstrap 5.3.3 from jsDelivr) | 2 | Minor / security low | Emir | Serve Bootstrap from `static/` instead of jsDelivr. This also closes the open privacy point of the [UI/UX design](../../ui_ux_design.md) (Google Fonts and jsDelivr see the visitor's IP address). The other way is to add `integrity="sha384-…"` and `crossorigin="anonymous"` to both tags. | Open, before the final delivery (30.11) |
| B1 | `<html>` without `lang` (Web:S5254, WCAG 2 A) | `docs/analysis/ui/01`–`09_*.html` (UI mockups of the requirements analysis) | 9 | Major / reliability medium | Heval | Add `lang="en"`. The real pages have it already (`base.html`). | **Fixed in this pull request** |
| C1 | Form label without a linked control (Web:S6853) | `docs/analysis/ui/*.html` | 26 | Major / reliability medium | Heval | Mockups from October, not part of the app. The real forms link every label to its field (`for`/`id`), checked by `test_every_form_field_has_a_label` in `tests/web/test_web_extras.py` and in #32 (WCAG 1.3.1). Proposal: leave the mockups as they are, because they record the analysis as it was, and mark these 26 as *Accepted* in SonarQube with this reason. | To be accepted |
| C2 | `autofocus` attribute (Web:S9379) | `src/campusevent/web/templates/login.html` line 22, `signup.html` lines 15 and 59 | 3 | Major / reliability medium | Emir | `autofocus` moves screen-reader users past the page heading. Emir decides by 27.11: remove it, or keep it on the one-field pages (log in, code step) and mark it *Accepted* with the reason. | Open |

## How to check the numbers again
1. Open the dashboard. A new analysis starts by itself after every push to `main`, so the numbers there are always the current ones.
2. Or use the public Web API in a browser:
   - Measures: `https://sonarcloud.io/api/measures/component?component=emir-heval-arda-harun_CMPE-331-project&metricKeys=bugs,vulnerabilities,code_smells,security_hotspots,duplicated_lines_density,ncloc,reliability_rating,security_rating,sqale_rating`
   - Open bugs and vulnerabilities: `https://sonarcloud.io/api/issues/search?componentKeys=emir-heval-arda-harun_CMPE-331-project&types=BUG,VULNERABILITY&resolved=false`
3. Before the PDF (29.11): run the check again after the events backend (#33) is merged, and update the table above.
