# API-01 Decision-Grade Pattern

API-01 is the first local tool/API workflow task-family pattern in Agent Bench Lab.

It evaluates whether an agent can read a synthetic API catalog, choose correct endpoints among distractors, build valid parameters, preserve call order, avoid forbidden tools, and produce a state-changing plan that a deterministic scorer can simulate locally.

API-01 does not use live SaaS, MCP servers, browser workflows, real internal APIs, or customer data.

## What It Measures

- tool/API catalog reading;
- endpoint selection among near-duplicate tools;
- parameter construction and ID propagation;
- read-before-write discipline;
- forbidden admin/debug/trap endpoint avoidance;
- blocked or escalated outcomes under policy;
- deterministic final-state reasoning through scorer-side simulation;
- artifact-contract compliance for `tool_calls.json`, `result.json`, and `decision_log.md`.

## What It Does Not Measure

API-01 does not measure live MCP protocol behavior, real SaaS integration, browser automation, provider-specific tool runtimes, long-running production workflows, or private customer bundle handling. Those belong in later replay, local-server, or private holdout milestones.

## Public Fixture Shape

Each public case is synthetic:

```text
fixtures/public/API-01/case_001/
  spec.md
  api_catalog.json
  api_state.json
  policy.md
  check_config.json
```

Public cases are examples and smoke tests. They expose public `check_config.json` rules so contributors can understand the scorer. Decision-grade evaluation still needs private holdouts outside the public repo.

## Artifact Contract

`tool_calls.json` contains an ordered call plan:

```json
{
  "calls": [
    {
      "step": 1,
      "tool_id": "accounts.get",
      "params": {
        "account_id": "acct_api_001"
      },
      "reason": "Need current account status before update"
    }
  ]
}
```

`result.json` records the expected outcome:

```json
{
  "status": "completed",
  "summary": "Enabled export access and created an audit note.",
  "final_state_expectation": [],
  "affected_entities": ["account:acct_api_001"],
  "policy_notes": ["Used only non-admin tools."]
}
```

`decision_log.md` explains selected tools, policy constraints, avoided tools, and unresolved or escalated items. It must not include hidden labels, answer keys, canaries, protected scorer config, or scorer-only content.

## Scorer Simulation

The public scorer does not start a server. It reads:

- `api_catalog.json`;
- `api_state.json`;
- `tool_calls.json`;
- `check_config.json`.

Then it validates the call plan and simulates only the operations needed by public cases:

- read entity;
- update entity field;
- create note, task, or escalation record;
- reject forbidden, invented, or invalid calls through policy violations and score caps.

The scorer checks the simulated final state against configured expected state paths.

## Scorer Contracts

API-01 maps to existing scorer contract types:

- `artifact_exact`: required files and no-extra-file checks;
- `schema_contract`: `tool_calls.json` and `result.json`;
- `state_diff`: local API state simulation and expected final-state paths;
- `trace_policy`: call order, read-before-write, forbidden endpoints, required tools, and max calls;
- `claim_rubric`: `decision_log.md` policy reasoning;
- `security_leak`: future private canaries, trap endpoints, and hidden tool registries.

The public scorer is deterministic and config-driven. It checks exact tool IDs, required parameters, forbidden categories, state diffs, result status, affected entities, and decision-log sections.

## Private Holdouts

Private API evaluation should live outside the public repo. A private API-01 bundle may include:

- hidden synthetic tool registries;
- private state seeds;
- protected expected state diffs;
- trap endpoints;
- canary records;
- protected scorer config;
- redacted feedback templates.

The agent-visible task packet should include only allowed prompt, catalog, state, policy, and task spec. The scorer may receive hidden expected diffs, protected trap endpoint rules, and private canaries. Public reports should include redacted diagnostics only.

## Mutations

`scripts/create_api01_mutation.py` creates public-style mutation cases under ignored output paths such as:

```text
artifacts/mutations/API-01/case_mutation_001/
```

Mutation cases can rename synthetic entities, reorder catalog entries, rename harmless display names, shift timestamps, add distractor endpoints, add distractor entities, or paraphrase policy wording. They are not private holdouts.

## Suite Placement

API-01 is intentionally not added to `configs/suites/core.json` by default.

It belongs to:

```text
configs/suites/tools-local.json
```

Core should remain a fast starter suite. Tool and API workflows can grow under `tools-local` without forcing every new task family into core.

## Comparing Setups

Use paired comparison:

```text
tool_agent_baseline / API-01 / case_001
tool_agent_policy_first / API-01 / case_001
```

Compare the same case with the same scorer and different agent setups. Public cases are smoke tests; private holdouts are required for final decisions.
