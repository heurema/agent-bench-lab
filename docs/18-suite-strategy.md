# Suite Strategy

Suites are comparison bundles. They should be small enough to run repeatedly and clear enough to
interpret.

## Core Is Not All Tasks

`core` is the fast general starter suite. It should not automatically absorb every new
decision-grade task family.

Core bloat makes routine regression checks slower and less diagnostic. New task families should
propose a suite explicitly.

## Current Suites

| Suite | Purpose | Current scope |
|---|---|---|
| `core-v0` | Fast general local regression and smoke comparison | starter task mix plus IF, DATA, DOC |
| `ops-local-v0` | Operational and customer-style workflows | SUP-01 |
| `tools-local-v0` | Local tool/API workflow evaluation | API-01 |

## Future Suites

Future suites may include:

- `dev-local` for repository and terminal work;
- `security-local` for prompt injection, leakage, and policy tasks;
- `research-local` for fixed-corpus source-grounded research;
- `browser-replay` for browser tasks over frozen snapshots;
- `weekly-deep` for slower, broader regression runs.

## Rule

Every new task family should answer:

```text
Which suite owns this task, and why?
```

If the answer is "core", the task should be fast, broadly useful, and worth running in most local
regression loops.
