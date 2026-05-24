# Concept

Agent Bench Lab is a repeatable test bench for AI-agent setups.

A setup can be:

- a model;
- a provider;
- a system prompt;
- a tool policy;
- a memory layer;
- a browser/terminal workflow;
- a critic loop;
- a multi-agent scaffold;
- an MCP-heavy tool layer.

The benchmark asks:

> If one part of the setup changes, did agent behavior improve in a way that generalizes?

## What counts as improvement?

Improvement is not just a nicer final answer. Improvement is measured by:

- higher hidden-case success;
- fewer policy violations;
- lower cost for the same score;
- lower latency for the same score;
- fewer unnecessary tool calls;
- better robustness to small task mutations;
- better repeated-run reliability.

## Task families, not single tasks

Do not test only one fixed task instance. Test a task family with multiple seeds:

```text
APP-04 airline rebooking
  public case_001
  public case_002
  private case_101
  private case_102
  mutation case_201
```

The visible cases help you develop the agent. Hidden and mutation cases tell you whether the improvement is real.

## Domain-agnostic task families

Agent Bench Lab evaluates agent behavior across task families, not only software-development tasks.

A task family can represent any repeatable workflow where inputs, allowed actions, expected outputs, and scoring rules can be versioned.

Examples:

| Domain | Example task family | Possible oracle |
|---|---|---|
| Code | Fix a seeded repository regression | unit tests + diff policy |
| Docs / knowledge | Answer from a frozen knowledge pack | citation coverage + factual checks |
| Spreadsheet / data | Produce metrics from CSV, Sheets, or SQLite | exact values + artifact contract |
| Support inbox | Classify and draft responses to customer emails | label, draft, and state checks |
| Tickets | Triage and update a task board | ticket state diff |
| Browser | Complete a self-hosted workflow | DB state + trace replay |
| Internal APIs | Execute policy-compliant tool workflow | API state diff + policy checks |
| Customer private checks | Validate customer-specific workflows | protected private scorer bundle |

The same benchmark protocol applies across domains: paired runs, fixed seeds, private holdouts, mutation cases, trace logging, and explicit cost/latency accounting.
