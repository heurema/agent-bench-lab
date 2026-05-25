# Research Radar

Agent Bench Lab needs a research radar because benchmark methodology changes quickly. Static
research snapshots are useful, but they are not enough to keep a benchmark standard current.

The radar is a public-safe process for tracking benchmark mechanics, not a generic AI-news feed.

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
| Weekly synthesis | 45 minutes | roadmap decision or explicit no-change |
| Monthly pruning | 30 minutes | watchlist cleanup |

Daily radar should answer: did anything important change?

Weekly synthesis should answer: should Agent Bench Lab change roadmap, open issues, or run
follow-up research?

## Public And Private Boundary

Public-safe:

- watchlists;
- public source maps;
- query sets;
- templates;
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
