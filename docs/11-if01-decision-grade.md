# IF-01 Decision-Grade Pattern

IF-01 measures strict instruction following and artifact-contract compliance.

It is intentionally small: no browser, no live services, no provider-specific runner, and no LLM
judge. The task asks an agent to read a precise synthetic spec and produce only the required
artifact files.

## What It Measures

- required files are present;
- forbidden files and extra files are absent;
- Markdown sections exist in the required order;
- JSON artifacts are valid and contain required fields;
- forbidden sections and fields are absent;
- required phrases or values are present;
- word, line, bullet, heading, and field limits are respected;
- critical must-not violations cap or zero the score.

## What It Does Not Measure

- broad coding skill;
- browser interaction;
- live tool use;
- research quality;
- subjective writing quality;
- model provider performance outside the artifact contract.

## Public Cases And Holdouts

Public IF-01 cases under `fixtures/public/IF-01/` are examples and smoke tests. They show the
fixture structure and scorer contract:

```text
case_001/
  spec.md
  check_config.json
```

Decision-grade evaluation needs private holdout cases outside the public repo, or under gitignored
local paths. Do not publish hidden cases, hidden expected artifacts, or private failure probes.

## Mutations

`scripts/create_if01_mutation.py` creates safe public-style mutation cases under ignored local
output paths by default. Mutations change harmless details such as entity names, section order, and
numeric limits. They help detect agents that overfit to one visible case instead of reading the
current spec.

## Comparing Setups

Run the same IF-01 cases for two agent configs, then compare their score directories:

```bash
agent-bench compare \
  --baseline runs/baseline \
  --candidate runs/spec_first \
  --out reports/generated/compare_baseline_vs_spec_first.md
```

The useful signal is paired: same task, same case, same scorer, different agent config.
