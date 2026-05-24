# Metrics

## Minimum v0 metrics

| Metric | Meaning |
|---|---|
| success | pass/fail at threshold |
| weighted_score | score from 0 to 1 |
| cost_usd | provider cost, if known |
| latency_ms | end-to-end duration |
| tool_calls | total tool calls |
| failed_tool_calls | invalid or failed calls |
| policy_violations | safety or instruction violations |
| artifact_valid | whether final artifact schema is valid |
| hidden_checks_passed | whether private checks passed |

## Reliability metrics

- `pass@k`: at least one of k attempts succeeds.
- `pass^k`: all k attempts succeed.

For user-facing agents, `pass^k` is often more important than `pass@k` because users need consistency, not one lucky run.

## Cost-aware comparison

A setup is not simply better because it scores higher. It may be worse if it costs much more or takes much longer.

Recommended reporting:

```text
score_delta
cost_delta
latency_delta
tool_call_delta
policy_violation_delta
```
