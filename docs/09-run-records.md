# Run Records

A run is one attempt by one agent config on one task case.

```text
agent config + task id + case id + artifacts = score.json
```

The score command reads an artifact directory, calls the task scorer, and writes a normalized
`score.json` record. The scorer remains deterministic and local.

```bash
agent-bench score \
  --task IF-01 \
  --case case_001 \
  --artifacts examples/artifacts/IF-01/case_001 \
  --agent-config configs/agents/baseline.json \
  --run-id baseline_IF-01_case_001 \
  --out runs/baseline/IF-01_case_001/score.json
```

Each score record includes:

- task and case identifiers;
- task version and scorer hash;
- agent config id and stable config hash;
- success, score, and pass threshold;
- component-level checks;
- policy violations and errors;
- hashes of submitted artifacts;
- optional cost, latency, tool-call, and model-call metadata.

Public fixtures are only smoke-test examples. Do not treat public `case_001` scores as
decision-grade evidence. Real evaluation needs private holdout cases outside the public repo.
