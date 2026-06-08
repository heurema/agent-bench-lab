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
Weekly synthesis may also produce bounded R&D idea candidates when a public source exposes a
transferable method pattern from another domain.

## Cadence

| Loop | Timebox | Purpose |
|---|---:|---|
| Daily radar | 15 minutes | Collect and triage high-signal source changes |
| Weekly synthesis | 45 minutes | Decide whether the roadmap changes and capture bounded idea candidates |
| Monthly pruning | 30 minutes | Remove noisy sources and add better ones |

Daily briefs are triage artifacts. Weekly synthesis is where roadmap decisions happen and where
one to three R&D idea candidates can be captured for later review. Idea candidates are not roadmap
commitments.

## Public-Safe Rule

Public `research/` files may contain:

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

## R&D Idea Candidates

Idea candidates turn a public signal into a testable benchmark direction without starting
implementation automatically.

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

Use `research/idea-candidates-template.md` for public-safe candidates. Keep private daily briefs,
raw feeds, private eval material, and personal notes outside the public repo.
