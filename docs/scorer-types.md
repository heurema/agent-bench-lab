# Scorer Type Contracts

Agent Bench Lab scorers should be built from reusable scorer contracts instead of one-off
task-family logic whenever possible.

Every score result should still normalize into the public score record format:

```text
score
success
pass_threshold
components
policy_violations
errors
metadata
```

## First-Class Scorer Types

| Type | Purpose | Typical inputs | Public vs private config | Example task families | Common failure modes |
|---|---|---|---|---|---|
| `artifact_exact` | Check required files and exact text/bytes/paths | artifacts, allowed file list | public file contract; private forbidden files or hidden probes | IF, DATA, DOC, SUP | missing files, extra files, wrong names |
| `schema_contract` | Validate JSON/YAML/CSV shape and required fields | artifact, schema, field rules | public schema; private hidden required fields if needed | IF, DATA, API | invalid JSON, missing keys, wrong types |
| `numeric_metric` | Compare numeric values with exact or tolerance rules | metrics artifact, expected values | public smoke values; private hidden expected metrics | DATA, OFFICE, API | rounding drift, wrong aggregation, boundary errors |
| `state_diff` | Compare final environment state to expected state | DB state, API state, filesystem state | public state checks; private hidden state diffs | APP, WEB, SUP, API | partial updates, wrong row, stale state |
| `claim_rubric` | Check factual claims, citations, and unsupported statements | report, citations, source pack | public rubric examples; private hidden labels/rubric | DOC, DATA, RSR, SUP | unsupported claims, missing citations, hallucinated facts |
| `trace_policy` | Check tool-use and action policy from traces | trace events, tool calls, policy rules | public policy shape; private hidden policy exceptions | API, SEC, MCP-like tasks | forbidden tool use, unsafe order, missing audit trail |
| `security_leak` | Detect leakage, exfiltration, or prompt-injection failure | artifacts, trace, canary config | public leak patterns; private canaries and tripwires | SEC, PRIV, SUP, API | leaked labels, copied hidden text, unsafe disclosure |
| `cost_latency` | Score budgets and efficiency diagnostics | run metadata, trace timing, cost fields | public budgets; private customer-specific budgets | all families | too many calls, timeout, excessive cost |
| `mutation_robustness` | Compare performance across variants and mutations | paired scores, mutation metadata | public mutation examples; private hidden variants | IF, DATA, DOC, SUP | brittle prompt, overfit public case, unstable output |

## Contract Requirements

Each scorer type should define:

- purpose;
- accepted inputs;
- expected outputs;
- public config fields;
- private config fields;
- component names;
- policy violation semantics;
- error semantics;
- feedback redaction rules.

Public config can describe the artifact shape and visible examples.
Private config can hold protected expected values, hidden labels, thresholds, canaries, or private
rubrics. Private config must not be committed to the public tree.

## Primary And Secondary Oracles

Every task family should have one mandatory primary oracle and optional secondary diagnostics.

Examples:

| Family | Primary oracle | Secondary diagnostics |
|---|---|---|
| IF-01 | `artifact_exact` + `schema_contract` | `mutation_robustness`, `cost_latency` |
| DATA-01 | `numeric_metric` + `schema_contract` | `claim_rubric`, `security_leak` |
| DOC-01 | `claim_rubric` with audited labels | `schema_contract`, `trace_policy` |
| SUP-01 | `state_diff` or exact labels | `claim_rubric`, `security_leak` |
| API-01 | `state_diff` + `trace_policy` | `cost_latency`, `security_leak` |

## Decision-Grade Graduation Criteria

A task family can be marked decision-grade only if:

1. The primary oracle is deterministic or audited.
2. Public synthetic examples exist.
3. Private holdout strategy is documented.
4. Mutation strategy is documented.
5. Scorer output uses the normalized score record.
6. Agent/scorer/runner/consumer visibility boundary is documented.
7. Feedback redaction policy is documented.
8. Exploit or leak smoke tests exist when relevant.
9. Versioning and changelog policy exists.
10. Repeatability is measured or explicitly planned.

Public examples are not final evaluation. They prove the task shape, scorer shape, and local smoke
loop. Decision-grade comparison needs private holdouts or protected bundles.

## DATA-01 Preview

DATA-01 should use these contracts:

- `schema_contract` for `metrics.json`;
- `numeric_metric` for expected values and tolerances;
- `claim_rubric` for factual claims in `report.md`;
- `schema_contract` and `artifact_exact` for `chart_spec.json`;
- `security_leak` or canary checks for private bundles when relevant.

That keeps DATA-01 from becoming a custom scorer shape and makes it a reusable pattern for
spreadsheet, reporting, and customer-data-style task families.
