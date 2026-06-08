# Local Agent Runner MVP

The local runner lets Agent Bench Lab run an external command against an existing public task case.

It is a command adapter, not a provider adapter.

It does not implement OpenAI, Anthropic, MCP, browser automation, private bundle mounting, scheduled evals, or a sandbox. Any local agent setup can be wrapped as a command as long as it writes artifacts to the artifacts directory provided by the runner.

## Command

```bash
agent-bench run \
  --task IF-01 \
  --case case_001 \
  --agent-cmd "python3 scripts/mock_agent_write_artifacts.py" \
  --out runs/manual/mock/IF-01_case_001
```

The command creates:

```text
runs/manual/mock/IF-01_case_001/
  run.json
  score.json
  trace.jsonl
  artifacts/
  task_packet/
```

If `--out` is omitted, the runner writes under `runs/manual/...`. Local run outputs are ignored by git.

## Environment

The external command receives:

```text
AGENT_BENCH_TASK_ID
AGENT_BENCH_CASE_ID
AGENT_BENCH_RUN_ID
AGENT_BENCH_TASK_PACKET
AGENT_BENCH_ARTIFACTS_DIR
AGENT_BENCH_AGENT_CONFIG
AGENT_BENCH_DIAGNOSTICS_FILE
```

The agent command should write final artifacts to:

```text
$AGENT_BENCH_ARTIFACTS_DIR
```

## Run Validity Diagnostics

Agent wrappers may write public-safe diagnostics to `$AGENT_BENCH_DIAGNOSTICS_FILE` when a run is
not valid evidence of agent quality. This is for provider, environment, or harness failures, not
for normal task failure.

```json
{
  "valid": false,
  "category": "provider_error",
  "diagnostic_code": "provider_routing_failure",
  "reason": "model endpoint returned 404 repeatedly",
  "environment_ref": "optional public-safe snapshot/version id"
}
```

Supported categories are:

- `provider_error`
- `environment_error`
- `harness_error`

Supported diagnostic codes are:

- `provider_routing_failure`
- `cost_accounting_drift`
- `final_submit_not_executed`
- `verifier_infrastructure_failure`

If the diagnostics file is missing, the runner preserves normal behavior. If it contains
`"valid": false`, the runner records `status: "environment_error"`, writes `run_validity` to
`score.json`, skips the scorer, and emits a `run_invalidated` trace event. The wrapper is
responsible for keeping `reason` and `environment_ref` public-safe.

`cost_accounting_drift` may be reported with `"valid": true` when task-quality evidence is valid but
cost metadata should not be trusted for cost comparisons. See
[Run Validity Diagnostics](22-run-validity-diagnostics.md).

## Visibility Boundary

The runner keeps the agent-visible task packet separate from the scorer-visible fixture.

The agent may see:

- task prompt;
- public task metadata;
- public case spec;
- safe public fixture inputs such as data, corpora, inbox files, API catalogs, policies, and state fixtures.

The agent must not see:

- `check_config.json`;
- answer keys;
- hidden labels;
- private scorer configs;
- canaries;
- expected values;
- private holdouts;
- private eval bundle contents.

The scorer still receives the original fixture directory and the produced artifact directory. This keeps public smoke runs aligned with the same visibility model needed for private holdouts.

## Run and Score Records

`run.json` records:

- run id;
- task and case id;
- task version;
- agent config id/hash;
- command hash;
- timing;
- status;
- score summary;
- paths to task packet, artifacts, score, and trace.
- optional validity category for invalid evidence.

`trace.jsonl` records minimal runner lifecycle events:

- `run_started`;
- `task_packet_created`;
- `agent_command_started`;
- `agent_command_completed`;
- `agent_command_timeout`;
- `run_invalidated`;
- `scorer_started`;
- `scorer_completed`;
- `run_completed`.

Command output snippets are bounded and redacted. The runner does not store raw secrets or private scorer-only content.

## Compare Setups

Run two agent setups into separate directories, then compare the resulting `score.json` files:

```bash
agent-bench run \
  --task DATA-01 \
  --case case_001 \
  --agent-cmd "python3 my_agent_a.py" \
  --out runs/setup_a/DATA-01_case_001

agent-bench run \
  --task DATA-01 \
  --case case_001 \
  --agent-cmd "python3 my_agent_b.py" \
  --out runs/setup_b/DATA-01_case_001

agent-bench compare \
  --baseline runs/setup_a \
  --candidate runs/setup_b
```

## Smoke Agent

`scripts/mock_agent_write_artifacts.py` is a test helper. It writes valid public sample artifacts for smoke cases into `$AGENT_BENCH_ARTIFACTS_DIR`.

It is not a benchmarked agent and should not be used as evidence of agent capability.

## Non-Goals

The MVP intentionally does not provide:

- provider-specific adapters;
- live SaaS or MCP integrations;
- browser or office workflow runners;
- private holdout storage;
- private bundle runtime;
- automatic GitHub issues or commits;
- scheduled evals.
