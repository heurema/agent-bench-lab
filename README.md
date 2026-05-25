# Agent Bench Lab

A public, local-first starter kit for building reproducible benchmark suites for AI agents.

The goal is not to create another leaderboard. The goal is to help agent builders answer one practical question:

> When I change my agent setup — model, prompt, memory, tools, MCP, planner, critic loop, or multi-agent scaffold — did it actually get better?

Agent Bench Lab is designed around repeatable task families, versioned fixtures, deterministic or semi-deterministic scoring, trace logging, and anti-overfitting controls.

## Scope: all agent task families

Agent Bench Lab is not limited to coding-agent benchmarks.

It is a canonical benchmark framework for any repeatable agent task family where the result can be checked with deterministic, semi-deterministic, state-based, artifact-based, trace-based, or rubric-assisted scoring.

Supported task families may include:

- code and repository repair;
- docs, knowledge-base, and source-grounded research tasks;
- spreadsheets, data analysis, and reporting tasks;
- support inbox and customer-service workflows;
- ticket triage and task-board updates;
- browser workflows over frozen or self-hosted snapshots;
- internal API and tool-use workflows;
- memory and personalization tasks;
- security, prompt-injection, and policy-compliance tasks;
- customer-specific private holdout checks.

The common unit is not "coding task" or "office task". The common unit is:

```text
task family + fixtures + allowed tools + expected artifact/state + scorer + run comparison
```

The public v0/v0.3 implementation includes a small starter suite and three hardened task-family patterns. The framework is intentionally broader than the implemented starter cases.

## Relationship to consumer applications

Agent Bench Lab is the benchmark standard layer.

Consumer applications may use Agent Bench Lab to run benchmark suites inside a product, workflow, CLI, dashboard, or customer-facing experience. Consumer applications should not define a separate benchmark system when they can consume Agent Bench Lab task families, scorer interfaces, run records, and comparison protocols.

Recommended boundary:

- Agent Bench Lab owns task-family definitions, schemas, scorer conventions, run records, comparison protocol, and public/private benchmark rules.
- Private Eval Layer owns protected holdouts, answer keys, hidden labels, customer-specific checks, canaries, and private scorer configs.
- Consumer applications own product UX, onboarding, agent setup management, access control, task delivery, artifact upload, result presentation, and customer workflows.

Agent Bench Lab should not need to know which consumer application is using it.

## Private eval and scorer contracts

Agent Bench Lab should define how benchmarks work without storing protected evaluation content.

The Private Eval Layer holds hidden labels, private holdouts, answer keys, protected scorer configs, canaries, customer-specific checks, and redaction rules outside the public repo. Scorers should use reusable contracts such as `artifact_exact`, `schema_contract`, `numeric_metric`, `state_diff`, `claim_rubric`, `trace_policy`, and `security_leak` instead of inventing a new hidden-check format per task family.

See [Private Eval Layer](docs/private-eval-layer.md), [Scorer type contracts](docs/scorer-types.md), and [Reporting and feedback](docs/reporting-and-feedback.md).

## Current status

This repository is a **v0 public starter**. It contains:

- public task-card templates;
- a small core-suite config;
- JSON schemas for tasks, runs, traces, and scores;
- minimal Python CLI scaffolding;
- sample public fixtures;
- sample scorers plus hardened IF-01, DATA-01, and DOC-01 artifact-based scorers;
- documentation for benchmark design, metrics, and anti-overfitting.

It intentionally does **not** contain private holdout tasks, production secrets, personal data, or benchmark answers for real evaluation runs.

## Why this exists

Most agent demos prove that an agent can succeed once. Product work needs stronger evidence:

- Can it succeed repeatedly?
- Does it still work after task mutations?
- Does the improvement generalize to hidden variants?
- Did latency or cost increase?
- Did it use tools safely?
- Did memory help or pollute the result?
- Did a critic loop improve quality or just add expensive theatre?

## Core idea

Use the same task families across different agent setups:

```text
Setup A: model + system prompt + tools, no memory
Setup B: same setup, but with memory
Setup C: same setup, but with reviewer loop
```

Then compare them on the same seeds and hidden variants.

```text
same task family + same scoring + controlled setup change = useful comparison
```

## Public/private split

This repo is public. Treat public files as examples and templates.

For serious evaluation, keep these outside the public repo:

- private hidden fixtures;
- private holdout seeds;
- real benchmark answers;
- traces from commercial or personal tasks;
- API keys and provider metadata;
- user data;
- production prompts that should not be public.

