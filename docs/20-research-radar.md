# Research Radar

Agent Bench Lab needs a research radar because benchmark methodology changes quickly. Static
research snapshots are useful, but they are not enough to keep a benchmark standard current.

The radar is a public-safe process for tracking benchmark mechanics, not a generic AI-news feed.
It can also capture bounded R&D idea candidates when a public source reveals a transferable method
pattern from another domain.

## What To Monitor

Monitor sources that can change Agent Bench Lab design:

- verified splits and benchmark repair;
- deterministic and audited scoring;
- state-diff and trace-policy oracles;
- replay and snapshot environments;
- private holdout and redacted-feedback methods;
- benchmark contamination and exploitability;
- prompt-injection and tool-output trust-boundary evals;
- cost, latency, pass^k, and repeatability reporting;
- eval-framework and standards updates.

## Cadence

| Loop | Timebox | Output |
|---|---:|---|
| Daily radar | 15 minutes | short triage brief |
| Weekly synthesis | 45 minutes | roadmap decision, explicit no-change, or bounded idea candidates |
| Monthly pruning | 30 minutes | watchlist cleanup |

Daily radar should answer: did anything important change?

Weekly synthesis should answer: should Agent Bench Lab change roadmap, open issues, or run
follow-up research? It may also capture one to three R&D idea candidates for later review when the
evidence is transferable and public-safe.

## Public And Private Boundary

Public-safe:

- watchlists;
- public source maps;
- query sets;
- templates;
- idea candidate templates;
- curated public summaries;
- decision logs.

Do not commit:

- raw feeds;
- dedupe caches;
- private eval material;
- hidden holdouts;
- answer keys;
- customer data;
- private rubrics;
- protected scorer configs;
- personal notes;
- consumer-application observations.

## Action Categories

Every item should end in one of:

- `ignore`
- `read later`
- `add to watchlist`
- `open issue`
- `update roadmap`
- `run follow-up research`
- `prototype after review`

Most items should be ignored or queued. The radar prevents stale decisions; it should not create
constant churn.

## R&D Idea Candidates

An idea candidate is a public-safe handoff from a new signal to a possible benchmark experiment. It
is not a roadmap decision, issue, or implementation request.

Each candidate should include:

- `Signal`: a new paper, repo, issue, release, project, or method;
- `Method Pattern`: the useful benchmark or eval mechanic;
- `Domain Transfer`: one of `software-engineering`, `browser-workflow`, `security`,
  `data-finance`, `science-bio`, `ops-support`, or `research`;
- `Benchmark Idea`: a possible task family, scorer, oracle, suite, or hardening gate;
- `Evidence`: public-safe source links or notes;
- `Action`: `ignore`, `read later`, `open issue`, `run follow-up research`, or
  `prototype after review`;
- `Confidence`: `low`, `medium`, or `high`;
- `Timebox`: the maximum follow-up or prototype budget.

Use idea candidates to transfer methods across domains, for example finance-style leakage controls,
biology-style blind evaluation, or security-style exploit smoke tests. Use `prototype after review`
only after a human review, not as an automatic implementation trigger.

## When To Open An Issue

Open an issue when a source introduces:

- a benchmark-hardening method Agent Bench Lab should adopt;
- a new scorer/oracle pattern;
- a verified split or benchmark repair lesson;
- a private/public split pattern;
- a replay/snapshot method;
- a concrete exploit or contamination risk;
- a report schema or lifecycle convention worth standardizing.

Do not open issues for leaderboard movement or generic model news unless the evaluation method
changes.

## Files

Research Radar files live under:

```text
research/
```

Start with:

- `research/watchlist.md`
- `research/source-map.csv`
- `research/daily-brief-template.md`
- `research/weekly-synthesis-template.md`
- `research/idea-candidates-template.md`
