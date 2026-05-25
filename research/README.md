# Research Radar

Research Radar is the public-safe benchmark intelligence layer for Agent Bench Lab.

It is not a generic AI-news feed. It tracks external work that can change benchmark design:

- scoring and oracle patterns;
- private/public split methods;
- replay and snapshot environments;
- trace policy and tool-use checks;
- benchmark hardening, exploitability, and contamination;
- cost, latency, pass^k, and repeatability methods;
- standards and eval-framework updates.

The goal is to turn external benchmark/eval signals into roadmap decisions without chasing hype.

## Cadence

| Loop | Timebox | Purpose |
|---|---:|---|
| Daily radar | 15 minutes | Collect and triage high-signal source changes |
| Weekly synthesis | 45 minutes | Decide whether the roadmap changes |
| Monthly pruning | 30 minutes | Remove noisy sources and add better ones |

Daily briefs are triage artifacts. Weekly synthesis is where roadmap decisions happen.

## Public-Safe Rule

Public `research/` files may contain:

- public watchlists;
- public source maps;
- public search queries;
- daily and weekly templates;
- curated public benchmark notes;
- public weekly summaries.

Do not commit:

- raw feeds or crawler caches;
- private eval material;
- private holdouts;
- hidden answer keys;
- protected scorer configs;
- customer data;
- personal notes;
- private roadmap doubts;
- consumer-application observations.

Private or noisy working notes belong outside the public repo.

## Action Categories

Every radar item should end in one action:

- `ignore`
- `read later`
- `add to watchlist`
- `open issue`
- `update roadmap`
- `run follow-up research`
- `prototype after review`

Most days should not change the roadmap.
