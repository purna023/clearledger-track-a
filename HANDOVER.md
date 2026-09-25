# Handover

- Name: Mutyala Purna Srivalli
- Email used for this application: purnamutyala239@gmail.com
- Chosen track: Track A — Repair the register
- Why this track: It matches my software/web development experience and gave me an opportunity to debug an existing application, preserve data, and verify changes rather than rewrite it.
- Approximate total time, including setup and handover:  Approximately 3 hours

## Run and verify

Prerequisite: Python 3.10+; no third-party packages.

From this directory:

```text
python -m unittest discover -s tests -v
python app.py reset-demo
python app.py
```

For the supplied existing register, stop the server first and run:

```text
python restore_fixture.py --replace
python app.py
```

The clean test run completed with **10 tests passing**.

The existing-register verification started from 9 invoices, 5 payments, 7 open invoices and INR 3,698.19 outstanding. I then imported one new invoice and one payment, restarted by closing and reopening the database, and verified both the original records and new records remained present. The original unmatched `KEEP-U1` payment remained unmatched.

## What I delivered

I investigated the seeded defects and focused on reliability across import, matching, reporting and browser feedback.

Changes include:
- invoice identity is now idempotent: an identical re-import is skipped; conflicting details are rejected without replacing the original;
- payment matching now uses the required `(customer_id, invoice_number)` identity rather than amount;
- invalid CSV data rows are rejected individually while other valid rows continue processing, with line numbers;
- `open` and `paid` filters now return only their respective statuses;
- money export/reporting preserves two decimal places without float truncation;
- the browser now checks HTTP import failures and displays imported/skipped/rejected counts and rejected line reasons;
- after successful import, the register is refreshed.

### Separate improvement

Added a small invoice search field to the register so the owner can quickly find invoices by customer or invoice number during review. The filtering is client-side and does not change the public API.

## Evidence and limits

Failing-before/passing-after cases included:
- a payment whose amount matched another invoice but whose customer/invoice reference identified a different invoice;
- a mixed-validity import where one invalid row previously aborted the whole import;
- a `0.29` invoice that previously exported as `0.28`;
- the broken `open`/`paid` filters.


The supplied fixture was successfully restored with 9 invoices and 5 payments. The existing register was opened in the browser and the restored records were verified.

Manual verification also covered:
- invoice search using `HARBOR`;
- `open` and `paid` status filters;
- mixed CSV import with valid and invalid rows;
- duplicate re-import handling;
- payment import and unmatched-payment visibility.
- Known limit: I did not add automatic rematching of unmatched payments after a future invoice import because the business rules explicitly place that outside scope.

In a real project I would additionally investigate concurrent writers, larger files, malformed CSV quoting/embedded newlines, and a production-grade audit trail.
## Tools and judgment

I used ChatGPT (GPT-5.6 Luna) to inspect the supplied code, suggest defect hypotheses and regression cases, and review the patch. I did not treat suggestions as proof: I reproduced the seeded behaviours against the original code, then ran the repaired test suite and existing-register/restart checks. A concrete issue caught through verification was amount-based payment matching: a payment for `HARBOR/INV-101` could be attached to another invoice solely because the amounts matched, so the matching rule was changed and tested against the exact customer/invoice identity.
