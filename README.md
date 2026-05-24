# Agent Bench Lab

A public, local-first starter kit for building reproducible benchmark suites for AI agents.

The goal is not to create another leaderboard. The goal is to help agent builders answer one practical question:

> When I change my agent setup — model, prompt, memory, tools, MCP, planner, critic loop, or multi-agent scaffold — did it actually get better?

Agent Bench Lab is designed around repeatable task families, versioned fixtures, deterministic or semi-deterministic scoring, trace logging, and anti-overfitting controls.

## Current status

This repository is a **v0 public starter**. It contains:

- public task-card templates;
- a small core-suite config;
- JSON schemas for tasks, runs, traces, and scores;
- minimal Python CLI scaffolding;
- sample public fixtures;
- sample scorers for several simple artifact-based tasks;
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

## Initial core suite

The recommended v0 core suite has six task families:

| ID | Task | Capability |
|---|---|---|
| CODE-01 | Local regression patch | coding + test discipline |
| TERM-02 | Log-driven config repair | terminal/debugging |
| APP-04 | Airline rebooking under policy | stateful tools + policy |
| DATA-01 | CSV + SQL memo | exact data work + concise reporting |
| IF-01 | Long spec contract artifact | strict instruction following |
| SEC-01 | Hidden prompt injection in HTML/email | security + tool-output trust boundary |

Start with these. Add browser, memory, MCP, research, office, and multi-agent tasks only after the core runner/scorer loop is stable.

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
- [Task authoring](docs/05-task-authoring.md)
- [Public/private split](docs/07-public-private-split.md)
- [Public release checklist](docs/public-release-checklist.md)
- [v0 roadmap](docs/roadmap-v0.md)

## License

MIT. See [LICENSE](LICENSE).
