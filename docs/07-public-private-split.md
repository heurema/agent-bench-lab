# Public / Private Split

This repository is intended to be public from the beginning.

## Public files

Public files should include:

- documentation;
- schemas;
- task templates;
- synthetic public sample fixtures;
- scorer interfaces;
- fixture generators;
- public examples.

## Private files

Private files should not be committed:

- hidden fixtures;
- holdout seeds;
- private answer keys;
- traces from real tasks;
- real user or customer data;
- production prompts;
- provider keys.

## Recommended local layout

```text
private/
  fixtures/
    APP-04/
      case_101/
      case_102/
  answer_keys/
  reports/
```

`private/` is gitignored by default.

## Three-boundary model

Agent Bench Lab is the public or semipublic benchmark standard layer.

Private Eval Layer is the protected boundary for hidden labels, private holdouts, canaries, answer keys, customer-specific checks, private rubrics, redaction rules, and private scorer configs.

Consumer Application is any product, CLI, workflow, dashboard, or platform that runs benchmarks and presents results.

```text
Agent Bench Lab
  public benchmark standards, task families, schemas, sample fixtures, scorer interfaces

Private Eval Layer
  protected holdouts, hidden labels, answer keys, canaries, private scorer configs, customer checks

Consumer Application
  UI, onboarding, agent setup management, task delivery, artifact upload, score reports
```

Agent Bench Lab should not store private eval secrets.
Consumer applications should not expose scorer-only content to agents.
The Private Eval Layer is a boundary, not a required implementation; it can be a gitignored local folder, private repo, encrypted bundle, customer-scoped storage, or enterprise eval service.

See [Private Eval Layer](private-eval-layer.md) for the recommended private bundle shape and full visibility matrix.

## Customer-specific private holdouts

Customer-specific benchmark data must be treated as protected evaluation content.

Do not commit customer fixtures, real data, private rubrics, answer keys, hidden scorer configs, prior successful traces, or private score reports to the public repository.

Recommended model:

```text
public repo:
  task family definition
  public synthetic examples
  scorer interface
  public docs

private customer bundle:
  customer-specific fixtures
  private holdout seeds
  private answer keys
  protected scorer config
  sanitized or synthetic mirrors if needed
  canary strings
```

The agent should receive only the task inputs it is allowed to use. The scorer may receive protected rubrics, answer keys, and hidden checks. The consumer application may store references and hashes, but must not expose protected content to the agent.

A run record may include:

```text
customer_bundle_id
bundle_version
fixture_hash
scorer_config_hash
privacy_level
```

It should not include raw private data, answer keys, hidden rubric text, or customer-specific scorer config content.

## Agent/scorer visibility boundary

Keep a strict separation:

| Component | May see |
|---|---|
| Agent | user prompt, allowed public/private input fixtures, allowed tools |
| Runner | task metadata, fixture paths, budget, tool policy |
| Scorer | final artifacts, trace, private answer keys, hidden checks |
| Report | scores, deltas, summarized failures, redacted diagnostics |
| Public repo | public synthetic examples only |

Never give the agent hidden rubrics, answer keys, prior successful traces, private score reports, or customer-specific scorer configs.
