@'

\# Events Non-Functional Tests



\## NFR-02 - Search Performance on Large Datasets

\- Test case: test\_nfr02\_search\_is\_fast\_with\_1000\_open\_events in tests/test\_nfr.py (outside the 56 unit/UC count).

\- PostgreSQL benchmark (#52 -> #58): Query duration on PostgreSQL improved from 2.1-3.4 s before #58 to 0.33-0.56 s after fixing N+1 queries in #58.



\## NFR-04 - Authorization and Ownership Enforcement

\- test\_nfr04\_only\_the\_organizer\_can\_cancel\_an\_event in tests/test\_nfr.py (alongside test\_only\_the\_organizer\_can\_cancel in test\_uc11\_cancel\_event.py) verifies non-organizers cannot cancel an event.

\- test\_nfr04\_only\_an\_admin\_can\_approve\_or\_reject\_event\_requests in tests/test\_nfr.py verifies only admins can approve or reject pending event requests.

'@ | Set-Content -Encoding UTF8 docs\\tests\\non-func-tests\\events.md

