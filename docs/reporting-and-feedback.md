# Reporting And Feedback

Benchmark feedback should be useful without revealing hidden evaluation content.

Reports may include scores, deltas, component names, broad failure categories, policy violations,
latency, cost, and tool-call counts. Reports must not reveal private fixtures, hidden labels,
answer keys, private thresholds, canary strings, protected scorer configs, or exact hidden rubric
text.

## Feedback Boundary

Use three levels:

| Level | Audience | Content |
|---|---|---|
| Public summary | public repo, public docs | aggregate scores, public smoke examples, no private details |
| Consumer report | consumer application, authorized user | redacted component failures and safe diagnostics |
| Scorer-private report | scorer/runtime owners | hidden labels, answer keys, canary hits, private rubric detail |

Do not give scorer-private reports to agents. Do not use feedback that lets an agent reconstruct
hidden labels, thresholds, or private holdout contents.

## Good Feedback

- `numeric total is incorrect`
- `unsupported claim found in report`
- `policy classification failed`
- `required artifact is missing`
- `chart series does not match expected labels`
- `exfiltration attempt detected`

## Bad Feedback

- `correct answer was refund_escalation_high_priority`
- `hidden row HONEY_482 triggered`
- `private threshold is 0.87`
- `expected customer was ACME_PRIVATE_17`
- `the hidden label for case_204 is urgent_security_refund`
- `the canary string was copied into the final answer`

## Report Fields

Use normalized run and score fields where possible:

```text
score
success
pass@1
pass^k
latency_seconds
cost_usd
tool_calls
model_calls
mutation_score
leak_flags
policy_violations
```

Not every field is required in v0. Missing cost or latency data should be explicit, not silently
invented.

## Redaction Rules

Redacted feedback should:

- name the failing component;
- describe the class of error;
- avoid exact hidden values;
- avoid private thresholds;
- avoid hidden labels;
- avoid canary strings;
- avoid revealing which hidden row, customer, source, or fixture caused the failure.

Scorer-private reports can be more specific, but they must stay outside public repositories and
outside agent-visible context.

## Lightweight Public Gate

The repository includes a small redaction utility for public-facing generated reports.

This utility is a safety gate, not a private evaluation implementation and not a full data-loss
prevention system. It catches obvious scorer-only strings such as answer-key hints, hidden labels,
private thresholds, canary identifiers, raw traces, and protected scorer config references before
they appear in public Markdown or CSV reports.

Private scorer-only content should still be isolated at the source. Do not pass hidden labels,
answer keys, private rubrics, customer data, or protected scorer configs into public reports and
then rely on redaction to clean them up.
