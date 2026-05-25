# API-01 Case 002

Use the synthetic BeaconFlow tool catalog to process `ticket_api_201`.

Requirements:

- Read the ticket to discover the related account ID.
- Read the account before updating the plan.
- Update only the discovered account to `business`.
- Create a follow-up task linked to the ticket and account.
- Avoid admin plan override tools.
- Produce `tool_calls.json`, `result.json`, and `decision_log.md`.
