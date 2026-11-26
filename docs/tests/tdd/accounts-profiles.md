# TDD evidence – Accounts, profiles and database (UC-01, UC-02, UC-03)

**Author:** Heval Hüseyin Demir · **Date:** 26.11.2026 · Part of the Software Testing Report, accounts section ([`docs/testing/accounts_profiles_test_section.md`](../../testing/accounts_profiles_test_section.md)). Tasks 3.1 and 3.2.

This page shows, with commits and CI runs that anyone can open, that the account and profile code was written **against requirement tests that already existed and failed**, and that the same tests passed once the code was merged (red → green).

## 1. Requirement tests were written before the code

| Date | Commit | What happened |
|---|---|---|
| 17 Oct 2026 | `333c49a` (PR #5, Requirement Analysis Report) | The requirement tests [`tests/test_uc01_register_and_verify.py`](../../../tests/test_uc01_register_and_verify.py) (5 tests), [`tests/test_uc02_login.py`](../../../tests/test_uc02_login.py) (3), [`tests/test_uc03_manage_profile.py`](../../../tests/test_uc03_manage_profile.py) (2) and the two NFR-03 tests in [`tests/test_nfr.py`](../../../tests/test_nfr.py) are written together with the use cases. `AuthService` and `ProfileService` are only skeletons: every method raises `NotImplementedError`, so all 12 tests fail (red). |
| 19 Nov 2026 | `6afea71` (PR #17) | `AuthService.get_user` and `require_role` with a `UserRepository` (NFR-04). The 12 tests still fail, because registering still raises `NotImplementedError`. |
| 20 Nov 2026 | `bdb0e34`, `62d00d5` (PR #23) | Password hashing, the rest of `UserRepository`, and register, verify, new code and log in in `AuthService` (UC-01, UC-02). |
| 20 Nov 2026 | `ce7d97f` (PR #24) | `ProfileService` with `ProfileRepository` (UC-03). |

So the tests that describe UC-01 to UC-03 are about **five weeks older** than the code that satisfies them.

## 2. Red → green on `main`, recorded by CI
CI (GitHub Actions) runs the whole suite on every push to `main` since #9 (17.11.2026). The runs show the same 12 tests failing with `NotImplementedError` until the account and profile code was merged, and passing right after:

| CI run | Commit on `main` | Whole suite | The 12 tests of UC-01 to UC-03 and NFR-03 |
|---|---|---|---|
| [44084821901](https://github.com/emir-heval-arda-harun/CMPE-331-project/actions/runs/44084821901), 17.11 | `7e0e4c9` (#9, first CI run) | 39 failed | **red:** all 12 fail with `NotImplementedError` |
| [44537743110](https://github.com/emir-heval-arda-harun/CMPE-331-project/actions/runs/44537743110), 19.11 | `1983514` (after #17) | 51 failed, 144 passed | **red:** all 12 fail with `NotImplementedError` |
| [44751221424](https://github.com/emir-heval-arda-harun/CMPE-331-project/actions/runs/44751221424), 20.11 | `772bd17` (just before #23 and #24) | 51 failed, 164 passed | **red:** all 12 fail with `NotImplementedError` |
| [44799388585](https://github.com/emir-heval-arda-harun/CMPE-331-project/actions/runs/44799388585), 20.11 | `0e4df7b` (after #23 and #24) | 36 failed, 231 passed | **green:** all 12 pass |

The whole suite went from 51 to 36 failures: the 12 tests above, and the 3 facility requirement tests that only needed a working `register` (see the [facilities TDD evidence](facilities.md)). The 36 that were left are the event tests (`EventService` skeleton, task 3.4); they passed after #33 (23.11). The run of `88e93e1` (#23 alone) was cancelled by the next push, so the first green run is the one after #24.

## 3. A test that caught a defect first
**Turkish capital İ (BR-14, defect 1 of the section, AI mistake case 1).** In the review of #24, Emir found that `"İngilizce kulübü"` was stored as `"i̇ngilizce kulübü"` (an `i` plus a combining dot), so it and `"ingilizce kulübü"` became two interests. The fix (`c7de164`) came with the test `test_turkish_capital_i_becomes_a_plain_i`. Its check, run on the function `_clean_interests` of both versions:

| Code of | Result of `_clean_interests(["İngilizce kulübü", "ingilizce kulübü", "İSTANBUL"])` | Test |
|---|---|---|
| `ce7d97f` (before the fix) | `["i̇ngilizce kulübü", "ingilizce kulübü", "i̇stanbul"]` | **red** |
| `c7de164` (the fix) | `["ingilizce kulübü", "istanbul"]` | **green** |

Run on 26.11.2026 with Python 3.13. The function was taken from each commit and run on its own, because the rest of the package needs the database libraries.

## 4. Honest limits
- The unit tests (`test_auth_accounts.py`, `test_auth_roles.py`, `test_profiles.py`) and the database tests were committed **in the same commit** as their code (`6afea71`, `bdb0e34`, `62d00d5`, `ce7d97f`). Git does not show which lines were typed first inside one commit. The test-first evidence of this part is the requirement tests of sections 1 and 2, which are older than the code and failed until it was merged.
- The limits from the penetration test (#55: P1, P2, P3, P6, P7) were written by Harun; their tests are in the same commits as the code.

## 5. How to repeat
- **Section 2:** open the CI runs above, job *Tests (pytest)*, step "pytest", and look for `tests/test_uc01`, `test_uc02`, `test_uc03` and `test_nfr03` in the short test summary. Or check out each commit and run:
  ```bash
  python -m pytest tests/test_uc01_register_and_verify.py tests/test_uc02_login.py tests/test_uc03_manage_profile.py tests/test_nfr.py -k "uc0 or nfr03"
  ```
  On `772bd17` this gives 12 failed (`NotImplementedError`); on `0e4df7b` it gives 12 passed.
- **Section 3:** check out `ce7d97f` and `c7de164` and run `python -m pytest tests/test_profiles.py -k turkish` with the test file of `c7de164` (`git show c7de164:tests/test_profiles.py > tests/test_profiles.py`).
