# SUP-01 Decision-Grade Pattern

SUP-01 is the first operational/customer-style task-family pattern in Agent Bench Lab.

It evaluates synthetic support inbox triage, policy-grounded draft replies, escalation decisions, and concise decision logging. It is local-first and does not use real inboxes, live SaaS systems, browser workflows, customer data, or an LLM judge as the primary oracle.

## What It Measures

- support email classification;
- priority and reply/no-reply decisions;
- escalation decisions under policy;
- policy-grounded draft replies;
- refusal to promise prohibited refunds, credits, security outcomes, or account changes;
- artifact-contract compliance for `triage.json`, `drafts.json`, `escalations.json`, and `decision_log.md`.

## What It Does Not Measure

SUP-01 does not measure live inbox handling, real customer support quality, provider-specific tool use, browser/SaaS workflows, long-running ticket state, or private customer bundle handling. Those belong in later task families or private holdout bundles.

## Public Fixture Shape

Each public case is synthetic:

```text
fixtures/public/SUP-01/case_001/
  spec.md
  policy.md
  customer_profile.json
  inbox/
    email_001.eml
    email_002.eml
    email_003.eml
  check_config.json
```

Public cases are examples and smoke tests. They intentionally expose public `check_config.json` rules so contributors can understand the scorer. Decision-grade evaluation still needs private holdouts outside the public repo.

## Artifact Contract

`triage.json` lists one triage decision per email:

```json
{
  "triage": [
    {
      "email_id": "email_001",
      "category": "billing",
      "priority": "normal",
      "requires_reply": true,
      "requires_escalation": false,
      "reason_code": "duplicate_charge_review"
    }
  ]
}
```

`drafts.json` contains drafts only for emails that require replies:

```json
{
  "drafts": [
    {
      "email_id": "email_001",
      "draft_subject": "Re: duplicate charge",
      "draft_body": "The billing team will review within two business days.",
      "policy_citations": ["BILLING-REVIEW"],
      "tone": "calm"
    }
  ]
}
```

`escalations.json` contains required escalation decisions:

```json
{
  "escalations": [
    {
      "email_id": "email_101",
      "escalation_team": "billing_escalations",
      "escalation_reason": "service credit above 100 synthetic dollars",
      "required_context": ["250 synthetic dollar credit", "queue outage"]
    }
  ]
}
```

`decision_log.md` records a short operational summary, policy decisions, and human-review items. It must not include hidden labels, answer keys, canaries, protected scorer config, or other scorer-only content.

## Scorer Contracts

SUP-01 maps to existing scorer contract types:

- `artifact_exact`: required files and no-extra-file checks;
- `schema_contract`: `triage.json`, `drafts.json`, and `escalations.json`;
- `claim_rubric`: policy-grounded draft content and prohibited promises;
- `trace_policy`: future tool-use and escalation-rule checks;
- `state_diff`: future inbox or ticket-state mutations;
- `security_leak`: future private canaries and prompt-injection support emails.

The public scorer is deterministic and config-driven. It checks exact labels, reason codes, required policy citations, required escalations, no unknown email IDs, prohibited promises, and decision-log sections.

## Private Holdouts

Private support evaluation should live outside the public repo. A private SUP-01 bundle may include:

- hidden support policies;
- private synthetic inboxes;
- protected expected labels;
- private escalation rules;
- canary messages;
- protected scorer config;
- redacted feedback templates.

The agent-visible task packet should include only the allowed prompt, policy, customer context, and inbox messages. The scorer may receive protected labels and private rules. Public reports should include redacted diagnostics only.

## Mutations

`scripts/create_sup01_mutation.py` creates public-style mutation cases under ignored output paths such as:

```text
artifacts/mutations/SUP-01/case_mutation_001/
```

Mutation cases can rename synthetic entities, reorder emails, shift timestamps, paraphrase policy wording, add distractor informational emails, or change labels through a configured mapping. They are not private holdouts.

## Suite Placement

SUP-01 is intentionally not added to `configs/suites/core.json` by default.

It belongs to:

```text
configs/suites/ops-local.json
```

Core should remain a fast starter suite. Operational/customer-style workflows can grow under `ops-local` without forcing every new task family into core.

## Comparing Setups

Use paired comparison:

```text
support_baseline / SUP-01 / case_001
support_policy_first / SUP-01 / case_001
```

Compare the same case with the same scorer and different agent setups. Public cases are smoke tests; private holdouts are required for final decisions.
