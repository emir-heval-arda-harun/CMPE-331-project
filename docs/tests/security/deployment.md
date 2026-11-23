# Penetration Test: Deployment and CI

Owner: Onur Alioğlu (tasks 3.7 CI/CD, 4.4 Deployment). This is the deployment part of the penetration tests for review item D (#34). Emir tests the application itself through the web UI. The automated scans are described in [`../non-func-tests/security_scans.md`](../non-func-tests/security_scans.md).

**Date:** 23.11.2026 · **Code:** `main` at `cf68ee0` plus #36

## Scope
| Area | What was tested |
|---|---|
| Repository | Secrets in the current files and in the **whole git history**: passwords, keys, tokens, `.env` files, database URLs |
| GitHub Actions | How the deploy secret is stored and used, job permissions, triggers (forks, other branches), third-party actions |
| Render configuration | `render.yaml`: secrets, `SECRET_KEY`, auto-deploy, the database connection |
| Running app (production settings) | gunicorn started with the same start command as on Render. Checked: debug console, sensitive paths, error pages, CSRF, cookie flags, security headers |
| Render dashboard | Not tested by the owner of this report, who has no access. A checklist for the account owner is in [Checks for the account owners](#checks-for-the-account-owners) |

Rules: only our own code and a local copy of the app were attacked. The live site was only checked from outside with harmless requests (see [Live site](#live-site)).

## Results
| # | Finding | Severity | Status |
|---|---|---|---|
| D1 | No secrets in the repository or in its history | — | ✅ Pass |
| D2 | Deploy secret is stored as an *environment* secret and used in one job only | — | ✅ Pass |
| D3 | Deploy secret could be read from another branch if the `production` environment is not limited to `main` | Medium | ⚠️ Check in GitHub settings (owner: Onur) |
| D4 | Third-party GitHub Actions were referenced by tag (`@v4`), not by commit SHA | Low | ✅ Fixed in this PR |
| D5 | Production app: no debug console, no stack traces, sensitive paths not served, CSRF enforced, cookie `Secure; HttpOnly; SameSite=Lax` | — | ✅ Pass |
| D6 | No security headers (HSTS, `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) | Medium | ⏳ Open PR #46 |
| D7 | Free Render PostgreSQL accepts connections from the whole internet by default (password protected) | Low | ⚠️ Check on Render (owner: Harun) |
| D8 | Demo accounts on the live site use publicly documented e-mail addresses. A demo password once committed in `scripts/run_demo.py` (removed on 18.11) must not be used on the live site | Low | ⚠️ Check on Render (owner: Harun) |
| D9 | `Server: gunicorn` response header (no version number) | Info | Accepted |

No High or Critical findings.

### D1 Secrets in the repository: pass
- **Method:**
  - [`detect-secrets`](https://github.com/Yelp/detect-secrets) 1.5.0 was run on all files.
  - Every added line in the full history (`git log --all -p`) was searched for: database URLs with passwords, private keys, AWS, GitHub, Brevo and SendGrid tokens, Render deploy hooks, and `PASSWORD`/`SECRET_KEY` assignments.
  - Every file name ever committed was checked for `.env`, `.pem`, `.key`, `id_rsa` and `credentials`.
- **Result:** 0 real secrets. All 23 `detect-secrets` hits were reviewed by hand and are false positives:
  - test passwords such as `S3cure-pass!` in `tests/` and `secret_key="test"`;
  - placeholders such as `choose-a-password` in `docs/database/README.md`, `PASSWORD` in `.env.example`, and `secret` in `tests/test_wiring.py`;
  - `pytest` and `ruff` cache tags.
- The only `.env*` file ever committed is `.env.example`, which has no values. `.gitignore` excludes `.env`, `.env.*`, `*.pem` and `*.key`.
- In history: `scripts/run_demo.py` had a fixed demo password from 17.11 to 18.11 (`2f16124` → removed in `d7da9f3`). It is only used by the local in-memory demo. See D8.
- The CI test database password added on 21.11 (#36) was removed again on 22.11. The CI database now uses `trust` authentication, which needs no password.

### D2, D3 Deploy secret in GitHub Actions
- `RENDER_DEPLOY_HOOK_URL` is an **environment secret** of `production` (since 23.11). Only the `deploy` job uses the `production` environment.
- `deploy` runs only on `push` to `main`, after lint, tests and the security scan pass.
- The workflow has `permissions: contents: read` and no `pull_request_target`. Pull requests from forks therefore get no secrets and only a read-only token.
- The secret is only passed to `curl` through an environment variable. It is never printed, and GitHub masks it in logs.
- **D3 (Medium):** `if: github.ref == 'refs/heads/main'` is part of the workflow file, and anyone who can push a branch can edit that file. Without a *deployment branch rule*, a changed workflow on another branch could use `environment: production` and send the hook URL elsewhere. The protection must be in the repository settings, not in the file. **To check:** *Settings → Environments → production → Deployment branches and tags* must be **Selected branches and tags: `main`**. The hook URL can only start a deploy of `main` and cannot change code, so the impact is limited.

### D4 Actions pinned to commit SHAs: fixed
A tag such as `actions/checkout@v4` can be moved to different code by whoever controls the action. All three actions now use the commit that the tag points to today, with the tag kept as a comment:

| Action | Commit |
|---|---|
| `actions/checkout` v4 | `11d5960a326750d5838078e36cf38b85af677262` |
| `actions/setup-python` v5 | `a26af69be951a213d495a4c3e4e4022e16d87065` |
| `actions/upload-artifact` v4 | `ea165f8d65b6e75b540449e92b4886f43607fa02` |

The SHAs were read with `git ls-remote https://github.com/<action> refs/tags/<tag>`. The Python tools in the security job were already pinned (#36). The two remaining `pip install` lines are covered by the lock-file work in #39.

### D5 App with production settings: pass
Started exactly like on Render, `gunicorn --chdir src "campusevent.web:create_web_app()"` with a random `SECRET_KEY` and the default `SESSION_COOKIE_SECURE=1`:

| Request | Result |
|---|---|
| `/console` (Werkzeug debugger) | 404: gunicorn does not run Flask's debug mode |
| `/.env`, `/.git/config`, `/static/`, `/static/../src/campusevent/app.py` | 404: only files inside `static/` are served, with no directory listing and no path traversal |
| Unknown page | Our own error page; no traceback and no Werkzeug or Python details in the body (the 500 handler also shows only a generic message and writes the details to the server log) |
| `/admin/requests`, `/facilities` without login | 302 to the login page |
| `POST /login` without CSRF token | 400 |
| Session cookie | `Secure; HttpOnly; Path=/; SameSite=Lax` |

`SECRET_KEY` is created by Render (`generateValue: true`) and stays the same across restarts. Without one, the app warns in the log and uses a random key. In `render.yaml`, the `SMTP_*` values are `sync: false`, so they are entered on Render and never kept in the repository. `DATABASE_URL` comes from the database resource (`fromDatabase`). `autoDeploy: false`, so only a green CI build on `main` reaches the live site.

### D6 Security headers: open
No response sets HSTS, `Content-Security-Policy`, `X-Frame-Options`/`frame-ancestors`, `X-Content-Type-Options` or `Referrer-Policy`. Without them, the pages can be framed (clickjacking), and HTTPS is not pinned in the browser. PR #46 adds these headers. After it is merged, check them on the live site with the commands below.

## Checks for the account owners
The owner of this report has no Render access, so these items are for the people who have it.

**Render (Harun, who set up the site on 22.11):**
- [ ] **D7:** `campusevent-db` → *Networking / Access Control*: remove `0.0.0.0/0`, or allow only the IP of the computer that runs `seed_db.py`, and only while it runs. The web service connects through Render's internal network and does not need outside access.
- [ ] **D8:** The demo password on the live site was created randomly by `seed_db.py` (or set through `CAMPUSEVENT_DEMO_PASSWORD`). It must not be the old value from `scripts/run_demo.py` history. If it is, run `seed_db.py --reset` with a new random password.
- [ ] *Environment* of the web service: `SECRET_KEY` is set (generated), `SMTP_*` are empty, and there are no other variables with secrets that are not needed.
- [ ] Account security: only team members are in the Render workspace, and two-factor authentication is on.

**GitHub (Onur, repository admin):**
- [ ] **D3:** *Settings → Environments → production → Deployment branches and tags* is set to **`main` only**.
- [ ] *Settings → Secrets and variables → Actions*: no repository-level copy of `RENDER_DEPLOY_HOOK_URL`, only the environment secret.
- [ ] Every admin uses two-factor authentication on GitHub.

## Live site
The live site could not be reached from the environment where this report was made. Run these from any computer and paste the output here:
```bash
# HTTP must redirect to HTTPS
curl -sI http://campusevent-86ax.onrender.com/login | head -3
# Cookie flags and security headers (after #46)
curl -sI https://campusevent-86ax.onrender.com/login
# No debug console, no files outside static/
curl -s -o /dev/null -w "%{http_code}\n" https://campusevent-86ax.onrender.com/console
curl -s -o /dev/null -w "%{http_code}\n" https://campusevent-86ax.onrender.com/.env
```
Expected results:
- The HTTP request redirects to `https://` with status 301 or 308.
- The `Set-Cookie` header has `Secure; HttpOnly; SameSite=Lax`.
- After #46, the response has `Strict-Transport-Security` and `Content-Security-Policy`.
- `/console` and `/.env` return 404.
