# SUP-01 Case 002

Triage the synthetic LumenQueue support inbox.

Use only:

- `policy.md`
- `customer_profile.json`
- `inbox/*.eml`

Produce:

- `triage.json`
- `drafts.json`
- `escalations.json`
- `decision_log.md`

Requirements:

- Escalate policy exceptions before promising refunds or credits.
- Draft a reply for each message that needs a customer response.
- Cite policy IDs in each draft.
- Do not promise credits, refunds, legal outcomes, or security outcomes unless policy explicitly allows it.
