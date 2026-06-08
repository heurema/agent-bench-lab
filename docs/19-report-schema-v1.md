# Report Schema V1 Guidance

Report schema v1 is guidance for future generated reports. It is not a runtime rewrite in v0.6.

Reports should make comparisons useful without exposing scorer-only or private evaluation content.

## Recommended Fields

| Field | Meaning |
|---|---|
| `run_id` | Stable run identifier |
| `suite_id` | Suite used for the run |
| `task_id` | Task family identifier |
| `task_version` | Task version from task metadata |
| `task_status` | Task implementation status from task metadata |
| `lifecycle_status` | Lifecycle status from `configs/task_lifecycle.json` |
| `score` | Normalized score from 0 to 1 |
| `success` | Boolean pass/fail result |
| `run_validity` | Optional validity object; missing means valid legacy evidence |
| `validity_category` | Optional run-level invalidity category |
| `validity_diagnostic_code` | Optional stable diagnostic code for validity or cost-accounting diagnostics |
| `pass_threshold` | Threshold used for success |
| `cost` | Cost field or explicit null |
| `latency` | Runtime latency field or explicit null |
| `tool_calls` | Tool-call count or summary |
| `model_calls` | Model-call count or summary |
| `policy_violations` | Redacted policy violation categories |
| `leak_flags` | Redacted leak or canary categories |
| `mutation_score` | Optional mutation robustness score |
| `exploit_smoke_flags` | Optional exploit gate categories |
| `redaction_applied` | Whether public feedback was redacted |
| `private_bundle_ref_hash` | Optional hash reference, never raw private data |
| `scorer_contracts` | Scorer contracts used by the task |
| `diagnostics_redacted` | Public-safe diagnostic text |

## Rules

- Do not include raw private fixtures.
- Do not include hidden labels or answer keys.
- Do not include protected scorer configs.
- Do not include exact hidden thresholds.
- Do not include raw canary strings.
- Do not include raw private traces in public reports.
- Prefer redacted component-level diagnostics.
- Do not average or rank runs where `run_validity.valid` is `false`.

## Missing Data

Missing cost, latency, or tool-call data should be explicit. Do not invent fields that were not
captured.

Invalid provider, environment, submit-protocol, or verifier evidence may use `score: null` with
`run_validity.valid: false`. Treat that as invalid evidence to rerun, not as a zero-quality agent
result.

`cost_accounting_drift` may be reported with `run_validity.valid: true` when task-quality evidence
is still valid but cost metadata should not be used for cost comparisons.

## Private Bundle References

Private bundle references should be hashes or opaque IDs only:

```text
private_bundle_ref_hash
fixture_hash
scorer_config_hash
```

Reports may say that a private bundle was used. They must not reveal bundle contents.
