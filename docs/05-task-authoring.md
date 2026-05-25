# Task Authoring Guide

A good task is not just a prompt. It is a package:

```text
instruction + fixtures + allowed tools + forbidden actions + expected artifact + scorer + trace policy
```

## Task card minimum

Each task needs:

- ID and version;
- category;
- purpose;
- agent role;
- user prompt;
- public fixture paths;
- expected artifact shape;
- scoring rubric;
- hidden/mutation strategy;
- failure modes;
- logging requirements.

## Prefer

- local data;
- synthetic fixtures;
- exact JSON/artifact formats;
- state diff scoring;
- fast tests;
- meaningful hidden checks;
- seeded variants.

## Avoid

- vague tasks with no oracle;
- live websites without snapshots;
- LLM-only scoring as the primary oracle;
- tasks that require private user data;
- hidden answer keys in public repos.

## Non-code task authoring examples

Agent Bench Lab tasks do not need to involve code.

A valid task can be any workflow with a checkable artifact or state change.

| Task type | Fixture examples | Expected artifact/state | Scoring method |
|---|---|---|---|
| Support inbox | synthetic emails, policy docs, customer profile | labels, draft replies, escalation decision | exact label + policy checker |
| Tickets | task board snapshot, product notes | updated tickets, priorities, assignees | board-state diff |
| Docs / knowledge | frozen source pack, query, citation rules | `memo.md`, `citations.json` | factual rubric + citation validation |
| Spreadsheet / data | CSV, XLSX, SQLite, rules | `metrics.json`, `report.md`, `chart_spec.json` | exact values + schema checks |
| Browser workflow | self-hosted app snapshot | final DB/app state | state diff + trace replay |
| Internal API | mock API state, policies | final state + user message | API state diff + policy compliance |
| Customer private check | customer-owned fixtures and rubric | customer-specific artifact | protected scorer bundle |

Avoid writing tasks whose only oracle is "the answer looks good".

## Scorer Contracts

Prefer reusable scorer contracts over family-specific hidden-check formats.

Common contracts include:

- `artifact_exact` for required files, forbidden files, and exact artifact checks;
- `schema_contract` for JSON/YAML/CSV structure;
- `numeric_metric` for exact values and tolerances;
- `state_diff` for database, API, filesystem, or app state;
- `claim_rubric` for factual claims and citations;
- `trace_policy` for tool-use and action policy;
- `security_leak` for canaries, leakage, and exfiltration checks.

See [Scorer type contracts](scorer-types.md).

## Decision-Grade Criteria

A task family is not decision-grade just because public examples pass.

Before marking a family decision-grade, require:

- deterministic or audited primary oracle;
- public synthetic examples;
- private holdout strategy;
- mutation strategy;
- normalized score output;
- documented visibility boundary;
- redacted feedback policy;
- exploit or leak smoke test when relevant;
- versioning and changelog policy.
