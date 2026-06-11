# Research Radar

Status: deprecated as an active intake surface.

`research/` is now an archived benchmark-mechanics profile for `heurema/lab/radar`, not a separate
Agent Bench Lab research loop. New watchlists, queries, cadence decisions, reports, idea candidates,
and verdicts belong in `heurema/lab` under `radar/`.

This profile tracks external work that can change benchmark design:

- scoring and oracle patterns;
- private/public split methods;
- replay and snapshot environments;
- trace policy and tool-use checks;
- benchmark hardening, exploitability, and contamination;
- cost, latency, pass^k, and repeatability methods;
- standards and eval-framework updates.

The goal is to give the shared lab radar a public-safe Agent Bench Lab profile without chasing hype.

## Former Cadence

| Loop | Timebox | Purpose |
|---|---:|---|
| Daily radar | 15 minutes | Collect and triage high-signal source changes |
| Weekly synthesis | 45 minutes | Decide whether the roadmap changes and capture bounded idea candidates |
| Monthly pruning | 30 minutes | Remove noisy sources and add better ones |

Do not run these loops from this repository. Daily briefs, weekly syntheses, and roadmap verdicts
belong in `heurema/lab/radar`.

## Public-Safe Rule

Archived `research/` files may contain:

- public watchlists;
- public source maps;
- public search queries;
- daily and weekly templates;
- idea candidate templates;
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

## Former Action Categories

When this profile is consumed by `heurema/lab/radar`, every radar item should end in one action:

- `ignore`
- `read later`
- `add to watchlist`
- `open issue`
- `update roadmap`
- `run follow-up research`
- `prototype after review`

Most days should not change the roadmap.

## R&D Idea Candidates

Idea candidates turn a public signal into a testable benchmark direction without starting
implementation automatically. New candidates belong in `heurema/lab/radar`, not in this directory.

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

Keep private daily briefs, raw feeds, private eval material, and personal notes outside the public
repo.
