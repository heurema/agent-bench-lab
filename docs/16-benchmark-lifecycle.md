# Benchmark Lifecycle

Agent Bench Lab task families move through explicit lifecycle statuses. The status is about
benchmark readiness, not model quality.

## Statuses

| Status | Meaning | Suitable use |
|---|---|---|
| `experimental` | The task exists, but the oracle, fixtures, or tests may still be starter-grade. | Demos, authoring examples, early scorer work |
| `decision-grade` | The task has a deterministic or audited primary oracle, public synthetic examples, tests, mutation strategy, private holdout guidance, normalized scores, and redacted feedback. | Serious comparisons when paired with private holdouts |
| `verified` | The task has passed an additional maintainer audit, scorer loophole review, solvability check, mutation smoke, exploit smoke, and changelog review. | High-confidence repeated evaluation |
| `deprecated` | The task is replaced, flawed, stale, or no longer maintained. | Historical comparison only |

No task family is `verified` in v0.6. Verification is a later audit level.

## Experimental

Experimental means:

- task metadata exists;
- public examples may exist;
- the scorer may be incomplete or sample-grade;
- hidden checks and mutation coverage may be planned only;
- the task is not suitable for decision-grade comparison.

Experimental task families can still be useful as templates, but they should not be marketed as
reliable evaluation signals.

## Decision-Grade

Decision-grade means:

- primary oracle is deterministic or audited;
- public synthetic cases exist;
- private holdout strategy is documented;
- mutation strategy is documented;
- scorer output uses normalized score records;
- redacted feedback is supported;
- leak gates pass;
- tests cover pass and fail cases;
- no live dependency is required unless the environment is snapshotted or replayed.

Decision-grade public cases are still examples and smoke tests. Final comparisons need private
holdouts or protected bundles outside the public repo.

## Verified

Verified means all decision-grade criteria are met, plus:

- maintainer audit completed;
- scorer loophole review completed;
- public cases are solvable;
- mutation smoke passes;
- exploit smoke passes or has an explicit not-applicable justification;
- changelog and version policy are clean;
- known limitations are documented.

Verification should be conservative. It is better to keep a task family decision-grade than to mark
it verified without an audit trail.

## Deprecated

Deprecated means the task family should not be used for new comparisons because it is:

- replaced by a better task family;
- known to be flawed;
- stale or unsupported;
- incompatible with current scorer contracts.

Deprecated tasks should keep enough metadata for historical interpretation.

## Config

Lifecycle metadata lives in:

```text
configs/task_lifecycle.json
```

Validate it with:

```bash
make lifecycle-check
```
