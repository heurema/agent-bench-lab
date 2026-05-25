# DOC-01 Decision-Grade Pattern

DOC-01 measures fixed-corpus document QA, grounded answers, citation validation, and unsupported-claim detection.

It uses synthetic local document corpora, deterministic public check configs, and local scoring.
There is no live web dependency, browser workflow, provider adapter, or LLM judge.

## What It Measures

- reading a fixed local document corpus;
- distinguishing current sources from stale or distractor sources;
- answering only from provided documents;
- marking unsupported claims as unsupported;
- citing source documents and quoted evidence;
- producing contract-compliant `answer.md`, `citations.json`, and `claims.json`;
- avoiding unsupported or stale claims in the final answer.

## What It Does Not Measure

- live web research;
- browser navigation;
- broad long-form writing quality;
- private customer corpus performance;
- subjective answer style beyond the provided contract.

## Fixed Corpus Instead Of Live Web

DOC-01 uses a fixed corpus because live web tasks are hard to replay and easy to contaminate.

The primary oracle is deterministic:

```text
provided corpus + artifact contract + citation checks + claim checks
```

Live web, browser snapshots, and replay systems can be added later as separate task-family patterns.
They should not be required for DOC-01 public smoke cases.

## Output Artifacts

DOC-01 expects:

```text
answer.md
citations.json
claims.json
```

`answer.md` is the concise user-facing answer.

`citations.json` lists cited corpus documents and exact quoted snippets.

`claims.json` lists atomic claims, whether each claim is supported, and which citation IDs support it.

## Scorer Contract Mapping

DOC-01 uses the shared scorer-contract model:

| Contract | DOC-01 use |
|---|---|
| `artifact_exact` | required output files and no-extra-file checks |
| `schema_contract` | valid `citations.json` and `claims.json` structures |
| `claim_rubric` | supported/unsupported claim status, required evidence, and unsupported-claim checks |
| `security_leak` | private canaries and hidden corpus leaks in future private bundles |
| `cost_latency` | report-level fields, not DOC-01-specific scoring |

The public scorer is config-driven for synthetic cases. Private expected claims and protected rubrics
belong in the Private Eval Layer.

## Public Cases And Holdouts

Public DOC-01 cases under `fixtures/public/DOC-01/` are examples and smoke tests. They include
synthetic corpora and public expected claim/citation checks in `check_config.json`.

Decision-grade evaluation needs private holdout corpora outside the public repo, or under gitignored
local paths. Do not publish real customer documents, private holdout corpora, hidden answer keys,
private scorer configs, or score reports that reveal hidden claims.

## Mutations

`scripts/create_doc01_mutation.py` creates safe public-style mutation cases under ignored local
output paths by default:

```bash
python3 scripts/create_doc01_mutation.py
```

Mutations can rename synthetic entities, reorder documents, change dates while preserving
current/stale logic, add distractor documents, and shuffle claim order. They help detect agents
that memorize public cases instead of reading the current corpus and spec.

## Private Bundle Guidance

Future private DOC-01 bundles can add:

- hidden corpora;
- protected expected claims;
- private citation rubrics;
- canary strings;
- stale-source traps;
- redacted feedback templates.

The agent should see only the task packet and allowed corpus view. The scorer may see protected
private checks. Public reports should use redacted feedback and should not reveal hidden claims,
answer keys, canaries, or private source IDs.

## Comparing Setups

Run the same DOC-01 cases for two agent configs, then compare score directories:

```bash
make doc01-smoke
make compare-smoke
```

The useful signal is paired: same task family, same case, same scorer, different agent setup.

## How DOC-01 Complements IF-01 And DATA-01

```text
IF-01   -> instruction following / contract discipline
DATA-01 -> exact data work / factual reporting
DOC-01  -> grounded document QA / citation discipline
```

Together these form a small local-first benchmark foundation for instruction, data, and knowledge-work agents.