The `.gitignore` includes `private/`, `runs/`, `artifacts/`, `traces/`, and common secret files by default.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
agent-bench list-tasks
agent-bench validate
```

Create public sample artifacts and run scoring smoke tests:

```bash
python3 scripts/create_sample_artifacts.py
agent-bench score --task IF-01 --case case_001 --artifacts examples/artifacts/IF-01/case_001
agent-bench score --task DATA-01 --case case_001 --artifacts examples/artifacts/DATA-01/case_001
python3 scripts/public_leak_check.py .
```

Without installing the package, use the source-tree Make targets:

```bash
make validate
make test
make smoke
make leak-check
```

The examples directory intentionally starts mostly empty. Generated artifacts under `examples/artifacts/` are ignored by git except for the README placeholder.

## Compare two agent setups

Create two local smoke-run directories and compare them:

```bash
make compare-smoke
```

Or run the commands directly:

```bash
python3 scripts/create_sample_runs.py
agent-bench compare \
  --baseline runs/baseline \
  --candidate runs/spec_first \
  --out reports/generated/compare_baseline_vs_spec_first.md \
  --csv reports/generated/compare_baseline_vs_spec_first.csv
```

The comparison is paired: same task, same case, same scorer, different agent config. Public runs are smoke tests only; decision-grade evaluation requires private holdout cases outside the public repo.

## First decision-grade task family: IF-01

IF-01 is the first hardened task-family pattern. It uses public synthetic cases, deterministic `check_config.json` files, critical violation caps, mutation support, and tests for strict artifact-contract compliance. See [IF-01 decision-grade pattern](docs/11-if01-decision-grade.md).

```bash
make if01-smoke
```

## Second decision-grade task family: DATA-01

DATA-01 is the second hardened task-family pattern. It uses synthetic CSV/SQLite fixtures, deterministic `metrics.json`, factual `report.md`, checked `chart_spec.json`, mutation support, and tests for exact data work without relying on a visual PNG oracle. See [DATA-01 decision-grade pattern](docs/12-data01-decision-grade.md).

```bash
make data01-smoke
```

## Third decision-grade task family: DOC-01

DOC-01 is the third hardened task-family pattern. It uses synthetic fixed-corpus documents, deterministic `answer.md`, checked `citations.json`, checked `claims.json`, mutation support, and tests for grounded answers without relying on live web or an LLM judge. See [DOC-01 decision-grade pattern](docs/13-doc01-decision-grade.md).

```bash
make doc01-smoke
```

## Initial core suite

The recommended v0 core suite has seven task families:

| ID | Task | Capability |
|---|---|---|
| CODE-01 | Local regression patch | coding + test discipline |
| TERM-02 | Log-driven config repair | terminal/debugging |
| APP-04 | Airline rebooking under policy | stateful tools + policy |
| DATA-01 | CSV + SQL memo | exact data work + concise reporting |
| DOC-01 | Fixed-corpus grounded answer | citations + unsupported-claim checks |
| IF-01 | Long spec contract artifact | strict instruction following |
| SEC-01 | Hidden prompt injection in HTML/email | security + tool-output trust boundary |

The initial core suite is a starter set for proving the runner/scorer/compare loop. It is not the full scope of Agent Bench Lab and should not be interpreted as coding-first. Future task families can cover support, knowledge work, spreadsheets, browser workflows, ticketing, internal APIs, and customer-specific private checks using the same task/scorer/run model.

## Repository layout

```text
agent-bench-lab/
  configs/              suite and agent config examples
  docs/                 public documentation
  fixtures/public/      public example fixtures only
  private/              gitignored private holdouts, if created locally
  schemas/              JSON schemas
  src/agent_bench_lab/  CLI and local harness skeleton
  tasks/                task cards, prompts, and scorer modules
  examples/artifacts/   local generated artifacts for smoke tests
  scripts/              helper scripts
```

## Design rules

1. Prefer local fixtures over live services.
2. Prefer exact/state-based scoring over subjective judging.
3. Keep hidden holdouts separate from public examples.
4. Log traces, costs, latency, and tool calls.
5. Compare paired runs on the same seeds.
6. Treat safety and policy violations as hard gates where appropriate.
7. Do not tune prompts on the same cases used for final comparison.

## Contributor docs

- [Documentation index](docs/README.md)
- [Canonical scope and consumer boundary](docs/canonical-scope-and-consumer-boundary.md)
- [Private Eval Layer](docs/private-eval-layer.md)
- [Scorer type contracts](docs/scorer-types.md)
- [Reporting and feedback](docs/reporting-and-feedback.md)
- [Task authoring](docs/05-task-authoring.md)
- [Public/private split](docs/07-public-private-split.md)
- [Run records](docs/09-run-records.md)
- [Comparing setups](docs/10-comparing-setups.md)
- [IF-01 decision-grade pattern](docs/11-if01-decision-grade.md)
- [DATA-01 decision-grade pattern](docs/12-data01-decision-grade.md)
- [DOC-01 decision-grade pattern](docs/13-doc01-decision-grade.md)
- [Public release checklist](docs/public-release-checklist.md)
- [v0 roadmap](docs/roadmap-v0.md)

## License

MIT. See [LICENSE](LICENSE).
