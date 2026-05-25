# Private Eval Layer

The Private Eval Layer is the protected boundary for evaluation content that must not live in the
public repository and must not be shown to agents.

It is a boundary, not a required product or repository. It can be implemented as:

- a gitignored local folder;
- a private repository;
- an encrypted bundle;
- customer-scoped storage;
- a scorer-only runtime mount;
- an enterprise eval service.

## What It Owns

- private holdouts;
- hidden labels;
- answer keys;
- protected scorer configs;
- canaries;
- hidden rubrics;
- customer-specific checks;
- private corpora;
- redaction rules;
- exploit smoke tests.

## Core Rule

```text
agent-visible task packet != scorer-visible scoring bundle
```

The agent receives only the task instructions, allowed fixtures, and allowed tools.
The scorer may receive protected labels, answer keys, rubrics, canaries, and hidden checks.
Consumer applications may keep references, hashes, permissions, and redacted reports, but must not
expose scorer-only content to agents.

## Recommended Bundle Shape

```text
private_eval_bundle/
  bundle.yaml
  lineage/
  public_stub/
  fixtures_private/
  labels_hidden/
  scorer/
  integrity/
  feedback/
  reports/
```

Recommended contents:

| Path | Purpose |
|---|---|
| `bundle.yaml` | Manifest with identity, versions, hashes, and policies |
| `lineage/` | Provenance notes, generator version, reviewer notes |
| `public_stub/` | Safe public-style metadata or synthetic mirror |
| `fixtures_private/` | Private fixtures and holdout seeds |
| `labels_hidden/` | Hidden labels, expected values, answer keys |
| `scorer/` | Protected scorer config and private scorer extensions |
| `integrity/` | Canaries, leak checks, exploit smoke tests, checksum tree |
| `feedback/` | Redaction rules and safe feedback templates |
| `reports/` | Private reports, kept outside public repos |

## Manifest Metadata

`bundle.yaml` should include:

```yaml
bundle_id: customer_or_suite_bundle_id
bundle_version: 2026-05-25.1
task_family: DATA-01
task_version: 0.2.0
fixture_hash: sha256:...
scorer_config_hash: sha256:...
visibility_policy: scorer_only_private_labels
redaction_policy: no_hidden_labels_or_thresholds
canary_policy: hidden_tripwire_only
created_at: 2026-05-25T00:00:00Z
reviewer: reviewer_id_or_team
provenance: synthetic_or_customer_approved_source
checksum_tree: sha256:...
```

Do not put raw private data, hidden labels, answer keys, private rubrics, or customer secrets in
public run records or public reports. Public records may include hashes and bundle identifiers.

## Visibility Matrix

| Item | Public repo | Agent | Runner | Scorer | Consumer application |
|---|---|---|---|---|---|
| Task schema | yes | optional | yes | yes | yes |
| Public fixture | yes | yes | yes | yes | yes |
| Private fixture | no | task-specific view only | path/reference | yes | reference/hash |
| Hidden label | no | no | no | yes | no raw value |
| Answer key | no | no | no | yes | no raw value |
| Scorer code | public interface | no | yes | yes | yes |
| Protected scorer config | no | no | reference/hash | yes | reference/hash |
| Run record | sanitized | no | yes | yes | redacted |
| Trace | no raw trace in public | no | yes | yes | redacted |
| Final artifact | no by default | produced by agent | yes | yes | yes/redacted |
| Score report | public summary only | no | yes | yes | redacted |
| Redacted feedback | optional | yes | yes | yes | yes |
| Canary strings | no | no | no | yes | no raw value |
| Customer data | no | only if task allows | path/reference | yes | access-controlled |
| Consumer UI config | no | no | optional | no | yes |
| Agent setup config | optional sanitized | no | yes | optional | yes |

## Canaries

Canaries are integrity tripwires, not the main defense.

Use canaries with fixed or replayed fixtures, sealed holdouts, exploit smoke tests, narrow runner
visibility, and redacted feedback. A canary hit should trigger investigation; it should not be the
only reason a benchmark is considered protected.
