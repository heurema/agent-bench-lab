# Agent Bench Lab R&D Idea Candidates

Date:

Source window:

Use this template to convert public benchmark, eval, research, and adjacent-domain signals into
bounded ideas. Do not paste private daily briefs, raw feeds, private eval material, customer data,
or personal notes into this file.

## Candidate Table

| Signal | Method Pattern | Domain Transfer | Benchmark Idea | Evidence | Action | Confidence | Timebox |
|---|---|---|---|---|---|---|---|
|  |  | software-engineering / browser-workflow / security / data-finance / science-bio / ops-support / research |  |  | ignore / read later / open issue / run follow-up research / prototype after review | low / medium / high |  |

## Transfer Taxonomy

| Domain | Transfer target |
|---|---|
| software-engineering | Coding, repository repair, and terminal debugging tasks. |
| browser-workflow | Replay, snapshots, verified environments, and workflow-state checks. |
| security | Prompt injection, exploit smoke tests, leakage checks, and adversarial scoring. |
| data-finance | Time splits, leakage controls, and backtesting-style validation. |
| science-bio | Blind evaluation, private holdouts, and reproducibility protocols. |
| ops-support | Policy-grounded triage, stateful workflows, and customer-style cases. |
| research | Citation scoring, fixed corpora, and unsupported-claim checks. |

## Example

| Signal | Method Pattern | Domain Transfer | Benchmark Idea | Evidence | Action | Confidence | Timebox |
|---|---|---|---|---|---|---|---|
| A public benchmark issue describes a verified split repair after leakage was found. | Treat split repair as benchmark lifecycle evidence, not only as a leaderboard update. | data-finance | Add a follow-up research note on time-split and leakage controls for private holdout generation. | Public issue or release URL. | run follow-up research | medium | 30 minutes |

## Decision Rule

Most candidates should stay as `read later` or `run follow-up research`. Use `prototype after
review` only when the source adds a concrete scorer, oracle, suite, replay, or hardening pattern that
can be tested without private-data leakage or roadmap churn.
