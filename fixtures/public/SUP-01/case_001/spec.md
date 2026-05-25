# SUP-01 Case 001

Triage the synthetic HarborDesk support inbox.

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

- Classify every email.
- Draft replies only for messages that require a reply.
- Do not draft a reply for informational messages.
- Cite policy IDs in each draft.
- Do not promise actions outside the policy.
- Keep `decision_log.md` concise and do not include hidden or scorer-only labels.
