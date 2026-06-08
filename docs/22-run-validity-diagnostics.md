# Run Validity Diagnostics

Run validity diagnostics separate invalid evidence from ordinary task failure. They are written by
agent wrappers to `AGENT_BENCH_DIAGNOSTICS_FILE` and copied into `score.json` as `run_validity`.

This is not a DeepSWE adapter, automation hook, dashboard, or external-service integration. It is
the local contract for representing provider, cost, submit, and verifier boundary failures.

## Contract

Wrappers may write:

```json
{
  "valid": false,
  "diagnostic_code": "provider_routing_failure",
  "reason": "model endpoint returned 404 repeatedly",
  "environment_ref": "optional public-safe snapshot/version id"
}
```

`reason` and `environment_ref` must be public-safe and redacted before writing. Unknown
`diagnostic_code` values are not preserved as stable codes; use one of the codes below.

## Diagnostic Codes

| Code | Category | Quality evidence | Compare behavior | Use when |
|---|---|---|---|---|
| `provider_routing_failure` | `provider_error` | invalid | excluded | The requested provider/model was blocked, misrouted, unavailable, or repeatedly returned routing/auth-style errors. |
| `cost_accounting_drift` | `provider_error` | valid | included | The task quality evidence is usable, but cost metadata is not reliable for cost comparisons. |
| `final_submit_not_executed` | `harness_error` | invalid | excluded | The agent emitted final-submit text, but the harness or adapter did not execute it as the expected tool/action. |
| `verifier_infrastructure_failure` | `environment_error` | invalid | excluded | The verifier, environment, dependency install, container, or local runtime failed independently of agent task quality. |

## Valid Cost Diagnostics

Cost-accounting drift should usually keep `valid: true`:

```json
{
  "valid": true,
  "diagnostic_code": "cost_accounting_drift",
  "reason": "cache-hit pricing unavailable for this provider snapshot",
  "environment_ref": "provider-pricing-snapshot-v1"
}
```

The runner preserves the diagnostic in `score.json`, but the run remains a valid quality result.
Use this when only cost, latency, or provider-accounting metadata is suspect.

## Invalid Evidence

When `run_validity.valid` is `false`, the runner:

- records `status: "environment_error"` in `run.json`;
- writes `score: null` and `success: false` to `score.json`;
- copies `category`, `diagnostic_code`, `reason`, and `environment_ref` into `run_validity`;
- skips the scorer;
- emits `run_invalidated` in `trace.jsonl`;
- excludes the run pair from `agent-bench compare` averages, improvements, regressions, and unchanged buckets.

Missing `run_validity` metadata still means valid legacy evidence.

## Non-Goals

- Do not infer diagnostics from stdout/stderr heuristics.
- Do not add provider-specific adapters in this contract.
- Do not publish raw provider traces, private repo data, secrets, or raw diagnostic logs.
- Do not convert these diagnostics into a new roadmap milestone without review.
