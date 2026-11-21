# Security Scans (static analysis and dependency audit)

Owner: Onur Alioğlu (CI/CD). Part of the Software Testing Report (task 4.1), review item D "Security tests" (#34) and NFR-03 Security.

These are automated checks that run on every push and every pull request. Other security tests, such as manual or penetration tests against the running site, are separate.

## What runs in CI
Job **Security scan (bandit, pip-audit)** in `.github/workflows/ci.yml`. The deploy job needs it, so a failing scan also stops a deploy.

| Tool | What it checks | The build fails when |
|---|---|---|
| [bandit](https://bandit.readthedocs.io/) | Static analysis of our own code in `src/`: shell injection, `eval`, weak hashes, hard-coded secrets, unsafe deserialisation, missing timeouts and more | a finding has **Medium or High** severity (`bandit -r src -ll`) |
| [pip-audit](https://pypi.org/project/pip-audit/) | Known vulnerabilities (PyPI advisory database and OSV) in the packages of `requirements.txt`, the ones installed on Render | any known vulnerability is found |

Results:
- Shown on the run page (*Summary*).
- The full bandit report, including Low findings, is in the build artifact `security-report` (`bandit-report.json`).

## Run it locally
```bash
pip install bandit pip-audit
bandit -r src            # all findings
bandit -r src -ll        # only Medium and High (the CI gate)
pip-audit -r requirements.txt
```

## Results (21.11.2026, `main` + this pull request)
- **pip-audit:** no known vulnerabilities in `requirements.txt`.
- **bandit:** 2295 lines scanned, **0 High, 0 Medium, 2 Low**. Both Low findings were reviewed and are false positives:

| ID | Location | Finding | Why it is not a problem |
|---|---|---|---|
| B107 | `src/campusevent/notifications.py:45` | "Possible hardcoded password: ''" | `password: str = ""` is only the default value of the `SmtpEmailSender` parameter. The real password comes from the `SMTP_PASSWORD` environment variable (`create_app_from_env`) and is never in the code. |
| B105 | `src/campusevent/web/common.py:14` | "Possible hardcoded password: 'token'" | `TOKEN_KEY = "token"` is the *name* of the session field that holds the login token, not a secret. The token itself is random and signed with `SECRET_KEY`. |

They are documented here instead of being hidden with `# nosec`, so every run still shows them.

## Checking that the gates work
Before enabling the job, both gates were tried locally with code that is known to be bad:
- **bandit:** a file with `subprocess.run(cmd, shell=True)` was reported as **B602, High severity** and `bandit -ll` exited with code 1.
- **pip-audit:** a requirements file with `jinja2==3.1.2` (an old version) reported 4 known vulnerabilities (fixed in 3.1.4–3.1.6) and exited with code 1.

Neither example was committed.
