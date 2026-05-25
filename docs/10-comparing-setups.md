# Comparing Setups

Use paired comparison to answer whether setup B became better or worse than setup A.

The comparison unit is the same task and same case scored with the same scorer:

```text
baseline / IF-01 / case_001
candidate / IF-01 / case_001
```

Only paired scores are included in averages. Missing scores are reported separately.

```bash
agent-bench compare \
  --baseline runs/baseline \
  --candidate runs/spec_first \
  --out reports/compare_baseline_vs_spec_first.md \
  --csv reports/compare_baseline_vs_spec_first.csv
```

The report includes:

- total paired tasks compared;
- baseline and candidate average score;
- score delta;
- success counts;
- improvements, regressions, and unchanged tasks;
- policy violations;
- missing scores;
- a per-task table.

Run the local smoke flow:

```bash
make smoke
make compare-smoke
```

Visible public fixtures are useful for validating the runner and report format. Decision-grade
evaluation needs private holdout cases, private seeds, and hidden answers kept outside the public
repository.

## Examples beyond coding agents

Paired comparison works the same across domains:

```text
support_agent_without_memory / INBOX-01 / case_101
support_agent_with_memory    / INBOX-01 / case_101

ticket_agent_old_policy      / TICKET-01 / case_204
ticket_agent_new_policy      / TICKET-01 / case_204

spreadsheet_agent_basic      / DATA-01 / case_303
spreadsheet_agent_tool_rich  / DATA-01 / case_303
```

The rule is always:

```text
same task family
same case
same scorer
different setup
```

Consumer applications should consume Agent Bench Lab task families and scorer outputs rather than defining parallel benchmark logic.

## Feedback Safety

Comparison reports should identify regressions and failure categories without revealing hidden
labels, answer keys, canary strings, private thresholds, or exact hidden rubric text.

Prefer redacted diagnostics such as:

- `numeric total is incorrect`;
- `unsupported claim found in report`;
- `policy classification failed`.

Avoid feedback such as:

- `the correct hidden label is urgent_refund`;
- `hidden row HONEY_482 triggered`;
- `private threshold is 0.87`.

See [Reporting and feedback](reporting-and-feedback.md).
