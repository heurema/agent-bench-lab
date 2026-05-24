# DATA-01 Decision-Grade Pattern

DATA-01 measures exact data work and artifact-contract compliance.

It uses synthetic CSV and SQLite fixtures, deterministic public check configs, and local scoring.
There is no browser dependency, live service, provider adapter, or LLM judge.

## What It Measures

- reading CSV fixtures;
- querying or inspecting SQLite fixtures;
- joining data across sources;
- handling null values, duplicate rows, and date boundaries;
- normalizing categories and regions;
- stable sorting and tie-breaking;
- producing exact `metrics.json` values;
- writing a concise factual `report.md`;
- producing deterministic `chart_spec.json` data.

## What It Does Not Measure

- broad spreadsheet UX skill;
- live database access;
- browser workflows;
- business judgment beyond the provided spec;
- visual chart rendering quality;
- private customer-data performance.

## Public Cases And Holdouts

Public DATA-01 cases under `fixtures/public/DATA-01/` are examples and smoke tests. They include
synthetic fixtures and public expected values in `check_config.json` so the local scorer can be
tested end to end.

Decision-grade evaluation needs private holdout cases outside the public repo, or under gitignored
local paths. Do not publish real customer data, private holdout fixtures, hidden answer keys,
private scorer config, or score reports that reveal hidden checks.

## Scorer Contract Mapping

DATA-01 uses the shared scorer-contract model instead of a one-off hidden-check shape:

| Contract | DATA-01 use |
|---|---|
| `artifact_exact` | required artifact files and no-extra-file checks |
| `schema_contract` | valid `metrics.json` and `chart_spec.json` objects with required keys |
| `numeric_metric` | exact or tolerance-based metric values |
| `claim_rubric` | required report sections, required metric references, and unsupported-claim checks |
| `security_leak` | private canaries and honey rows in future private bundles, not public smoke cases |

The public scorer is config-driven for synthetic cases. Private holdout configs should stay in the
Private Eval Layer and public-facing reports should rely on redacted diagnostics.

## Why Chart Spec Instead Of PNG

`chart_spec.json` is scored instead of `chart.png` in v0.2.

The goal is to verify the data contract deterministically:

```text
title + axes + labels + series values
```

Visual rendering can be added later as an optional artifact. It should not be the primary oracle
until the benchmark has stable image-rendering rules and a deterministic renderer.

## Mutations

`scripts/create_data01_mutation.py` creates safe public-style mutation cases under ignored local
output paths by default:

```bash
python3 scripts/create_data01_mutation.py
```

Mutations change synthetic names, numeric values, dates, row order, and harmless distractor rows.
They help detect agents that memorize one public case instead of reading the current data and spec.

## How DATA-01 Complements IF-01

IF-01 checks whether an agent follows strict instructions and artifact contracts.

DATA-01 checks whether an agent can compute exact values from structured data, avoid invented
numbers, and produce checkable reporting artifacts.

Together they create a small paired-comparison suite:

```text
IF-01   -> instruction following / contract discipline
DATA-01 -> exact data work / factual reporting
```

## Comparing Setups

Run the same DATA-01 cases for two agent configs, then compare their score directories:

```bash
make data01-smoke
make compare-smoke
```

Or compare explicit runs:

```bash
agent-bench compare \
  --baseline runs/baseline \
  --candidate runs/spec_first \
  --out reports/generated/compare_baseline_vs_spec_first.md
```

The useful signal is paired: same task family, same case, same scorer, different agent setup.

## Customer-Data-Style Tasks

DATA-01 can later support spreadsheet or customer-data-style evaluation through private bundles.

The public repo should contain only task-family definitions, synthetic examples, scorer interfaces,
and docs. Customer-specific fixtures, protected expected values, answer keys, and private scorer
config should be mounted at run time for the scorer, not shown to the agent and not committed to
the public tree.
