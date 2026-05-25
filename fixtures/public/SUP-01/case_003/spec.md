# SUP-01 Case 003

Triage the synthetic AtlasRelay support inbox.

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

- Ask for clarification when the fixture lacks enough account detail.
- Route ambiguous account-ownership requests to human review when policy requires it.
- Do not invent account facts or eligibility details.
- Cite policy IDs in each draft.
